"""Execute atomic test tool."""

import logging
from typing import List, Optional

from fastmcp import Context

from atomic_red_team_mcp.models import Atomic
from atomic_red_team_mcp.services import load_atomics, run_test

logger = logging.getLogger(__name__)


async def execute_atomic(
    ctx: Context,
    auto_generated_guid: Optional[str] = None,
) -> str:
    """Execute an atomic test by GUID.

        If technique_id or name is provided, use `query_atomics` to get the atomic test's auto_generated_guid and then execute the atomic test.

    Args:
        auto_generated_guid: The GUID of the atomic test

    At least one parameter must be provided.
    """

    guid_to_find = None
    if not auto_generated_guid:
        result = await ctx.elicit(
            "What's the atomic test you want to execute?", response_type=str
        )
        if result.action == "accept":
            guid_to_find = result.data
        elif result.action == "decline":
            return "Atomic test not provided"
        else:  # cancel
            return "Operation cancelled"
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
    if matching_atomic.input_arguments:
        logger.info(
            f"The atomic test '{matching_atomic.name}' has {len(matching_atomic.input_arguments)} input argument(s)"
        )

        for key, value in matching_atomic.input_arguments.items():
            default_value = value.get("default", "")
            description = value.get("description", "No description available")

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

    return run_test(matching_atomic.auto_generated_guid, input_arguments)
