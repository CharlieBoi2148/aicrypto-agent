import json
import os
import yaml
import re
import openai
from src.model import MODEL_MAP
from src.utils import Logger




def load_system_prompt(file_path):
    """Loads the system prompt from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: System prompt file not found at {file_path}")
        return None

def load_questions(file_path):
    """Loads questions from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list): # Check if the top level is a list of questions
                return data
            elif isinstance(data, dict) and "questions" in data and isinstance(data["questions"], list):
                 # Support for a common pattern where questions are under a "questions" key
                return data["questions"]
            else:
                # Try to load if it's a single JSON object per line
                with open(file_path, 'r', encoding='utf-8') as f_again:
                    try:
                        return [json.loads(line) for line in f_again if line.strip()]
                    except json.JSONDecodeError:
                         print(f"Error: {file_path} is not a list of questions nor a JSON object with a 'questions' list, nor JSON Lines format.")
                         return []
    except FileNotFoundError:
        print(f"Error: Data file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return []

def format_user_prompt_for_llm(question_data):
    """Formats the question and choices into a prompt for the LLM."""
    question_text = question_data.get("question", "N/A")
    choices = question_data.get("choice", [])
    
    prompt = f"Question: {question_text}\n"
    prompt += "Choices:\n"
    for i, choice in enumerate(choices):
        prompt += f"{i}: {choice}\n"
    
    if len(question_data.get("answer", [])) == 1:
        prompt += "\nAnalyze this cryptography question and provide your reasoning and answer. It is a multiple-choice question with one correct answer."
    else:
        prompt += "\nAnalyze this cryptography question and provide your reasoning and answers. It is a multiple-choice question with two or more correct answers."
    # print(prompt)
    # exit()
    return prompt

def parse_llm_response(response_str):
    """Extract reasoning text and answer indices from an LLM response.

    Expected canonical format:
        ### Reasoning
        ...
        ### Answer
        0,2  (comma-separated indices)

    However, many models omit the exact *Reasoning* heading.  We therefore fall back to:
        – locating the mandatory `### Answer` section,
        – treating everything before that heading as reasoning (even if it contains other markdown headings),
        – extracting every integer appearing in the answer block as the indices.
    """

    print(response_str)  # keep full response for logging/debugging

    # Locate the `### Answer` section (case-insensitive, tolerant to spacing)
    answer_match = re.search(r"###\s*Answer\s*([\s\S]*?)(?=$)", response_str, re.IGNORECASE)
    if not answer_match:
        print("Invalid format: missing `### Answer` section.")
        return None

    answer_str = answer_match.group(1).strip()

    # Everything before the `### Answer` heading is treated as reasoning
    reasoning_text = response_str[: answer_match.start()].strip()

    # Extract integer indices from the answer string
    index_candidates = re.findall(r"\d+", answer_str)
    if not index_candidates:
        print(f"Could not parse any numeric answer indices from: '{answer_str}'.")
        return None

    try:
        answer_indices = [int(idx) for idx in index_candidates]
    except ValueError:
        print(f"Failed to convert extracted indices to int from: '{answer_str}'.")
        return None

    return {
        "reasoning": reasoning_text,
        "answer_indices": answer_indices,
    }



# --- Main Logic ---

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4.1")
    parser.add_argument("--question", type=str, default="data/mcqs/aicrypto_mcqs.json")
    args = parser.parse_args()
    output_dir = f"outputs/MultipleChoice_EDIT/{args.model}"
    
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "log.txt")
    results_file = os.path.join(output_dir, "results.json")
    
    logger = Logger(f'MultipleChoice_{args.model}', log_file)
    system_prompt = load_system_prompt('src/prompts/MultipleChoice/systemp_prompt')
    
    
    
    model_config = yaml.load(open('config/model.yaml'), Loader=yaml.FullLoader)[args.model]
    model = MODEL_MAP[args.model](model_config, system_prompt)
    
    
    


    # 3. Load questions
    raw_questions_data = load_questions(args.question)

    
    # If data/questions.json contains a single JSON object (not in a list), wrap it
    questions = raw_questions_data if isinstance(raw_questions_data, list) else [raw_questions_data]
    try:
        all_results = json.load(open(results_file))
    except:
        all_results = []
    correct_answers_count = 0
    print(len(all_results))
    start_index = len(all_results)
    # 4. Iterate through questions
    for i, q_data in enumerate(questions[start_index:]):
        i = i + start_index
        print(f"\nProcessing question {i+1}/{len(questions)}: {q_data.get('question', 'N/A')}")
        model.init_prompt()
        user_llm_prompt = format_user_prompt_for_llm(q_data)
        model.add_user_message(user_llm_prompt)
        while True: 
            llm_response = model.get_response()['answer']
            llm_response_json = parse_llm_response(llm_response)
            if isinstance(llm_response_json, dict):
                break
            else:
                raise ValueError('r')
                
        llm_predicted_indices =  llm_response_json.get("answer_indices", "") if llm_response_json else ""
        llm_reasoning = llm_response_json.get("reasoning", "") if llm_response_json else ""
        
        # Correct answer processing: expects "answer": [indices]
        correct_answer_list = q_data.get("answer", [])
        
        is_correct = False
        if llm_predicted_indices is not None and correct_answer_list:
            # Sort both lists to compare content regardless of order
            llm_predicted_sorted = sorted(llm_predicted_indices)
            if isinstance(correct_answer_list, list):
                correct_sorted = sorted(correct_answer_list)
            else:
                correct_sorted = [correct_answer_list]
            
            if llm_predicted_sorted == correct_sorted:
                is_correct = True
                correct_answers_count += 1
            
        result_entry = {
            "question_id": i,
            "question_text": q_data.get("question"),
            "choices": q_data.get("choice"),
            "correct_answer_indices": correct_answer_list,
            "llm_raw_response": llm_response_json,
            "llm_predicted_indices": llm_predicted_indices,
            "llm_reasoning": llm_reasoning,
            "is_correct": is_correct,
            "subject": q_data.get("subject"),
            "source": q_data.get("source")
        }
        all_results.append(result_entry)
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\nDetailed results saved to {results_file}")
        if llm_predicted_indices is None:
            print(f"LLM response could not be parsed. Raw response: {llm_response_json}")
        elif not correct_answer_list:
            print(f"Could not determine correct answer indices for this question.")
        else:
            print(f"LLM predicted indices: {llm_predicted_indices}, Correct indices: {correct_answer_list}, Evaluation: {'Correct' if is_correct else 'Incorrect'}")
            if llm_reasoning:
                print(f"LLM reasoning summary: {llm_reasoning[:100]}...")

    # 5. Save detailed results
   

    # 6. Calculate and print accuracy
    total_questions = len(questions)
    if total_questions > 0:
        accuracy = (correct_answers_count / total_questions) * 100
        print(f"\n--- Summary ---")
        print(f"Total questions processed: {total_questions}")
        print(f"Correctly answered by LLM: {correct_answers_count}")
        print(f"Accuracy: {accuracy:.2f}%")
    else:
        print("\nNo questions were processed.")

if __name__ == "__main__":
    main() 