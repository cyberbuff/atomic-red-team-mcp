"""Service for executing Atomic Red Team tests."""

import json
import logging
from uuid import UUID

from atomic_operator import AtomicOperator
from atomic_operator.base import Base
from atomic_operator.execution.runner import Runner

from atomic_red_team_mcp.utils.config import get_atomics_dir

logger = logging.getLogger(__name__)


class AtomicRunner:
    """Context manager for running atomic test phases with shared monkey-patched state.

    Separates the monkey-patch lifecycle from phase execution so callers can
    await progress notifications between phases without tearing down the patches.
    """

    def __init__(
        self, guid: UUID | str, input_arguments: dict, art_dir: str | None = None
    ) -> None:
        self.guid = str(guid)
        self.art_dir = art_dir or get_atomics_dir()
        self.input_arguments = input_arguments
        self.captured_outputs: list[dict] = []
        self._current_phase = "unknown"
        self._art: AtomicOperator | None = None
        self._orig_set_input = None
        self._orig_print = None

    def __enter__(self) -> "AtomicRunner":
        self._art = AtomicOperator()
        self._orig_set_input = Base._set_input_arguments
        self._orig_print = Runner.print_process_output

        input_args = self.input_arguments
        orig_set = self._orig_set_input
        runner = self
        orig_print = self._orig_print

        def patched_set_input(base_self, test, **kwargs):
            return orig_set(base_self, test, **input_args)

        def patched_print(runner_self, command, return_code, output, errors):
            result = orig_print(runner_self, command, return_code, output, errors)
            runner.captured_outputs.append(
                {
                    "phase": runner._current_phase,
                    "command": command,
                    "return_code": return_code,
                    "output": (
                        output.decode("utf-8", errors="replace")
                        if isinstance(output, bytes)
                        else output
                    ),
                    "errors": (
                        errors.decode("utf-8", errors="replace")
                        if isinstance(errors, bytes)
                        else errors
                    ),
                }
            )
            return result

        Base._set_input_arguments = patched_set_input
        Runner.print_process_output = patched_print
        return self

    def __exit__(self, *args) -> None:
        Base._set_input_arguments = self._orig_set_input
        Runner.print_process_output = self._orig_print

    def run_phase(self, phase: str, **kwargs) -> None:
        """Run a single phase of the atomic test (blocking)."""
        self._current_phase = phase
        logger.info(f"Running {phase} for test {self.guid}")
        self._art.run(
            prompt_for_input_args=False,
            atomics_path=self.art_dir,
            test_guids=[self.guid],
            debug=True,
            **kwargs,
        )


def run_test(guid: UUID, input_arguments: dict, art_dir: str | None = None) -> str:
    """Execute an atomic test by GUID with the specified input arguments."""
    logger.info(f"Running test {guid} with input arguments {input_arguments}")
    try:
        with AtomicRunner(guid, input_arguments, art_dir) as runner:
            runner.run_phase("prerequisites", get_prereqs=True)
            runner.run_phase("execution")
            runner.run_phase("cleanup", cleanup=True)
        return json.dumps(runner.captured_outputs)
    except Exception as e:
        return json.dumps({"error": f"Error running test: {e}"})
