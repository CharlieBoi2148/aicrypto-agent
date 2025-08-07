from __future__ import annotations

"""Parallel batch runner for CTF tasks.

This script is a drop-in replacement for *run_ctf.py* that executes up to
*max_workers* instances of `python run_single_task.py --model … --task-path …`
concurrently.  A task is only launched if a record for the given
``(model, task_path)`` pair is **not** already present in
``outputs/CTF/results/ctf_<model>_task_results.json`` – this makes the script
safe to resume and ideal for long-running background execution.

Usage examples
--------------
Run 32 tasks in parallel (the default):

    python run_ctf_parallel.py --model gpt-4

Run several models at once:

    python run_ctf_parallel.py --model "gpt-4,claude-3" --jobs 16

If you want the whole job to continue after closing your shell, combine the
command with *nohup* or your preferred job scheduler, e.g.:

    nohup python run_ctf_parallel.py --model gpt-4 &

The implementation mirrors the logic of *run_ctf.py* but utilises
``concurrent.futures.ProcessPoolExecutor`` for concurrency.
"""

from pathlib import Path
import json
from typing import Dict, List, Tuple, Union
import subprocess
import sys
import os
import signal
import concurrent.futures as cf
import yaml
import atexit
import itertools

# Optional: use psutil for reliable process tree traversal.
try:
    import psutil  # type: ignore
except ImportError:  # pragma: no cover
    psutil = None  # type: ignore

from src.utils import single_task_args

# ---------------------------------------------------------------------------
# Global state (will be filled in the `__main__` guard)
# ---------------------------------------------------------------------------

# Optional experiment identifier, forwarded via `--id` CLI flag.  When set, all
# artefacts are stored under ``outputs/CTF-<OUTPUT_ID>/`` instead of the
# default ``outputs/CTF/`` path so that multiple parallel runs do not
# interfere with each other.
OUTPUT_ID: str = ""

# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

RESULTS_DIR = Path("outputs/CTF/results")

JsonResult = Union[str, bool]  # the value type stored in the results file


# ----------------------------------------------------------------------------
# Helpers copied from *run_ctf.py* with minimal changes
# ----------------------------------------------------------------------------

def _gather_task_paths(base_dir: Path) -> List[str]:
    """Return a list of all task directories below *base_dir*.

    Expected structure::

        data/CTF/<category>/<task>/

    Only directories whose names start with a digit (e.g. ``01-…``) are treated
    as tasks.  Hidden directories are ignored.
    """

    task_dirs: List[str] = []
    categories = sorted(
        d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    )

    for category in categories:
        for task_dir in sorted(category.iterdir()):
            if task_dir.is_dir() and task_dir.name[0].isdigit():
                task_dirs.append(str(task_dir))

    return task_dirs


def _load_previous_results(path: Path) -> Dict[str, JsonResult]:
    if path.is_file():
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # Corrupted file – start fresh.
            return {}

        # Legacy support: convert list[dict] -> dict
        if isinstance(data, list):
            legacy: Dict[str, JsonResult] = {}
            for item in data:
                if isinstance(item, dict):
                    legacy.update(item)
            return legacy
        return data  # type: ignore[return-value]
    return {}


