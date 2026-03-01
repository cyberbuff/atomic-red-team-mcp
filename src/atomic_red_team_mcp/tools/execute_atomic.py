"""Execute atomic test tool."""

import json
import logging
import time
from typing import List, Optional

from fastmcp import Context
from mcp.shared.exceptions import McpError

from atomic_red_team_mcp.models import ExecuteAtomicOutput, MetaAtomic
from atomic_red_team_mcp.services import load_atomics, run_test

logger = logging.getLogger(__name__)


async def execute_atomic(
    ctx: Context,
    auto_generated_guid: Optional[str] = None,
) -> ExecuteAtomicOutput:
    """Execute an atomic test on the server.

    ⚠️ WARNING: This tool executes security tests that may modify system state, create files,
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
        - For tests with input_arguments, you'll be prompted for each argument:
          * You can accept the default value by typing "default"
          * Or provide a custom value
          * Each prompt shows the argument description and default value
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

        5. If needed, run cleanup (if test has cleanup_command)

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
        except McpError as e:
            # Client doesn't support elicitation
            logger.warning(
                f"Elicitation not supported by client: {e}. auto_generated_guid parameter is required."
            )
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

    input_arguments = {}
    elicitation_supported = True

    if matching_atomic.input_arguments:
        logger.info(
            f"The atomic test '{matching_atomic.name}' has {len(matching_atomic.input_arguments)} input argument(s)"
        )

        for key, value in matching_atomic.input_arguments.items():
            default_value = value.get("default", "")
            description = value.get("description", "No description available")

            # Try elicitation first, fall back to defaults if not supported
            try:
                if elicitation_supported:
                    question = f"""
Input argument: {key}
Description: {description}
Default value: {default_value}

Would you like to use the default value or provide a custom value?
(Reply with "default" to use the default, or provide your custom value)
"""
                    result = await ctx.elicit(question, response_type=str)

                    if result.action == "accept":
                        response = result.data.strip().lower()
                        if response == "default" or response == "use default":
                            input_arguments[key] = default_value
                            logger.info(
                                f"{matching_atomic.auto_generated_guid} - Using default value for '{key}': {default_value}"
                            )
                        else:
                            # Use the provided value
                            input_arguments[key] = result.data.strip()
                            logger.info(
                                f"{matching_atomic.auto_generated_guid} - Using custom value for '{key}': {result.data.strip()}"
                            )
                    elif result.action == "decline":
                        # If declined, use default
                        input_arguments[key] = default_value
                        logger.info(f"Using default value for '{key}': {default_value}")
                    else:  # cancel
                        return ExecuteAtomicOutput(
                            success=False,
                            atomic_name=matching_atomic.name,
                            technique_id=matching_atomic.technique_id or "Unknown",
                            platform=", ".join(matching_atomic.supported_platforms),
                            execution_time=0.0,
                            error="Operation cancelled by user during input argument collection",
                        )
            except McpError as e:
                # Client doesn't support elicitation, use default values for all arguments
                if elicitation_supported:
                    logger.warning(
                        f"Elicitation not supported by client: {e}. Using default values for all input arguments."
                    )
                    elicitation_supported = False

                input_arguments[key] = default_value
                logger.info(
                    f"{matching_atomic.auto_generated_guid} - Using default value for '{key}': {default_value} (elicitation not supported)"
                )

    # Execute the test and measure time
    start_time = time.time()
    result_json = run_test(matching_atomic.auto_generated_guid, input_arguments)
    execution_time = time.time() - start_time

    # Parse the JSON result
    try:
        result_data = json.loads(result_json)

        # Check if there was an error
        if isinstance(result_data, dict) and "error" in result_data:
            return ExecuteAtomicOutput(
                success=False,
                atomic_name=matching_atomic.name,
                technique_id=matching_atomic.technique_id or "Unknown",
                platform=", ".join(matching_atomic.supported_platforms),
                execution_time=execution_time,
                error=result_data["error"],
            )

        # Aggregate outputs from all phases
        stdout_parts = []
        stderr_parts = []
        exit_codes = []

        for output in result_data:
            phase = output.get("phase", "unknown")
            stdout_parts.append(f"[{phase}] {output.get('output', '')}")
            stderr_parts.append(f"[{phase}] {output.get('errors', '')}")
            if output.get("return_code") is not None:
                exit_codes.append(output.get("return_code"))

        # Determine success based on exit codes
        success = all(code == 0 for code in exit_codes) if exit_codes else True
        final_exit_code = exit_codes[-1] if exit_codes else 0

        return ExecuteAtomicOutput(
            success=success,
            atomic_name=matching_atomic.name,
            technique_id=matching_atomic.technique_id or "Unknown",
            platform=", ".join(matching_atomic.supported_platforms),
            execution_time=execution_time,
            stdout="\n".join(stdout_parts),
            stderr="\n".join(stderr_parts),
            exit_code=final_exit_code,
        )
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse execution result: {e}")
        return ExecuteAtomicOutput(
            success=False,
            atomic_name=matching_atomic.name,
            technique_id=matching_atomic.technique_id or "Unknown",
            platform=", ".join(matching_atomic.supported_platforms),
            execution_time=execution_time,
            error=f"Failed to parse execution result: {e}",
        )
