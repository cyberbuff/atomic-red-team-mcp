"""Execute atomic test tool."""

import asyncio
import time
from typing import List, Optional

from fastmcp import Context
from mcp.shared.exceptions import McpError
from pydantic import create_model

from atomic_red_team_mcp.models import ExecuteAtomicOutput, MetaAtomic
from atomic_red_team_mcp.services import load_atomics
from atomic_red_team_mcp.services.executor import AtomicRunner


async def execute_atomic(
    ctx: Context,
    auto_generated_guid: Optional[str] = None,
) -> ExecuteAtomicOutput:
    """Execute an atomic test on the server.

    WARNING: This tool executes security tests that may modify system state, create files,
    or perform actions that security tools may flag as malicious. Only use in controlled,
    isolated environments (test VMs, sandboxes).

    This tool runs a specific atomic test by its GUID. If you don't know the GUID, use the
    `query_atomics` tool first to search for tests and retrieve their GUIDs. The tool will
    prompt you for any required input arguments before execution.

    Args:
        auto_generated_guid: The unique identifier (UUID) of the atomic test to execute.
                            Example: "a8c41029-8d2a-4661-ab83-e5104c1cb667"

                            To find a test's GUID:
                            1. Use query_atomics to search for tests
                            2. Look for the auto_generated_guid field in the results
                            3. Pass that GUID to this function

                            If not provided, you will be prompted to enter it interactively.

    Returns:
        ExecuteAtomicOutput: Structured output containing:
            - success (bool): Whether the atomic test executed successfully
            - atomic_name (str): Name of the executed atomic test
            - technique_id (str): MITRE ATT&CK technique ID
            - platform (str): Platform the test was executed on
            - execution_time (float): Execution time in seconds
            - stdout (str): Standard output from the test execution
            - stderr (str): Standard error from the test execution
            - exit_code (int): Exit code from the executed command
            - error (str): Error message if execution failed

    Interactive Prompts:
        - If auto_generated_guid is not provided, you'll be asked to provide it
        - For tests with input_arguments, you'll be prompted with a structured form
          to fill in all arguments at once (or accept defaults)
        - You can cancel execution at any time during prompts

    Examples:
        # Execute a specific test
        execute_atomic(ctx, auto_generated_guid="a8c41029-8d2a-4661-ab83-e5104c1cb667")

        # Execute interactively (will prompt for GUID)
        execute_atomic(ctx)

    Workflow:
        1. Use query_atomics to find tests:
           query_atomics(ctx, query="powershell registry")

        2. Copy the auto_generated_guid from results

        3. Execute the test:
           execute_atomic(ctx, auto_generated_guid="<guid>")

        4. Review the execution output

    Notes:
        - This tool is disabled by default (requires ART_EXECUTION_ENABLED=true)
        - Tests run with the same privileges as the MCP server
        - Tests with elevation_required=true need sudo/admin privileges
        - Check test details with query_atomics before execution
        - Review supported_platforms to ensure compatibility
    """

    guid_to_find = None
    if not auto_generated_guid:
        try:
            result = await ctx.elicit(
                "What's the atomic test you want to execute?", response_type=str
            )
            if result.action == "accept":
                guid_to_find = result.data
            elif result.action == "decline":
                return ExecuteAtomicOutput(
                    success=False,
                    atomic_name="Unknown",
                    technique_id="Unknown",
                    platform="Unknown",
                    execution_time=0.0,
                    error="Atomic test GUID not provided",
                )
            else:  # cancel
                return ExecuteAtomicOutput(
                    success=False,
                    atomic_name="Unknown",
                    technique_id="Unknown",
                    platform="Unknown",
                    execution_time=0.0,
                    error="Operation cancelled by user",
                )
        except McpError:
            return ExecuteAtomicOutput(
                success=False,
                atomic_name="Unknown",
                technique_id="Unknown",
                platform="Unknown",
                execution_time=0.0,
                error=(
                    "The auto_generated_guid parameter is required because the MCP client "
                    "does not support elicitation (interactive prompts). Please provide the GUID directly: "
                    "execute_atomic(auto_generated_guid='<guid>'). "
                    "Use query_atomics to find the GUID of the test you want to execute."
                ),
            )
    else:
        guid_to_find = auto_generated_guid

    atomics: List[MetaAtomic] = load_atomics()

    matching_atomic = None
    for atomic in atomics:
        if str(atomic.auto_generated_guid) == guid_to_find:
            matching_atomic = atomic
            break

    if not matching_atomic:
        return ExecuteAtomicOutput(
            success=False,
            atomic_name="Unknown",
            technique_id="Unknown",
            platform="Unknown",
            execution_time=0.0,
            error=f"No atomic test found with GUID: {guid_to_find}",
        )

    ctx.info(
        f"Preparing to execute '{matching_atomic.name}' ({matching_atomic.technique_id})"
    )

    input_arguments: dict = {}

    if matching_atomic.input_arguments:
        # Collect all arguments in a single structured elicitation
        field_defs = {
            key: (str, spec.get("default", ""))
            for key, spec in matching_atomic.input_arguments.items()
        }
        InputArgsModel = create_model("InputArguments", **field_defs)

        arg_descriptions = "\n".join(
            f"  - {k}: {v.get('description', '')} (default: {v.get('default', '')})"
            for k, v in matching_atomic.input_arguments.items()
        )
        prompt = (
            f"Provide input arguments for '{matching_atomic.name}'.\n\n"
            f"Arguments:\n{arg_descriptions}\n\n"
            "Leave fields unchanged to use default values."
        )

        try:
            elicit_result = await ctx.elicit(prompt, response_type=InputArgsModel)
            if elicit_result.action == "accept":
                input_arguments = elicit_result.data.model_dump()
                ctx.info(f"Collected {len(input_arguments)} input argument(s)")
            elif elicit_result.action == "cancel":
                return ExecuteAtomicOutput(
                    success=False,
                    atomic_name=matching_atomic.name,
                    technique_id=matching_atomic.technique_id or "Unknown",
                    platform=", ".join(matching_atomic.supported_platforms),
                    execution_time=0.0,
                    error="Operation cancelled by user during input argument collection",
                )
            else:  # decline — use defaults
                input_arguments = {
                    k: v.get("default", "")
                    for k, v in matching_atomic.input_arguments.items()
                }
        except McpError:
            # Client doesn't support elicitation — fall back to defaults
            input_arguments = {
                k: v.get("default", "")
                for k, v in matching_atomic.input_arguments.items()
            }
            ctx.info("Elicitation not supported; using default argument values")

    start_time = time.time()
    try:
        with AtomicRunner(
            matching_atomic.auto_generated_guid, input_arguments
        ) as runner:
            await ctx.report_progress(
                progress=0, total=3, message="Running prerequisites..."
            )
            await asyncio.to_thread(runner.run_phase, "prerequisites", get_prereqs=True)

            await ctx.report_progress(progress=1, total=3, message="Executing test...")
            await asyncio.to_thread(runner.run_phase, "execution")

            await ctx.report_progress(progress=2, total=3, message="Running cleanup...")
            await asyncio.to_thread(runner.run_phase, "cleanup", cleanup=True)

            await ctx.report_progress(progress=3, total=3, message="Complete")

        execution_time = time.time() - start_time
        outputs = runner.captured_outputs

        stdout_parts = []
        stderr_parts = []
        exit_codes = []
        for output in outputs:
            phase = output.get("phase", "unknown")
            stdout_parts.append(f"[{phase}] {output.get('output', '')}")
            stderr_parts.append(f"[{phase}] {output.get('errors', '')}")
            if output.get("return_code") is not None:
                exit_codes.append(output.get("return_code"))

        success = all(code == 0 for code in exit_codes) if exit_codes else True
        ctx.info(f"Execution complete in {execution_time:.2f}s, success={success}")
        return ExecuteAtomicOutput(
            success=success,
            atomic_name=matching_atomic.name,
            technique_id=matching_atomic.technique_id or "Unknown",
            platform=", ".join(matching_atomic.supported_platforms),
            execution_time=execution_time,
            stdout="\n".join(stdout_parts),
            stderr="\n".join(stderr_parts),
            exit_code=exit_codes[-1] if exit_codes else 0,
        )
    except Exception as e:
        return ExecuteAtomicOutput(
            success=False,
            atomic_name=matching_atomic.name,
            technique_id=matching_atomic.technique_id or "Unknown",
            platform=", ".join(matching_atomic.supported_platforms),
            execution_time=time.time() - start_time,
            error=f"Error running test: {e}",
        )
