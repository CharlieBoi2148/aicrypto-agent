import argparse
from pathlib import Path
import yaml
import json


from src.utils import Logger
from src.model import MODEL_MAP


# ---------------------------------------------------------------------------
# Per-question compliance requirements appended to every problem statement.
# ---------------------------------------------------------------------------

REQUIREMENTS_SUFFIX = (
    "\n\n---\n"
    "PLEASE FOLLOW THESE MANDATORY REQUIREMENTS WHEN FORMULATING YOUR ANSWER:\n"
    "1. Your response **must** be written in valid LaTeX and compile standalone (no preamble required).\n"
    "2. It must contain **exactly two** starred section headings in this order:\n"
    "   \\section*{Reasoning}\n   \\section*{Proof}\n"
    "3. Do **not** add additional sections, preambles, or epilogues.\n"
    "4. Inline mathematics must use `$…$`; display mathematics must use `\\[…\\]`.\n"
    "5. Avoid non-renderable commands such as \\Adv; instead write `\\mathsf{Adv}` etc.\n"
    "6. Escape reserved LaTeX characters when used literally (#, $, %, &, _, {, }, ~, ^, \\).\n"
    "7. The *Proof* section alone will be scored. Do not reference the *Reasoning* section from *Proof*.\n"
    "Failure to comply will result in a zero score.\n"
)


def build_parser() -> argparse.ArgumentParser:
    """Return CLI parser for the proof task runner."""
    parser = argparse.ArgumentParser(description="Run cryptography proof tasks with a specified LLM model.")
    parser.add_argument(
        "--model",
        default="gpt-4.1",
        help="Model key defined in config/model.yaml.",
    )
    parser.add_argument(
        "--exam",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="Exam dataset index (1-3).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output (useful for batch runs)",
    )
    return parser


def extract_proof(text: str) -> str:
    """Extract and return the proof body from the model's response.
    
    The current system prompt requires the model to output exactly two sections:
    ## Reasoning and ## Proof
    
    This function extracts everything after the "## Proof" heading.
    If no "## Proof" section is found, it falls back to legacy formats for compatibility.
    """
    import re

    # 1. Primary: Look for "## Proof" heading (exact format required by system prompt)
    proof_pattern = re.compile(r"^## Proof\s*$", re.MULTILINE)
    match = proof_pattern.search(text)
    if match:
        # Extract everything after the "## Proof" heading
        proof_content = text[match.end():].strip()
        return proof_content

    # 2. Fallback: LaTeX proof environment (for backward compatibility)
    env_start = re.search(r"\\begin\{proof\}", text, flags=re.IGNORECASE)
    if env_start:
        env_end = re.search(r"\\end\{proof\}", text[env_start.end():], flags=re.IGNORECASE)
        if env_end:
            return text[env_start.end(): env_start.end() + env_end.start()].strip()
        # If no closing tag, return everything after the opening tag.
        return text[env_start.end():].strip()

    # 3. Fallback: Other markdown proof headings (e.g., '# Proof', '### Proof')
    md_pattern = re.compile(r"^#{1,6}\s+[Pp]roof\s*$", re.MULTILINE)
    match = md_pattern.search(text)
    if match:
        return text[match.end():].strip()

    # 4. Fallback: LaTeX heading \section*{Proof}
    latex_heading = re.compile(r"\\section\*?\{[Pp]roof\}")
    match = latex_heading.search(text)
    if match:
        return text[match.end():].strip()

    # Default: return unchanged if no recognized format is found
    return text.strip()


def extract_reasoning(text: str) -> str:
    """Extract the *Reasoning* section from the model's response.

    The prompt enforces a structure with exactly two top-level headings:
    ## Reasoning
    ## Proof

    We capture the content located strictly between these two markers.
    If either marker is missing, we fall back gracefully and return an
    empty string (so downstream code remains robust).
    """
    import re

    reasoning_pattern = re.compile(r"^## Reasoning\s*$", re.MULTILINE)
    proof_pattern = re.compile(r"^## Proof\s*$", re.MULTILINE)

    r_match = reasoning_pattern.search(text)
    if not r_match:
        # Support LaTeX starred section headings (new default)
        latex_reasoning_pattern = re.compile(r"\\section\*?\{[Rr]easoning\}")
        r_match = latex_reasoning_pattern.search(text)

    if not r_match:
        return ""  # no reasoning section found

    # If a proof heading exists and comes after reasoning, take text in-between
    p_match = proof_pattern.search(text, r_match.end()) if r_match else None
    if r_match and not p_match:
        # try LaTeX proof heading
        latex_proof_pattern = re.compile(r"\\section\*?\{[Pp]roof\}")
        p_match = latex_proof_pattern.search(text, r_match.end())

    if p_match:
        return text[r_match.end(): p_match.start()].strip()

    # Otherwise, return everything after the reasoning heading
    return text[r_match.end():].strip()