def _save_results(path: Path, results: Dict[str, JsonResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        # Dump with sorted keys so that results.json stays in deterministic order.
        json.dump(results, f, indent=2, ensure_ascii=False, sort_keys=True)


# ----------------------------------------------------------------------------
# Sub-process execution helper
# ----------------------------------------------------------------------------

def _run_task_subprocess(model: str, task_dir: str) -> JsonResult:
    """Execute *run_single_task.py* for *task_dir*/*model* and return its result.

    The child script prints a single-line JSON summary to *stdout* – we parse
    that to obtain the boolean *result* field.  Any exception or non-zero exit
    code is converted into a human-readable string so that it can be stored in
    the results JSON file.
    """

    cmd = [
        sys.executable,
        "run_single_task.py",
        "--model",
        model,
        "--task-path",
        task_dir,
    ]

    # Pass the experiment identifier downstream so that *run_single_task.py*
    # and the underlying *TaskRunner* can place their artefacts in the correct
    # directory hierarchy.
    if OUTPUT_ID:
        cmd.extend(["--id", OUTPUT_ID])

    # ------------------------------------------------------------------
    # Environment tuning: limit BLAS / OpenMP libraries to *one* thread so
    # that spawning many concurrent subprocesses does not exhaust the thread
    # quota ("Resource temporarily unavailable", OpenBLAS pthread_create
    # failures).  We only set the variables when they are **not** defined so
    # that power users can override them from the outside.
    # ------------------------------------------------------------------
    env = os.environ.copy()
    for var in (
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OMP_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        env.setdefault(var, "1")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,  # so we can terminate the whole group if needed
        env=env,
    )

    try:
        stdout, stderr = proc.communicate()
    except KeyboardInterrupt:
        # Propagate the interrupt to the child group first, then re-raise.
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        except Exception:
            pass
        proc.wait(timeout=5)
        raise

    if proc.returncode != 0:
        return f"error (exit={proc.returncode}): {stderr.strip()[:500]}"

    stdout_lines = stdout.strip().splitlines()
    if not stdout_lines:
        return "no output from child process"

    last_line = stdout_lines[-1]
    try:
        summary = json.loads(last_line)
        # Successful flag retrieval
        if summary.get("result") is True:
            return True
        # When result is False, but an explicit error message is provided, keep it.
        if "error" in summary and summary["error"]:
            return f"error: {summary['error']}"
        # Otherwise just return False to indicate failure without extra info.
        return False
    except json.JSONDecodeError:
        # Child produced something unexpected – store raw stdout for debugging.
        combined = stdout.strip()
        return f"unparseable output: {combined[:500]}"


# ----------------------------------------------------------------------------
# Parallel execution logic
# ----------------------------------------------------------------------------

def _run_task(model: str, task_dir: str) -> Tuple[str, JsonResult]:
    """Helper wrapper to satisfy *ProcessPoolExecutor* API."""
    return task_dir, _run_task_subprocess(model, task_dir)


# ----------------------------------------------------------------------------
# Entry-point
# ----------------------------------------------------------------------------

def _load_models_from_yaml(path: Path) -> List[str]:
    """Return a list of **all** top-level keys in the given YAML file."""
    if not path.is_file():
        print(f"Model configuration file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(f"Failed to parse YAML: {exc}", file=sys.stderr)
            sys.exit(1)

    if not isinstance(data, dict):
        print("Unexpected structure in model.yaml – expected mapping at top level", file=sys.stderr)
        sys.exit(1)

    return list(data.keys())


def _terminate_descendants(sig: int = signal.SIGTERM) -> None:
    """Send *sig* to all descendant processes of the current process.

    Uses *psutil* when available; otherwise falls back to ``pkill -P``.
    """

    if psutil is not None:
        parent = psutil.Process()
        for proc in parent.children(recursive=True):
            try:
                proc.send_signal(sig)
            except Exception:
                pass
    else:
        # Fallback: best-effort using pkill; ignore errors.
        try:
            subprocess.run(["pkill", f"-{sig}", "-P", str(os.getpid())], check=False)
        except Exception:
            pass


def main() -> None:
    args = single_task_args()

    # Load *all* models from config/model.yaml (ignoring any CLI value).
    models = _load_models_from_yaml(Path("config/model.yaml"))

    # Number of parallel jobs – fall back to 32 when not supplied via CLI.
    jobs: int = getattr(args, "jobs", 32)  # type: ignore[attr-defined]

    if not models:
        print("No models found in config/model.yaml", file=sys.stderr)
        sys.exit(1)

    base_task_dir = Path("data/CTF")
    task_paths = _gather_task_paths(base_task_dir)

    # ------------------------------------------------------------------
    # Build per-model task queues and load existing results
    # ------------------------------------------------------------------
    model_infos: Dict[str, Dict[str, object]] = {}

    for model in models:
        result_path = RESULTS_DIR / f"ctf_{model}_task_results.json"
        completed: Dict[str, JsonResult] = _load_previous_results(result_path)

        # Filter out tasks that have been completed already.
        remaining: List[str] = [tp for tp in task_paths if tp not in completed]
        if not remaining:
            print(f"All tasks completed for model {model} – skipping.")
            continue

        model_infos[model] = {
            "result_path": result_path,
            "completed": completed,
            "queue": remaining,  # still pending
        }

    # --------------------新增打印待执行任务数量--------------------
    total_pending_tasks = 0
    for mdl, info in model_infos.items():
        num_pending = len(info["queue"])  # type: ignore[index]
        total_pending_tasks += num_pending
        print(f"[CTF] Model {mdl}: {num_pending} tasks to run.")
    print(f"[CTF] Total tasks to execute across all models: {total_pending_tasks}")
    # -----------------------------------------------------------

    if not model_infos:
        print("No work left – exiting.")
        return

    print(
        f"Launching parallel run: {len(model_infos)} models, "
        f"up to {jobs} concurrent workers, tasks distributed evenly across models."
    )

    # ------------------------------------------------------------------
    # Scheduler: distribute tasks evenly across models while utilising all
    #            available worker slots.
    # ------------------------------------------------------------------
    with cf.ProcessPoolExecutor(max_workers=jobs) as executor:
        future_to_info: Dict[cf.Future, Tuple[str, str]] = {}

        # Create an infinite cyclic iterator over the models for fair scheduling.
        model_cycle = itertools.cycle(model_infos.keys())

        def _enqueue_next() -> bool:
            """Attempt to submit the next task in round-robin order.

            Returns True when a task was scheduled and False when no tasks are
            left in any queue.
            """
            for _ in range(len(model_infos)):
                model = next(model_cycle)
                queue: List[str] = model_infos[model]["queue"]  # type: ignore[index]
                if queue:
                    task_dir = queue.pop(0)
                    # ------------------新增打印正在执行的脚本------------------
                    print(f"[CTF:{model}] Running task {task_dir}")
                    # ------------------------------------------------------
                    fut = executor.submit(_run_task, model, task_dir)
                    future_to_info[fut] = (model, task_dir)
                    return True
            return False  # All queues are empty.

        # Prime the executor with as many initial jobs as allowed.
        pending_jobs = sum(len(info["queue"]) for info in model_infos.values())
        for _ in range(min(jobs, pending_jobs)):
            if not _enqueue_next():
                break

        try:
            while future_to_info:
                # Wait for the **next** task to finish.
                done, _ = cf.wait(future_to_info.keys(), return_when=cf.FIRST_COMPLETED)
                for future in done:
                    model, task_dir = future_to_info.pop(future)
                    info = model_infos[model]

                    try:
                        td, result = future.result()
                    except Exception as exc:  # noqa: BLE001
                        result = f"internal error: {exc}"
                        td = task_dir

                    # Record & persist
                    info["completed"][td] = result  # type: ignore[index]
                    _save_results(info["result_path"], info["completed"])  # type: ignore[arg-type]
                    print(f"[CTF:{model}] {td} -> {result}")

                    # Keep the worker pool filled while respecting fairness.
                    _enqueue_next()

        except KeyboardInterrupt:
            print("\nInterrupted by user – shutting down executor…", file=sys.stderr)
            executor.shutdown(wait=False, cancel_futures=True)

            # Ensure all descendant processes are terminated.
            _terminate_descendants(signal.SIGTERM)
            # Give them a moment, then SIGKILL any survivors.
            if psutil is not None:
                import time
                time.sleep(1)
                _terminate_descendants(signal.SIGKILL)

            sys.exit(130)


if __name__ == "__main__":
    # Inject an extra CLI option (--jobs) without touching src.utils.parser.
    # We parse *sys.argv* manually here because *single_task_args()* swallows
    # unknown args.  The following code extracts "--jobs N" if present.
    argv = sys.argv.copy()
    if "--jobs" in argv:
        idx = argv.index("--jobs")
        try:
            jobs_val = int(argv[idx + 1])
        except (ValueError, IndexError):
            print("Invalid value for --jobs", file=sys.stderr)
            sys.exit(2)
        # Remove the custom option before delegating to single_task_args().
        del argv[idx : idx + 2]
        sys.argv = argv
        # We will attach this attribute to the parsed args later on.
        _extra_jobs = jobs_val
    else:
        _extra_jobs = 32

    # ------------------------------------------------------------------
    # Custom CLI option: --id N (optional experiment identifier)
    # ------------------------------------------------------------------
    if "--id" in argv:
        idx = argv.index("--id")
        try:
            id_val = argv[idx + 1]
        except IndexError:
            print("Invalid value for --id", file=sys.stderr)
            sys.exit(2)

        # Remove the custom option before delegating to single_task_args().
        del argv[idx : idx + 2]
        sys.argv = argv

        _extra_id = id_val
    else:
        _extra_id = ""

    parsed_args = single_task_args()
    setattr(parsed_args, "jobs", _extra_jobs)
    setattr(parsed_args, "id", _extra_id)

    # Make the identifier globally available so that helper functions can
    # forward it to child processes.
    globals()["OUTPUT_ID"] = _extra_id

    # Update the *RESULTS_DIR* to point to the correct output hierarchy.
    if _extra_id:
        globals()["RESULTS_DIR"] = Path(f"outputs/CTF-{_extra_id}/results")

    # Ensure the directory exists early to avoid race conditions later.
    globals()["RESULTS_DIR"].mkdir(parents=True, exist_ok=True)

    # Replace *single_task_args* so that *main()* receives the enriched namespace.
    globals()["single_task_args"] = lambda: parsed_args  # type: ignore[misc]

    main() 