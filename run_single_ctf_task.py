"""Run a single CTF task via the TaskRunner CLI.

This script is primarily intended to be invoked by ``run_ctf.py`` which
executes it as a subprocess for every task/model combination.  Therefore we
ensure that:

1. Any logging performed by the underlying ``TaskRunner`` still works as
   before.
2. We emit a concise JSON payload **to STDOUT** when the run finishes so that
   the parent process can parse the outcome without needing to inspect the
   log files.

Exit status ``0`` means the run completed without *unexpected* exceptions.  A
failed task (i.e., wrong flag) is **not** treated as an error – the JSON field
``"result"`` will be ``false`` in that case.
"""

import os
import json
import sys
import traceback
import signal
from typing import Optional

from src.agent.task_runner import TaskRunner
from src.utils import single_task_args

# Will be populated with the active TaskRunner instance so that the signal
# handler can access it.
_ACTIVE_RUNNER: Optional[TaskRunner] = None

# Optional experiment identifier passed via ``--id``.  We expose it as a
# module-level global so that it can be inspected elsewhere if necessary.
OUTPUT_ID: str = ""

# ---------------------------------------------------------------------------
# Limit thread-hungry math libraries (OpenBLAS, MKL, OpenMP, etc.) to a single
# worker thread **before** they are imported anywhere else.  This prevents
# errors such as "OpenBLAS blas_thread_init: pthread_create failed… Resource
# temporarily unavailable" when many tasks run concurrently.
# Users can override the limits by explicitly exporting the variables with a
# different value *before* invoking this script.
# ---------------------------------------------------------------------------
for _var in (
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_var, "1")


def _graceful_shutdown(signum, frame):  # noqa: D401 – callback, ignore frame
    """Signal handler to terminate the TaskRunner and its server cleanly."""
    global _ACTIVE_RUNNER  # noqa: PLW0603 – required to modify global

    if _ACTIVE_RUNNER is not None:
        try:
            _ACTIVE_RUNNER.log(f"Received signal {signum}; shutting down gracefully…")
            if _ACTIVE_RUNNER.server_manager:
                _ACTIVE_RUNNER.server_manager.stop()
        except Exception:
            pass

    # Exit with 128 + signal number (conventional for Unix)
    sys.exit(128 + signum)


def main() -> None:  # noqa: D401 – simple function
    """CLI entry-point."""

    # --------------------------------------------------------------
    # Extract custom CLI flag --id (if present) **before** delegating to the
    # shared argument parser, mirroring the approach used in
    # *run_ctf_parallel.py*.
    # --------------------------------------------------------------
    argv = sys.argv.copy()
    global OUTPUT_ID  # noqa: PLW0603 – ensure assignments modify the module-level vars

    if "--id" in argv:
        idx = argv.index("--id")
        try:
            id_val = argv[idx + 1]
        except IndexError:
            print("Invalid value for --id", file=sys.stderr)
            sys.exit(2)

        # Remove the custom option so that *single_task_args()* does not
        # attempt to process it (it would otherwise ignore it silently).
        del argv[idx : idx + 2]
        sys.argv = argv

        OUTPUT_ID = id_val
    else:
        OUTPUT_ID = ""

    args = single_task_args()

    # Attach the identifier to the parsed namespace so downstream components
    # (in particular *TaskRunner*) can access it straightforwardly.
    setattr(args, "id", OUTPUT_ID)

    try:
        global _ACTIVE_RUNNER  # noqa: PLW0603 – allow assignment

        # Register signal handlers **before** heavy processing starts so that
        # we can react to Ctrl-C or SIGTERM.
        signal.signal(signal.SIGINT, _graceful_shutdown)
        signal.signal(signal.SIGTERM, _graceful_shutdown)

        runner = TaskRunner(args)
        _ACTIVE_RUNNER = runner

        task_result = runner.run()  # ``True`` when flag verified successfully.
        summary = {
            "task_path": args.task_path,
            "model": args.model,
            "result": task_result,
            "id": OUTPUT_ID,
        }

        # Always print summary on **one line** so the caller can ``json.loads``
        # it easily.
        print(json.dumps(summary, ensure_ascii=False))

    except Exception as exc:  # noqa: BLE001 – we want to catch everything
        # If 'runner' exists it means TaskRunner initialised successfully – log
        # the error through its logger.  Otherwise fall back to stderr.
        if 'runner' in locals():
            runner.log(f"Unexpected error in run_single_task.py: {exc}\n{traceback.format_exc()}")
            try:
                # Persist failure reason so that parallel runner can resume correctly.
                runner._save_state(f"error: {exc}")  # type: ignore[attr-defined]
            except Exception:
                # Ignore any issues during error persistence.
                pass
        else:
            print(f"Unexpected error before TaskRunner initialisation: {exc}", file=sys.stderr)

        # Emit failure JSON so the caller can record the reason.
        error_summary = {
            "task_path": args.task_path,
            "model": args.model,
            "result": False,
            "error": str(exc),
        }
        print(json.dumps(error_summary, ensure_ascii=False))

        # Non-zero exit so external scripts know something went wrong.
        sys.exit(1)


if __name__ == "__main__":
    main()

