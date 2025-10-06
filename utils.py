import json
import logging
import os
from uuid import UUID

from atomic_operator import AtomicOperator
from atomic_operator.base import Base
from atomic_operator.execution.runner import Runner

# Configure logging to stderr to avoid interfering with MCP JSON protocol
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

art = AtomicOperator()
atomics_dir: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atomics")


def run_test(guid: UUID, input_arguments: dict):
    guid = str(guid)
    logger.info(f"Running test {guid} with input arguments {input_arguments}")
    # Monkey-patch the _set_input_arguments method to use our custom values
    # This workaround is needed because atomic_operator's __check_arguments validation
    # incorrectly rejects kwargs that should be passed to tests
    original_set_input_arguments = Base._set_input_arguments

    def patched_set_input_arguments(self, test, **kwargs):
        # Call original with our custom input arguments
        return original_set_input_arguments(self, test, **input_arguments)

    Base._set_input_arguments = patched_set_input_arguments

    # Capture command outputs from print_process_output
    captured_outputs = []
    current_phase = "unknown"
    original_print_process_output = Runner.print_process_output

    def patched_print_process_output(self, command, return_code, output, errors):
        nonlocal current_phase
        # Call original method to maintain normal logging behavior
        return_dict = original_print_process_output(
            self, command, return_code, output, errors
        )

        # Store the captured output for later retrieval with phase information
        captured_outputs.append(
            {
                "phase": current_phase,
                "command": command,
                "return_code": return_code,
                "output": output.decode("utf-8", errors="replace")
                if isinstance(output, bytes)
                else output,
                "errors": errors.decode("utf-8", errors="replace")
                if isinstance(errors, bytes)
                else errors,
            }
        )
        return return_dict

    Runner.print_process_output = patched_print_process_output

    try:
        # Phase 1: Prerequisites
        current_phase = "prerequisites"
        logger.info(f"Running prerequisites for test {guid}")
        art.run(
            get_prereqs=True,
            prompt_for_input_args=False,
            atomics_path=atomics_dir,
            test_guids=[guid],
            debug=True,
        )

        # Phase 2: Execution
        current_phase = "execution"
        logger.info(f"Running execution for test {guid}")
        art.run(
            prompt_for_input_args=False,
            atomics_path=atomics_dir,
            test_guids=[guid],
            debug=True,
        )

        # Phase 3: Cleanup
        logger.info(f"Running cleanup for test {guid}")
        current_phase = "cleanup"
        art.run(
            cleanup=True,
            prompt_for_input_args=False,
            atomics_path=atomics_dir,
            test_guids=[guid],
            debug=True,
        )

        return json.dumps(captured_outputs)
    except Exception as e:
        return json.dumps({"error": f"Error running test: {e}"})
    finally:
        # Restore patched methods
        Base._set_input_arguments = original_set_input_arguments
        Runner.print_process_output = original_print_process_output
