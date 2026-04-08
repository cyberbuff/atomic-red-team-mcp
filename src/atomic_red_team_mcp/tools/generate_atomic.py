"""Generate atomic test tool using LLM sampling."""

from fastmcp import Context

from atomic_red_team_mcp.models import Atomic, ValidationOutput


async def generate_atomic(
    ctx: Context,
    technique_id: str,
    platform: str = "linux",
    description: str = "",
) -> ValidationOutput:
    """Generate an atomic test for a MITRE ATT&CK technique using AI assistance.

    Uses the MCP client's LLM to draft an atomic test YAML for the given technique and
    platform, then validates it automatically. Returns a ValidationOutput so you can
    immediately see if the generated test is ready to use or needs adjustments.

    Args:
        technique_id: MITRE ATT&CK technique ID (e.g., "T1059.001").
                      Used to focus the generated test on the correct technique.

        platform: Target platform for the test. Valid values: windows, linux, macos.
                  Defaults to "linux".

        description: Optional free-text description of what the test should do or
                     demonstrate. Leave blank to let the AI determine the best approach
                     for the technique.

    Returns:
        ValidationOutput: Validation result for the generated YAML, containing:
            - valid (bool): Whether the generated test passes schema validation
            - message (str): Success or error message
            - atomic_name (str): Name of the generated test (if valid)
            - supported_platforms (list): Platforms declared in the test (if valid)
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

    focus = f" The test should: {description}." if description else ""
    prompt = (
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

    try:
        result = await ctx.sample(prompt, max_tokens=1024)
        yaml_text = result.text.strip()

        # Strip markdown code fences if the LLM added them anyway
        if yaml_text.startswith("```"):
            lines = yaml_text.splitlines()
            yaml_text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()
    except Exception as e:
        return ValidationOutput(
            valid=False,
            message="Sampling failed",
            error=f"Could not sample from LLM: {e}. Ensure the MCP client supports server-side sampling.",
        )

    # Validate the generated YAML
    import yaml
    from pydantic import ValidationError

    try:
        atomic_data = yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        return ValidationOutput(
            valid=False,
            message="Generated YAML is invalid",
            error=f"YAML parse error: {e}",
        )

    if not atomic_data:
        return ValidationOutput(
            valid=False,
            message="Generated YAML is empty",
            error="The LLM returned empty content.",
        )

    warnings = []
    if "auto_generated_guid" in atomic_data:
        warnings.append(
            "WARNING: Remove 'auto_generated_guid' - system generates this automatically"
        )
    if atomic_data.get("executor", {}).get("command"):
        cmd = atomic_data["executor"]["command"].lower()
        if "echo" in cmd or "print" in cmd or "write-host" in cmd:
            warnings.append(
                "WARNING: Avoid echo/print/Write-Host statements in test commands"
            )

    try:
        atomic = Atomic(**atomic_data)
    except (ValidationError, Exception) as e:
        return ValidationOutput(
            valid=False,
            message="Generated test failed schema validation",
            error=str(e),
        )

    if warnings:
        msg = "Generated atomic test is valid with warnings:\n" + "\n".join(warnings)
    else:
        msg = f"Generated atomic test '{atomic.name}' is valid and ready to use."

    ctx.info(f"Generated atomic test '{atomic.name}' for {technique_id}/{platform}")
    return ValidationOutput(
        valid=True,
        message=msg,
        atomic_name=atomic.name,
        supported_platforms=atomic.supported_platforms,
        warnings=warnings if warnings else None,
    )
