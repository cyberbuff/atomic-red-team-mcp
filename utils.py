from atomic_operator import AtomicOperator
from atomic_operator.base import Base
from atomic_operator.execution.runner import Runner
import os
import json

art = AtomicOperator()
atomics_dir: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atomics")


def run_test(guid: str, input_arguments: dict):
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
                "return_dict": return_dict,
            }
        )
        return return_dict

    Runner.print_process_output = patched_print_process_output

    try:
        # Phase 1: Prerequisites
        current_phase = "prerequisites"
        art.run(
            get_prereqs=True,
            prompt_for_input_args=False,
            atomics_path=atomics_dir,
            test_guids=[guid],
            debug=True,
        )

        # Phase 2: Execution
        current_phase = "execution"
        art.run(
            prompt_for_input_args=False,
            atomics_path=atomics_dir,
            test_guids=[guid],
            debug=True,
        )

        # Phase 3: Cleanup
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
        return f"Error running test: {e}"
    finally:
        # Restore patched methods
        Base._set_input_arguments = original_set_input_arguments
        Runner.print_process_output = original_print_process_output


if __name__ == "__main__":
    print(
        run_test(
            "4ff64f0b-aaf2-4866-b39d-38d9791407cc",
            {"output_file": "/tmp/processes.txt"},
        )
    )
