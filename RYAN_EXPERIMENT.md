# Ryan's Experiment

For the Student Researcher part of the project I wanted to see if I could get
the LLM to solve CTF problems faster by changing the system prompt. Our paper
said LLMs struggle with multi-step reasoning, and our proposal mentioned that
CTF challenges are basically "a breach in confidentiality" — so I figured if
I make the model walk through a Confidentiality Analysis before each action,
maybe it'll be more focused and finish in fewer iterations.

## Task tested

`data/CTF/04-RSA/01-blue-hens-2023` — "RSA School 3rd Grade", a static RSA
common-modulus challenge.

## The prompt I added

The Analysis I added has 4 questions taken from the CIA triad lecture:
1. What needs to be protected?
2. How much protection is needed?
3. For how long is protection needed?
4. Which threat applies (Exposure / Interception / Inference / Intrusion)?

The model has to answer all 4 in a "Step 0" section before picking any
Action. Everything else in the prompt is identical to the original.

I also wanted to see if it mattered whether the model was using extended
thinking or not, so I tested both `claude-opus-4-7` and the thinking version.

## Files I added

- `config/members/ryan.yaml` — non-thinking model config
- `config/members/ryan-thinking.yaml` — thinking model config
- `config/custom_prompts/ryan_instructional.txt` — my CIA prompt (used by
  both yamls — same prompt for both model modes)

## How to run it

From `~/aicrypto-agent` with conda env `crypto`:

```bash
# === non-thinking model (claude-opus-4-7) ===
# baseline (original prompt)
python run_member.py --member ryan --task data/CTF/04-RSA/01-blue-hens-2023 --prompt-mode original
# my CIA prompt
python run_member.py --member ryan --task data/CTF/04-RSA/01-blue-hens-2023 --prompt-mode instructional

# === thinking model (claude-opus-4-7-thinking) ===
# baseline (original prompt)
python run_member.py --member ryan-thinking --task data/CTF/04-RSA/01-blue-hens-2023 --prompt-mode original
# my CIA prompt
python run_member.py --member ryan-thinking --task data/CTF/04-RSA/01-blue-hens-2023 --prompt-mode instructional
```

## What I got

|  | original prompt | my CIA prompt |
|---|---|---|
| non-thinking | 5 iters / 21s | 6 iters / 29s |
| thinking | 10 iters / 48s | **4 iters / 16s** |

Logs end up at `outputs/CTF-ryan/.../run/run.log` (non-thinking) and
`outputs/CTF-ryan-thinking/.../run/run.log` (thinking). To count iterations:

```bash
grep -c "^Starting iteration" <path-to-log>
```

## What I think this means

My prompt made things slightly worse for the non-thinking model (5 → 6) but
cut the thinking model's iterations in half (10 → 4) and made it 3x faster.
So the CIA scaffolding only helps if the model is already doing internal
reasoning — without that, the extra structure just gets in the way.
