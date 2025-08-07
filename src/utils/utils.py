import yaml
import os
import re
import json

def load_task_file(task_file: str) -> dict:
    """
    Load task configuration from a YAML file.
    
    Args:
        task_file: Path to the task YAML file
        
    Returns:
        dict: Task configuration data
        
    Raises:
        Exception: If file cannot be loaded or parsed
    """
    try:
        with open(task_file, 'r') as f:
            task_data = yaml.safe_load(f)
        return task_data
    except Exception as e:
        raise Exception(f"Error loading task file: {e}")
    
    
def set_up_write_path(output_dir: str):
    """
    Set up the write path for the task.
    """
    
    os.makedirs(output_dir, exist_ok=True)
    run_env_id = len([f for f in os.listdir(output_dir) if f.startswith("run_env")])
    write_path = os.path.join(output_dir, "run_env_" + str(run_env_id), 'write')
    
    return write_path


def detect_file_type(filename: str, content: str) -> str:
    """
    Detect file type based on extension and content.
    
    Args:
        filename: Name of the file
        content: File content
        
    Returns:
        str: Detected file type ('python', 'sage', 'output', 'json', 'yaml', 'text')
    """
    filename_lower = filename.lower()
    
    # Check by extension first
    if filename_lower.endswith('.py'):
        return 'python'
    elif filename_lower.endswith('.sage'):
        return 'sage'
    elif filename_lower.endswith(('.json',)):
        return 'json'
    elif filename_lower.endswith(('.yaml', '.yml')):
        return 'yaml'
    elif filename_lower.startswith('output') or filename_lower.endswith('.out'):
        return 'output'
    
    # Check by content patterns
    content_sample = content[:500]
    if re.search(r'^\s*(def|class|import|from)\s+', content_sample, re.MULTILINE):
        return 'python'
    elif re.search(r'(Integer\(|GF\(|EllipticCurve|load\()', content_sample):
        return 'sage'
    elif content_sample.strip().startswith(('{', '[')):
        return 'json'
    
    return 'text'


def smart_number_abbreviation(text: str, preserve_digits: int = 6) -> str:
    """
    Intelligently abbreviate long numbers while preserving structure.
    
    Args:
        text: Input text containing numbers
        preserve_digits: Number of digits to preserve from start and end
        
    Returns:
        str: Text with abbreviated numbers
    """
    def abbreviate_number(match):
        num_str = match.group()
        if len(num_str) <= 10:  # Don't abbreviate short numbers
            return num_str
        
        if len(num_str) <= preserve_digits * 2:
            return num_str
        
        start = num_str[:preserve_digits]
        end = num_str[-preserve_digits:]
        middle_length = len(num_str) - preserve_digits * 2
        
        return f"{start}...{end} ({len(num_str)} digits)"

    # Match decimal numbers (at least 11 digits)
    decimal_pattern = r'\b\d{11,}\b'
    # Match hexadecimal numbers (at least 11 hex chars)
    hex_pattern = r'\b[0-9a-fA-F]{11,}\b'
    
    text = re.sub(decimal_pattern, abbreviate_number, text)
    text = re.sub(hex_pattern, abbreviate_number, text)
    
    return text


def abbreviate_data_structures(text: str, max_items: int = 5) -> str:
    """
    Abbreviate large data structures (lists, tuples, sets) while preserving structure.
    
    Args:
        text: Input text
        max_items: Maximum number of items to show in each structure
        
    Returns:
        str: Text with abbreviated data structures
    """
    def abbreviate_list_like(match):
        full_match = match.group()
        bracket_open = full_match[0]
        bracket_close = ']' if bracket_open == '[' else ')'
        
        # Extract content between brackets
        content = full_match[1:-1]
        
        # Split by commas but be careful about nested structures
        items = []
        current_item = ""
        bracket_count = 0
        paren_count = 0
        
        for char in content:
            if char in '[{(':
                bracket_count += 1
            elif char in ']})':
                bracket_count -= 1
            elif char == ',' and bracket_count == 0:
                items.append(current_item.strip())
                current_item = ""
                continue
            current_item += char
        
        if current_item.strip():
            items.append(current_item.strip())
        
        if len(items) <= max_items:
            return full_match
        
        # Keep first few and last few items
        keep_start = max_items // 2
        keep_end = max_items - keep_start
        
        abbreviated_items = items[:keep_start] + [f"... ({len(items) - max_items} more items) ..."] + items[-keep_end:]
        
        return bracket_open + ', '.join(abbreviated_items) + bracket_close
    
    # Match lists and tuples with many items
    list_pattern = r'\[[^\[\]]{100,}\]'
    tuple_pattern = r'\([^()]{100,}\)'
    
    text = re.sub(list_pattern, abbreviate_list_like, text)
    text = re.sub(tuple_pattern, abbreviate_list_like, text)
    
    return text