def main() -> None:
    args = build_parser().parse_args()

    # Suppress console output if --quiet is enabled
    if getattr(args, "quiet", False):
        import os, sys
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    exam_dir = Path(f"data/Proof/exam{args.exam}")
    if not exam_dir.exists():
        raise FileNotFoundError(f"Exam directory not found: {exam_dir}")

    if (exam_dir / 'Note.md').exists():
        note = (exam_dir / 'Note.md').read_text()
    else:
        note = ""
    proof_out_dir = Path(f"outputs/proof/exam{args.exam}/proof")
    reasoning_out_dir = Path(f"outputs/proof/exam{args.exam}/reasoning")
    log_out_dir = Path(f"outputs/proof/exam{args.exam}/log")
    proof_out_dir.mkdir(parents=True, exist_ok=True)
    reasoning_out_dir.mkdir(parents=True, exist_ok=True)
    log_out_dir.mkdir(parents=True, exist_ok=True)
    logger = Logger(f"{args.model}_exam{args.exam}_proof", log_out_dir / f"{args.model}_exam{args.exam}_proof_log.txt")

    with Path("config/model.yaml").open("r") as f:
        model_cfg = yaml.safe_load(f)[args.model]

    # Load system prompt and inject exam-specific macros / pre-notes if placeholders are present.
    prompt_template = Path("src/prompts/Proof/system_prompt.md").read_text()

    
    system_prompt = prompt_template.format(note)
    logger.log(system_prompt)
    

    model = MODEL_MAP[args.model](model_cfg, system_prompt)

    proofs = []
    reasonings = []
    record = []
    problem_paths = sorted(exam_dir.glob("problem*.tex"))
    for path in problem_paths:
        question = path.read_text()
        prompt_text = question + REQUIREMENTS_SUFFIX
        logger.log('==='*30)
        logger.log(prompt_text)
        logger.log('---'*30)
        model.add_user_message(prompt_text)
        i= 0
        while True:
            try:
                response = model.get_response()
                if response:
                    break
                
            except Exception as e:
                i += 1
                if i>3:
                    raise e 
                continue

        
        
        answer = response['answer']
        logger.log(answer)
        model.add_assistant_message(answer)

        # Separate reasoning and proof for dedicated storage
        proof_body = extract_proof(answer)
        reasoning_body = extract_reasoning(answer)

        proofs.append(proof_body)
        reasonings.append(reasoning_body)

        record.append({
            "id": len(record) + 1,
            "thinking": response['thinking'],
            "reasoning": reasoning_body,
            "proof": proof_body
        })

    # -------------------------------------------------------------------
    # Persist results: save *Proof* and *Reasoning* in separate files.
    # -------------------------------------------------------------------

    proof_file = proof_out_dir / f"{args.model}_proof_results.tex"
    reasoning_file = reasoning_out_dir / f"{args.model}_reasoning_results.tex"
    proof_rlt = ""
    with open('src/prompts/Proof/proof_template.tex', 'r', encoding='utf-8') as f:
        proof_template = f.read()
    with proof_file.open("w") as f:
        for idx, proof in enumerate(proofs, 1):
            proof_rlt+=(f"\section{{Problem{idx}}}\n{proof}\n\n")
        f.write(proof_template + proof_rlt +'\n\n\\end{document}')
    with reasoning_file.open("w") as f:
        for idx, reasoning in enumerate(reasonings, 1):
            f.write(f"## Problem{idx}\n{reasoning}\n\n")

    record_file = log_out_dir / f"{args.model}_record.json"
    json.dump(record, open(record_file, 'w'), indent=4)


if __name__ == "__main__":
    main()

