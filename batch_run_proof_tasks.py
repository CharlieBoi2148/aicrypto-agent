#!/usr/bin/env python3
"""
Batch runner for proof tasks with multi-threading support.
Runs run_proof_task.py with all combinations of specified exam values and available models.
"""

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import sys
from typing import List, Tuple
import argparse

# Import MODEL_MAP to get all available models
sys.path.append(str(Path(__file__).parent))
from src.model import MODEL_MAP


class TaskRunner:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results = []
        self.lock = threading.Lock()
        
    def run_single_task(self, exam: int, model: str) -> Tuple[int, str, bool, str]:
        """Run a single proof task and return the result."""
        cmd = ["python", "run_proof_task.py", "--exam", str(exam), "--model", model]
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            if success:
                message = f"✅ Exam {exam} + {model}: Completed successfully ({duration:.1f}s)"
            else:
                message = f"❌ Exam {exam} + {model}: Failed ({duration:.1f}s)\nError: {result.stderr[:200]}"
                
            with self.lock:
                print(message)
                
            return exam, model, success, message
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            message = f"⏰ Exam {exam} + {model}: Timeout after {duration:.1f}s"
            with self.lock:
                print(message)
            return exam, model, False, message
            
        except Exception as e:
            duration = time.time() - start_time
            message = f"💥 Exam {exam} + {model}: Exception ({duration:.1f}s): {str(e)}"
            with self.lock:
                print(message)
            return exam, model, False, message

    def run_all_tasks(self, exam_values: List[int], model_names: List[str]) -> None:
        """Run all combinations of exam values and models."""
        # Create all combinations
        tasks = [(exam, model) for exam in exam_values for model in model_names]
        
        print(f"🚀 Starting batch execution with {len(tasks)} tasks using {self.max_workers} threads")
        print(f"📊 Exam values: {exam_values}")
        print(f"🤖 Models: {len(model_names)} models")
        print("=" * 80)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self.run_single_task, exam, model): (exam, model)
                for exam, model in tasks
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_task):
                exam, model, success, message = future.result()
                completed += 1
                
                self.results.append({
                    'exam': exam,
                    'model': model,
                    'success': success,
                    'message': message
                })
                
                # Progress update
                progress = (completed / len(tasks)) * 100
                print(f"📈 Progress: {completed}/{len(tasks)} ({progress:.1f}%)")
        
        total_time = time.time() - start_time
        self.print_summary(total_time)
    
    def print_summary(self, total_time: float) -> None:
        """Print execution summary."""
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful
        
        print("\n" + "=" * 80)
        print("📋 EXECUTION SUMMARY")
        print("=" * 80)
        print(f"⏱️  Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success rate: {(successful/len(self.results)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed tasks:")
            for result in self.results:
                if not result['success']:
                    print(f"   • Exam {result['exam']} + {result['model']}")
        
        print("\n🎉 Batch execution completed!")


def main():
    parser = argparse.ArgumentParser(description="Batch runner for proof tasks")
    parser.add_argument(
        "--exam-values",
        nargs="+",
        type=int,
        default=[2, 3],
        help="Exam values to run (default: 2 3)"
    )
    parser.add_argument(
        "--models",
        nargs="*",
        help="Specific models to run (default: all models from MODEL_MAP)"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="Maximum number of concurrent threads (default: 4)"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List all available models and exit"
    )
    
    args = parser.parse_args()
    
    # List models if requested
    if args.list_models:
        print("Available models:")
        for model in sorted(MODEL_MAP.keys()):
            print(f"  • {model}")
        return
    
    # Determine which models to use
    if args.models:
        model_names = args.models
        # Validate model names
        invalid_models = [m for m in model_names if m not in MODEL_MAP]
        if invalid_models:
            print(f"❌ Invalid model names: {invalid_models}")
            print("Use --list-models to see all available models")
            return
    else:
        model_names = list(MODEL_MAP.keys())
    
    # Validate exam values
    valid_exams = [1, 2, 3]
    invalid_exams = [e for e in args.exam_values if e not in valid_exams]
    if invalid_exams:
        print(f"❌ Invalid exam values: {invalid_exams}")
        print(f"Valid exam values: {valid_exams}")
        return
    
    # Check if run_proof_task.py exists
    if not Path("run_proof_task.py").exists():
        print("❌ run_proof_task.py not found in current directory")
        return
    
    print(f"🎯 Selected exam values: {args.exam_values}")
    print(f"🤖 Selected models ({len(model_names)}): {model_names}")
    print(f"🧵 Max workers: {args.jobs}")
    
    # Confirm before starting
    total_tasks = len(args.exam_values) * len(model_names)
    response = input(f"\n🚀 Ready to run {total_tasks} tasks. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Cancelled by user")
        return
    
    # Run the batch
    runner = TaskRunner(max_workers=args.jobs)
    runner.run_all_tasks(args.exam_values, model_names)


if __name__ == "__main__":
    main() 