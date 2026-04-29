import subprocess
import sys
import os
import signal
import time
from datetime import datetime

def run_benchmarks(member, task):
    prompt_modes = [
        "original", "prompt-charlie", "prompt-juan", 
        "prompt-justus", "prompt-miguel-i", "prompt-miguel-p", "prompt-ryan"
    ]
    TIMEOUT_SECONDS = 1200 

    for mode in prompt_modes:
        print(f"\n{'='*70}")
        print(f"PROMPT: {mode} | START: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")

        cmd = ["python", "run_member copy.py", "--member", member, "--task", task, "--prompt-mode", mode]

        # Use start_new_session to create a process group for this run
        proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

        try:
            # Wait for the process to finish or timeout
            proc.wait(timeout=TIMEOUT_SECONDS)
            print(f"[SUCCESS] Completed {mode}")
            
        except subprocess.TimeoutExpired:
            print(f"\n[!] TIMEOUT: Killing entire process group for '{mode}'...")
            # Kill the entire process group (pgid) so no ghost processes remain
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            time.sleep(2) # Give it a moment to release ports/files
            print(f"[!] Cleaned up {mode}")
            
        except Exception as e:
            print(f"\n[!] ERROR: {e}")
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

if __name__ == "__main__":
    MEMBER_NAME = "miguel"
    if len(sys.argv) < 2:
        print("Usage: python run_all_prompts.py <task_path>")
        sys.exit(1)

    TASK_PATH = sys.argv[1]
    if not os.path.exists(TASK_PATH):
        print(f"Error: Path '{TASK_PATH}' not found.")
        sys.exit(1)
        
    run_benchmarks(MEMBER_NAME, TASK_PATH)