# AICrypto — Group 11 Fork

[![Paper](https://img.shields.io/badge/Paper-arXiv-red)](https://arxiv.org/abs/2507.09580)
[![Original Repo](https://img.shields.io/badge/Original-Repo-gray)](https://github.com/wangyu-ovo/aicrypto-agent)
[![Dataset](https://img.shields.io/badge/Dataset-HuggingFace-yellow)](https://huggingface.co/datasets/yuuwwang/aicrypto)

Fork of the [AICrypto benchmark](https://github.com/wangyu-ovo/aicrypto-agent) for a Systems Security course group project. We reproduced the paper's results and extended the benchmark with a per-member prompt injection system.

---

## Setup

> All steps must be run on Linux (Ubuntu 20.04 recommended).
>
> **Important:** These setup steps are for Linux (Ubuntu 20.04) running on an x86_64 machine. The conda environment will not work on macOS (including Apple Silicon or Intel Macs) due to Linux-only dependencies. Use the VirtualBox VM provided in class.

### Prerequisites

- Python 3.10.15
- SageMath 10.5
- yafu 1.34.5
- VirtualBox VM configured as per the class setup (≥ 5000 MB base memory recommended for some operations)

### Installation

1. **Install Git and clone:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install git -y
   cd ~/Documents
   git clone https://github.com/CharlieBoi2148/aicrypto-agent.git
   cd aicrypto-agent
   git checkout development
   ```

2. **Install Miniconda:**
   ```bash
   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
   bash Miniconda3-latest-Linux-x86_64.sh
   source ~/.bashrc
   ```
   During installation: accept the license, confirm the default install location, and type `yes` to initialize Miniconda.

3. **Create the conda environment:**

   > The original `environment.yml` has a Cascadelake CPU constraint that fails on VirtualBox. Use the fix below — do **not** run `conda env create -f environment.yml` directly.

   ```bash
   grep -v "_x86_64-microarch-level" environment.yml > environment_fixed.yml
   conda env create -f environment_fixed.yml --solver=classic
   ```
   This step takes 20–40 minutes. Once complete:
   ```bash
   conda activate crypto
   ```

4. **Install SageMath dependencies:**
   ```bash
   sage -pip install -r sage-requirements.txt
   ```

5. **Install flatter:**
   ```bash
   sudo apt install libgmp-dev libmpfr-dev fplll-tools libfplll-dev libeigen3-dev libopenblas-dev cmake -y
   cd ~/Documents
   git clone https://github.com/keeganryan/flatter.git
   cd flatter && mkdir build && cd build
   cmake .. && make && sudo make install && sudo ldconfig
   cd ~/Documents/aicrypto-agent
   ```

6. **Install yafu:**
   ```bash
   sudo apt install libgmp-dev libecm-dev -y
   cd ~/Documents
   git clone https://github.com/bbuhrow/yafu.git
   cd yafu
   make -f Makefile.gcc yafu
   sudo cp ~/Documents/yafu/yafu /usr/local/bin/
   cd ~/Documents/aicrypto-agent
   ```

7. **Fix proof data path:**
   ```bash
   ln -s proof_problems data/Proof
   ```

8. **Configure API keys:**
   ```bash
   nano .env
   ```
   ```
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```
   > Do not commit this file to GitHub.

9. **Install additional dependencies:**
   ```bash
   pip install pyyaml
   ```

---

## Usage

### Run Single CTF Challenge

```shell
python run_single_ctf_task.py --task-path data/CTF/04-RSA/01-blue-hens-2023 --model gpt-4.1
```

Results are saved to `./outputs/CTF-0/04-RSA/01-blue-hens-2023/gpt-4.1/run`.

### Run CTF Challenges in Parallel for Evaluation

```shell
python run_ctf_parallel.py --jobs 4 --id 0
```

Uses 4 processes to run tasks with run ID 0. Results saved to `./outputs/CTF-0`. Models are specified in `config/model.yaml`.

### Run Single MCQ Evaluation

```shell
python run_choice_question.py --model gpt-4.1
```

Results are saved to `./outputs/MultipleChoice/<model_name>/`.

### Run MCQ Evaluation in Parallel

```shell
python batch_run_choice_question.py --parallel --jobs 4
# Optionally select specific models:
python batch_run_choice_question.py --parallel --jobs 4 --models gpt-4.1 o3
```

### Run Single Proof Task

```shell
python run_proof_task.py --exam 1 --model gpt-4.1
```

Outputs:
- Proofs: `./outputs/proof/exam1/proof/gpt-4.1_proof_results.tex`
- Reasoning: `./outputs/proof/exam1/reasoning/gpt-4.1_reasoning_results.tex`
- Logs: `./outputs/proof/exam1/log/`

### Run Proof Tasks in Parallel

```shell
python batch_run_proof_tasks.py --exam-values 1 2 3 --jobs 4
```

---

## Our Extension — Prompt Injection

We added `run_member.py`, a new entry point that lets each team member swap the CTF agent's system prompt with a custom technique. Each member has a config in `config/members/<name>.yaml` that declares their model and prompt files.

```bash
python run_member.py --member charlie --task data/CTF/04-RSA/01-blue-hens-2023 --prompt-mode original
python run_member.py --member charlie --task data/CTF/04-RSA/01-blue-hens-2023 --prompt-mode instructional
python run_member.py --member charlie --task data/CTF/04-RSA/01-blue-hens-2023 --prompt-mode poisoned
```

`--prompt-mode` accepts: `original | instructional | poisoned`. Model is pulled from `config/members/<member>.yaml`, not from the CLI, so each member's results use their declared model consistently.

To add a new member, copy `config/members/charlie.yaml`, rename it to `<name>.yaml`, and update the fields.

---

## Configuration

- **Models**: Configure available models in `config/model.yaml`
- **Custom Models**: Add custom model implementations in `src/model/`
- **API Keys**: Set up your API keys in the `.env` file


## What Works / What Doesn't

**Works:**
- MCQ benchmark (all 135 questions)
- CTF challenges in the RSA category
- Proof generation (exam 1, all 6 problems)
- Per-member prompt injection via `run_member.py`

**Does not work:**
- Proof grading — requires `gpt-5.1` and `gemini-3-pro-preview` as graders; these are not included in the repository. Only proof generation can be reproduced.
- Full LLM Compatibility with custom prompts — For testing purposes, custom prompts are run through individual member files where each member is associated with a particular model. As a result, only 5 LLMs (1 per associated member) can be tested with custom prompts. However, model values inside each member file can be updated to work with any models in config > model.yaml or a new member can be created to handle a new model inside config > model.yaml with ease.

---

## Scholarly References

**Prior/Foundational Work:**

[FROM MIGUEL]

**Contemporary Work:**

*Recent advancements (late 2025–2026) showcasing the shift toward autonomous agents, reinforcement learning, and real-world vulnerability discovery.*

* **Muzsai, L., Imolai, D., & Lukács, A. (2025).** *Improving LLM Agents with Reinforcement Learning on Cryptographic CTF Challenges.* Eötvös Loránd University.
    * **Contribution:** Introduces the **RANDOM-CRYPTO** dataset and utilizes **Group Relative Policy Optimization (GRPO)** to demonstrate that procedural reasoning for CTFs can be significantly improved through targeted reinforcement learning.
* **Cui, Y., et al. (2025).** *FREE-MAD: Consensus-Free Multi-Agent Debate.* arXiv:2509.11035v1.
    * **Contribution:** Proposes a framework to mitigate the inherent **conformity** of LLMs in multi-agent environments. By evaluating the entire debate trajectory rather than a simple final consensus, the system achieves higher reasoning accuracy.
* **Anthropic PBC (2026).** *Partnering with Mozilla to Improve Firefox’s Security.*
    * **Contribution:** An industry case study documenting **Claude Opus 4.6** identifying 22 vulnerabilities in the Firefox codebase, demonstrating the transition of LLMs toward real-world vulnerability discovery at scale.
* **Mastrodonato, M. (2026).** *How Good Are Today's AIs at Cryptography and Mathematics?* Medium.
    * **Contribution:** A practitioner’s perspective on the "zero-tolerance" nature of cryptography. It argues that the binary success/failure state of cryptographic tasks provides a more rigorous measure of an LLM's true reasoning depth than general coding tasks.

---
