import subprocess
import time
import sys

# Configuration
MODEL = "gemini-3.1-flash-lite"  # Or your preferred model
ID = "lattice_sequential_v1"
RETRY_DELAY = 65  # Seconds to wait after a rate limit/error
MAX_RETRIES = 5

def run_batch():
    # We call the batch runner with --jobs 1 to ensure one-at-a-time execution
    command = [
        "python", "batch_run_ctf.py",
        "--model", MODEL,
        "--jobs", "1",
        "--id", ID
    ]
    
    print(f"--- Starting Sequential Batch: {ID} ---")
    
    while True:
        try:
            # run() will wait for the process to finish
            result = subprocess.run(command, check=True)
            print("Batch finished successfully!")
            break 
            
        except subprocess.CalledProcessError as e:
            print(f"\n[!] Batch runner exited with an error (likely rate limit).")
            print(f"Waiting {RETRY_DELAY} seconds before retrying...")
            time.sleep(RETRY_DELAY)
            continue
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break

if __name__ == "__main__":
    run_batch()