def preserve_code_structure(text: str, file_type: str) -> str:
    """
    Preserve important code structure elements.
    
    Args:
        text: Input text
        file_type: Type of file ('python', 'sage', etc.)
        
    Returns:
        str: Text with preserved structure
    """
    if file_type not in ['python', 'sage']:
        return text
    
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Always preserve: function definitions, class definitions, imports, comments
        if (stripped.startswith(('def ', 'class ', 'import ', 'from ', '#')) or
            stripped.startswith(('load(', 'save(')) or  # Sage specific
            '=' in stripped and len(stripped.split('=')[0].strip()) < 50):  # Variable assignments with short names
            
            processed_lines.append(line)
        
        # For very long lines, check if they're important
        elif len(line) > 200:
            # If it's a variable assignment, preserve the structure
            if '=' in stripped:
                var_name = stripped.split('=')[0].strip()
                if len(var_name) < 50:  # Reasonable variable name length
                    # Preserve variable name and abbreviate value
                    value_part = '='.join(stripped.split('=')[1:]).strip()
                    abbreviated_value = smart_number_abbreviation(value_part)
                    abbreviated_value = abbreviate_data_structures(abbreviated_value)
                    processed_lines.append(f"{' ' * (len(line) - len(line.lstrip()))}{var_name} = {abbreviated_value}")
                else:
                    processed_lines.append(line[:100] + "... (truncated)")
            else:
                processed_lines.append(line[:100] + "... (truncated)")
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def smart_content_filter(content: str, filename: str = "", max_length: int = 8192) -> str:
    """
    Intelligently filter content based on file type and content structure.
    
    Args:
        content: File content to filter
        filename: Name of the file (for type detection)
        max_length: Maximum allowed length after filtering
        
    Returns:
        str: Filtered content
    """
    if len(content) <= max_length // 2:  # If content is reasonably short, don't filter
        return content
    
    # Detect file type
    file_type = detect_file_type(filename, content)
    
    # Apply appropriate filtering strategy
    if file_type in ['python', 'sage']:
        # For code files, preserve structure and abbreviate data
        filtered = preserve_code_structure(content, file_type)
        filtered = smart_number_abbreviation(filtered)
        filtered = abbreviate_data_structures(filtered)
        
    elif file_type == 'json':
        try:
            # Try to parse and pretty-print JSON with abbreviation
            data = json.loads(content)
            pretty_json = json.dumps(data, indent=2)
            filtered = smart_number_abbreviation(pretty_json)
            filtered = abbreviate_data_structures(filtered)
        except:
            # If JSON parsing fails, treat as text
            filtered = smart_number_abbreviation(content)
            filtered = abbreviate_data_structures(filtered)
            
    elif file_type == 'output':
        # For output files, preserve key-value pairs and abbreviate values
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            if '=' in line and len(line.split('=')[0].strip()) < 100:
                # Looks like key=value format
                key_part = line.split('=')[0]
                value_part = '='.join(line.split('=')[1:])
                abbreviated_value = smart_number_abbreviation(value_part)
                abbreviated_value = abbreviate_data_structures(abbreviated_value)
                processed_lines.append(key_part + '=' + abbreviated_value)
            else:
                # Regular line
                abbreviated_line = smart_number_abbreviation(line)
                abbreviated_line = abbreviate_data_structures(abbreviated_line)
                processed_lines.append(abbreviated_line)
        
        filtered = '\n'.join(processed_lines)
        
    else:
        # For other text files, apply basic filtering
        filtered = smart_number_abbreviation(content)
        filtered = abbreviate_data_structures(filtered)
    
    # Final length check and truncation if still too long
    if len(filtered) > max_length:
        # Smart truncation: preserve beginning and end
        keep_start = max_length * 2 // 3
        keep_end = max_length - keep_start - 50  # Leave space for truncation message
        
        truncation_msg = f"\n\n... [TRUNCATED: {len(filtered) - max_length} characters omitted] ...\n\n"
        filtered = filtered[:keep_start] + truncation_msg + filtered[-keep_end:]
    
    return filtered


