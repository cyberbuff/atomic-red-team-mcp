"""Generate atomic test tool using LLM sampling."""

import yaml
from fastmcp import Context
from pydantic import ValidationError

from atomic_red_team_mcp.models import Atomic
from atomic_red_team_mcp.models.outputs import GenerateAtomicOutput

_MAX_RETRIES = 3


def _build_initial_prompt(
    technique_id: str, platform: str, description: str, schema_summary: str
) -> str:
    focus = f" The test should: {description}." if description else ""
    return (
        f"Generate an Atomic Red Team YAML test for MITRE ATT&CK technique {technique_id} "
        f"targeting {platform}.{focus}\n\n"
        f"Schema: {schema_summary}\n\n"
        "Rules:\n"
        "- Use input_arguments for any hardcoded paths, names, or values\n"
        "- Include cleanup_command to restore system state\n"
        "- Do NOT include auto_generated_guid\n"
        "- Do NOT use echo/print/Write-Host in commands\n"
        "- Set elevation_required: true only if sudo/admin is needed\n\n"
        "Reply with ONLY the YAML — no markdown fences, no explanation."
    )


def _build_fix_prompt(previous_yaml: str, issues: list[str]) -> str:
    issues_text = "\n".join(f"- {i}" for i in issues)
    return (
        "The following Atomic Red Team YAML has issues that must be fixed:\n\n"
        f"{previous_yaml}\n\n"
        f"Issues to fix:\n{issues_text}\n\n"
        "Reply with ONLY the corrected YAML — no markdown fences, no explanation."
    )


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        lines = text.splitlines()
        return "\n".join(line for line in lines if not line.startswith("```")).strip()
    return text


def _collect_issues(yaml_text: str) -> tuple[Atomic | None, list[str]]:
    """Parse and validate yaml_text. Returns (atomic, issues) where issues is empty on success."""
    try:
        atomic_data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]

    if not atomic_data:
        return None, ["YAML is empty — the response contained no content"]

    issues = []
    if "auto_generated_guid" in atomic_data:
        issues.append(
            "Remove 'auto_generated_guid' — the system generates this automatically"
        )
    if atomic_data.get("executor", {}).get("command"):
        cmd = atomic_data["executor"]["command"].lower()
        if "echo" in cmd or "print" in cmd or "write-host" in cmd:
            issues.append("Avoid echo/print/Write-Host statements in test commands")

    try:
        atomic = Atomic(**atomic_data)
    except (ValidationError, Exception) as e:
        return None, issues + [f"Schema validation error: {e}"]

    return atomic, issues


async def generate_atomic(
    ctx: Context,
    technique_id: str,
    platform: str = "linux",
    description: str = "",
) -> GenerateAtomicOutput:
    """Generate an atomic test for a MITRE ATT&CK technique using AI assistance.

    Uses the MCP client's LLM to draft an atomic test YAML for the given technique and
    platform, then validates it automatically. If the generated test has errors or
    warnings, re-samples up to 3 times to fix them before returning.

    Args:
        technique_id: MITRE ATT&CK technique ID (e.g., "T1059.001").
                      Used to focus the generated test on the correct technique.

        platform: Target platform for the test. Valid values: windows, linux, macos.
                  Defaults to "linux".

        description: Optional free-text description of what the test should do or
                     demonstrate. Leave blank to let the AI determine the best approach
                     for the technique.

    Returns:
        GenerateAtomicOutput: Result containing:
            - valid (bool): Whether the final test passes schema validation
            - message (str): Success or error message
            - atomic_name (str): Name of the generated test (if valid)
            - supported_platforms (list): Platforms declared in the test (if valid)
            - yaml (str): Generated YAML content (if valid)
            - warnings (list): Best-practice warnings to address (if any)
            - error (str): Validation error details (if invalid)

    Notes:
        - Requires the MCP client to support server-side sampling
        - If the client doesn't support sampling, returns an error
        - The generated YAML is validated but NOT saved automatically
        - Use `server_info` to find where to save validated tests
        - Always review generated tests before use in production environments
    """
    schema = Atomic.model_json_schema()
    schema_summary = (
        f"Required fields: {schema.get('required', [])}. "
        f"Executor types: CommandExecutor (name, command) or ManualExecutor (name, steps). "
        f"Valid platforms: windows, linux, macos, office-365, azure-ad, containers."
    )

    prompt = _build_initial_prompt(technique_id, platform, description, schema_summary)
    yaml_text: str = ""

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            result = await ctx.sample(prompt)
            yaml_text = _strip_fences(result.text.strip())
        except Exception as e:
            return GenerateAtomicOutput(
                valid=False,
                message="Sampling failed",
                error=f"Could not sample from LLM: {e}. Ensure the MCP client supports server-side sampling.",
            )

        atomic, issues = _collect_issues(yaml_text)

        if not issues and atomic is not None:
            ctx.info(
                f"Generated atomic test '{atomic.name}' for {technique_id}/{platform}"
            )
            return GenerateAtomicOutput(
                valid=True,
                message=f"Generated atomic test '{atomic.name}' is valid and ready to use.",
                atomic_name=atomic.name,
                supported_platforms=atomic.supported_platforms,
                yaml=yaml_text,
            )

        if attempt < _MAX_RETRIES:
            ctx.info(
                f"Attempt {attempt}/{_MAX_RETRIES} had issues, resampling to fix: {issues}"
            )
            prompt = _build_fix_prompt(yaml_text, issues)

    # Final attempt still had issues
    atomic, issues = _collect_issues(yaml_text)
    if atomic is not None:
        # Valid but has warnings — return with warnings
        msg = "Generated atomic test is valid with warnings:\n" + "\n".join(issues)
        ctx.info(
            f"Generated atomic test '{atomic.name}' for {technique_id}/{platform} (with warnings)"
        )
        return GenerateAtomicOutput(
            valid=True,
            message=msg,
            atomic_name=atomic.name,
            supported_platforms=atomic.supported_platforms,
            yaml=yaml_text,
            warnings=issues,
        )

    return GenerateAtomicOutput(
        valid=False,
        message=f"Failed to generate a valid atomic test after {_MAX_RETRIES} attempts",
        error="\n".join(issues),
    )
