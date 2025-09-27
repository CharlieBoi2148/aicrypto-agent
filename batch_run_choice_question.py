#!/usr/bin/env python
"""
Batch runner for run_choice_question.py across all models defined in config/model.yaml.

Usage examples:
    python batch_run_choice_question.py              # Run all models sequentially
    python batch_run_choice_question.py --parallel   # Run all models in parallel (CPU core count processes)
    python batch_run_choice_question.py --models gpt-4.1 o3  # Run a subset of models
    python batch_run_choice_question.py --jobs 4 --parallel  # Parallel with explicit process count

The script spawns a child process for every selected model:
    python run_choice_question.py --model <model_name>

Outputs for each run are already handled by run_choice_question.py, which writes to
`outputs/MultipleChoice/<model_name>/`.
"""

import argparse
import subprocess
import yaml
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

CONFIG_PATH = os.path.join("config", "model.yaml")


def load_model_names() -> List[str]:
    """Return the list of model names (top-level keys) from config/model.yaml."""
    if not os.path.exists(CONFIG_PATH):
        sys.exit(f"Could not find {CONFIG_PATH}. Make sure you are running from the project root.")
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_yaml = yaml.safe_load(f)
        if not isinstance(config_yaml, dict):
            sys.exit(f"Unexpected structure in {CONFIG_PATH}: expected a mapping of model names to configs.")
        return list(config_yaml.keys())
    except yaml.YAMLError as exc:
        sys.exit(f"Failed to parse YAML from {CONFIG_PATH}: {exc}")


def run_single_model(model_name: str, extra_args: List[str] = None) -> int:
    """Run `python run_choice_question.py --model <model_name> [extra_args...]`. Returns exit code."""
    cmd = [sys.executable, "run_choice_question.py", "--model", model_name]
    if extra_args:
        cmd.extend(extra_args)
    # Indicate that this model's run has begun.
    print(f"[BatchRunner] ▶️ Running {model_name} (PID will be shown when spawned)...")

    # Run the child process while capturing its output so it doesn't flood our console.
    completed = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # If the process failed, surface its captured output for debugging.
    if completed.returncode != 0:
        print(f"[BatchRunner] ❌ {model_name} exited with code {completed.returncode}. Output below:\n" + "-" * 60)
        print(completed.stdout)
        print("-" * 60)
    else:
        print(f"[BatchRunner] ✅ {model_name} finished successfully.")
    return completed.returncode


def main():
    parser = argparse.ArgumentParser(description="Batch run run_choice_question.py for multiple models.")
    parser.add_argument(
        "--models",
        nargs="*",
        help="Space-separated list of models to run. Default: all models found in config/model.yaml.",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run models in parallel using multiple processes.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="Number of worker processes when --parallel is set. Default: CPU core count.",
    )
    parser.add_argument(
        "--extra-args",
        nargs=argparse.REMAINDER,
        help="Additional flags to pass through to run_choice_question.py after the --model argument.",
    )

    args = parser.parse_args()

    all_models = load_model_names()
    selected_models = args.models if args.models else all_models

    # Validate model names
    unknown = [m for m in selected_models if m not in all_models]
    if unknown:
        sys.exit(f"Unknown model names: {', '.join(unknown)}. Available models: {', '.join(all_models)}")

    if args.parallel:
        jobs = args.jobs or os.cpu_count() or 1
        print(f"[BatchRunner] Running {len(selected_models)} models in parallel (pool size = {jobs})")
        with ProcessPoolExecutor(max_workers=jobs) as executor:
            futures = {
                executor.submit(run_single_model, model, args.extra_args): model for model in selected_models
            }
            failures = []
            for future in as_completed(futures):
                model = futures[future]
                try:
                    exit_code = future.result()
                    if exit_code != 0:
                        failures.append((model, exit_code))
                except Exception as exc:
                    print(f"[BatchRunner] ❌ Model {model} generated an exception: {exc}")
                    failures.append((model, -1))
        if failures:
            print("[BatchRunner] Completed with errors:")
            for model, code in failures:
                print(f"  - {model}: exit code {code}")
            sys.exit(1)
        else:
            print("[BatchRunner] All models completed successfully.")
    else:
        print(f"[BatchRunner] Running {len(selected_models)} models sequentially")
        for model in selected_models:
            code = run_single_model(model, args.extra_args)
            if code != 0:
                sys.exit(code)


if __name__ == "__main__":
    main() 