def filter_file_content(content: str, filename: str, max_length: int = 16384) -> str:
    """
    Filter file content with filename context for optimal CTF problem solving.
    
    Args:
        content: File content to filter
        filename: Name of the file for context-aware filtering
        max_length: Maximum allowed length (higher for code files)
        
    Returns:
        str: Intelligently filtered content preserving essential information
    """
    # Use higher limits for code files as they're critical for problem solving
    file_type = detect_file_type(filename, content)
    if file_type in ['python', 'sage']:
        max_length = max(max_length, 16384)  # Ensure sufficient space for code
    elif file_type == 'output':
        max_length = max(max_length, 12288)  # Output files often contain important data
    
    return smart_content_filter(content, filename, max_length)


def truncate_long_string(text: str, context: str = "") -> str:
    """
    Enhanced string truncation using smart content filtering.
    
    Args:
        text: Input string to be filtered/truncated
        context: Additional context (like command being executed) for better filtering
        
    Returns:
        str: Filtered and truncated string
    """
    # Check if this looks like file content based on context
    filename = ""
    if context:
        # Extract filename from common command patterns
        if 'cat ' in context or 'head ' in context or 'tail ' in context:
            # Try to extract filename from command
            parts = context.split()
            for part in parts:
                if not part.startswith('-') and part not in ['cat', 'head', 'tail']:
                    filename = part
                    break
    
    # Heuristic: if very long numbers (typical in crypto challenges) or big
    # numeric arrays are present we allow a much larger budget.  We still rely
    # on ``smart_content_filter`` (which already abbreviates numbers and
    # structures) but avoid an overly aggressive 2 KB cap that previously
    # stripped crucial information such as RSA moduli or ciphertext blocks.

    contains_long_nums = has_long_numbers(text, length_threshold=20)

    # Detect large numeric list/array patterns (e.g. ct = [1, 2, 3, ...])
    import re  # Local import to avoid polluting global namespace unintentionally
    large_list_pattern = r"\[[\d,\s]{200,}\]"
    contains_large_list = bool(re.search(large_list_pattern, text))

    # Dynamically set the maximum length.
    max_len = 8192 if (contains_long_nums or contains_large_list) else 2048

    return smart_content_filter(text, filename, max_length=max_len)


def has_long_numbers(text: str, length_threshold: int = 15) -> bool:
    """
    Check if a string contains any numbers with length greater than the threshold.
    
    Args:
        text: Input string to check for long numbers
        length_threshold: Minimum length to consider a number as "long" (default: 15)
        
    Returns:
        bool: True if the string contains numbers longer than the threshold, False otherwise
    """
    # Pattern to find sequences of digits
    pattern = r'\d+'
    matches = re.findall(pattern, text)
    
    # Check if any match exceeds the threshold
    for match in matches:
        if len(match) > length_threshold:
            return True
    
    return False

def mask_braced_string(s: str) -> str:
    match = re.fullmatch(r'(.*?)\{[^{}]*\}', s)
    if match:
        prefix = match.group(1)
        return f"{prefix}{{***}}"
    else:
        return '***'
    
def create_task_prompt_from_task(task_data, port=None):
    """
    Create a task description prompt from the task data.
    
    Args:
        task_data: The task data loaded from the task.json file.
        port: Optional port number for dynamic challenges.
        
    Returns:
        A formatted task prompt string.
    """
    # Determine challenge type and load appropriate prompt
    if port:
        description_info = open("src/prompts/CTF/dynamic", "r").read().format(port, port)
    else:
        description_info = open("src/prompts/CTF/static", "r").read()
    
    # Check for helper files and determine type
    help_info = ""
    helper_path = task_data["write_path"]
    
    if os.path.exists(helper_path):
        files_in_path = os.listdir(helper_path)
        
        # Check for helper.py (Python helper)
        if 'helper.py' in files_in_path:
            help_info = open("src/prompts/CTF/helper_info_py", "r").read()
        # Check for helper.sage (SageMath helper)  
        elif 'helper.sage' in files_in_path:
            help_info = open("src/prompts/CTF/helper_info_sage", "r").read()
        # No helper file found
        else:
            help_info = ""
    
    # Format the main task prompt with description and helper info
    task_prompt = open("src/prompts/CTF/task_prompt", "r").read().format(description_info, help_info, mask_braced_string(task_data['flag']))

    return task_prompt


def get_model_config(model_name: str) -> dict:
    model_config = yaml.safe_load(open("config/model.yaml", "r"))
    return model_config[model_name]