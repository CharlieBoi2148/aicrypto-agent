# Charlie's Experiment

I wanted to see if reinforcing the response format rules would reduce malformed outputs and let the model spend more iterations actually solving rather than recovering from format errors.

## Tasks tested

The first challenge from each of the first 5 categories:

| Task | Category |
|---|---|
| `01-Classic/01-greek-cipher` | Classic |
| `02-Block/01-integral-communication` | Block |
| `03-Stream-PRNG-Hash/01-babycharge` | Stream/PRNG/Hash |
| `04-RSA/01-blue-hens-2023` | RSA |
| `05-DLP/01-prove-it` | DLP |

## The prompt I added

The core content is the same as the original, but with two structural changes:

1. **Mandatory rules block at the top** — before any description of the agent's role or tools,
   the response format is stated upfront as a requirement the model must read first.
2. **Rules repeated at the bottom** — the same format rules are restated at the end of the prompt
   under "MANDATORY — RESPONSE RULES REPEATED", reinforcing that the three-section structure
   (`### Reasoning` → `### Action` → `### Action Content`) and one-action-per-response constraint are mandatory.

The hypothesis is that sandwiching the prompt content between two copies of the rules makes the
model less likely to drift from the required format mid-run.

## Files I added

- `config/members/charlie.yaml` — member config pointing to `gpt-4.1`
- `config/custom_prompts/charlie_instructional.txt` — my reinforced-format prompt
- `run_member copy.py` — per-member entry point that wires together a member's model, a CTF task, and a prompt variant, then passes them to `TaskRunner` with an isolated timestamped output directory
- `src/agent/task_runner.py` — patched to accept a dynamic system prompt path via `getattr(self.args, "system_prompt", "src/prompts/CTF/system_prompt")` instead of a hardcoded path, allowing `run_member copy.py` to inject custom prompts while keeping the original runners unchanged

## How to run it

From `~/aicrypto-agent` with conda env `crypto`:

```bash
python run_all_prompts.py charlie data/CTF/01-Classic/01-greek-cipher
python run_all_prompts.py charlie data/CTF/02-Block/01-integral-communication
python run_all_prompts.py charlie data/CTF/03-Stream-PRNG-Hash/01-babycharge
python run_all_prompts.py charlie data/CTF/04-RSA/01-blue-hens-2023
python run_all_prompts.py charlie data/CTF/05-DLP/01-prove-it
```

## What I got

gpt-4.1 only solved `01-blue-hens-2023` — all other tasks failed across every prompt variant.

### Time (mm:ss)

| Task | original | prompt-charlie | prompt-juan | prompt-justus | prompt-miguel-i | prompt-miguel-p | prompt-ryan |
|---|---|---|---|---|---|---|---|
| 01-greek-cipher | Failure | Failure | Failure | Failure | Failure | Failure | Failure |
| 01-integral-communication | Failure | Failure | Failure | Failure | Failure | Failure | Failure |
| 01-babycharge | Failure | Failure | Failure | Failure | Failure | Failure | Failure |
| 01-blue-hens-2023 | 0:19 | 0:17 | 0:24 | 0:27 | 0:17 | 0:16 | 0:13 |
| 01-prove-it | Failure | Failure | Failure | Failure | Failure | Failure | Failure |

### Iterations

| Task | original | prompt-charlie | prompt-juan | prompt-justus | prompt-miguel-i | prompt-miguel-p | prompt-ryan |
|---|---|---|---|---|---|---|---|
| 01-greek-cipher | Failure | Failure | Failure | Failure | Failure | Failure | Failure |
| 01-integral-communication | Failure | Failure | Failure | Failure | Failure | Failure | Failure |
| 01-babycharge | Failure | Failure | Failure | Failure | Failure | Failure | Failure |
| 01-blue-hens-2023 | 5 | 6 | 6 | 5 | 7 | 6 | 5 |
| 01-prove-it | Failure | Failure | Failure | Failure | Failure | Failure | Failure |

Logs end up at `outputs/CTF-charlie-<prompt-mode>/.../run/run.log`. To count iterations:

```bash
grep -c "Starting iteration" <path-to-log>
```

## What I think this means

My sandwich method cannot enhance an LLM's multi-step problem-solving ability to the point that it can solve problems it could not solve without prompt engineering. The LLM's performance on certain types of questions lies not in the prompting but in the training of the model itself. Prompting can either hamper or improve the performance that the LLM was originally going to achieve. It would not unlock any new attack paths