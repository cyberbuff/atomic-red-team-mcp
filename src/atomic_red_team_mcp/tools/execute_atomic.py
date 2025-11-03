"""Execute atomic test tool."""

import logging
from typing import List, Optional

from fastmcp import Context
from mcp.shared.exceptions import McpError

from atomic_red_team_mcp.models import Atomic
from atomic_red_team_mcp.services import load_atomics, run_test

logger = logging.getLogger(__name__)


async def execute_atomic(
    ctx: Context,
    auto_generated_guid: Optional[str] = None,
) -> str:
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
        str: Execution result message containing:
            - Success/failure status
            - Command output (stdout/stderr)
            - Exit codes
            - Any execution errors or warnings

            The exact format depends on the executor type (powershell, bash, sh, cmd, manual)

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

    Raises:
        Exception: If test GUID is not found in the atomic tests database
        Exception: If execution fails due to system errors or invalid commands

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
                return "Atomic test not provided"
            else:  # cancel
                return "Operation cancelled"
        except McpError as e:
            # Client doesn't support elicitation
            logger.warning(
                f"Elicitation not supported by client: {e}. auto_generated_guid parameter is required."
            )
            return (
                "Error: The auto_generated_guid parameter is required because the MCP client "
                "does not support elicitation (interactive prompts). Please provide the GUID directly:\n\n"
                "execute_atomic(auto_generated_guid='<guid>')\n\n"
                "Use query_atomics to find the GUID of the test you want to execute."
            )
    else:
        guid_to_find = auto_generated_guid

    atomics: List[Atomic] = load_atomics()

    matching_atomic = None

    for atomic in atomics:
        if str(atomic.auto_generated_guid) == guid_to_find:
            matching_atomic = atomic
            break

    if not matching_atomic:
        return "No atomic test found"

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
                        return "Operation cancelled by user"
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

    return run_test(matching_atomic.auto_generated_guid, input_arguments)
