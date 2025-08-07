"""LLM-powered helper used by TaskRunner to solve CTF challenges."""

from __future__ import annotations

import os
import subprocess
import signal
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List, Callable
import re
import time

from src.model import MODEL_MAP

_PROHIBITED_CMDS: List[str] = [
    "rm",
    "rmdir",
    "mv",
    "cp",
    "cd",
    "pushd",
    "popd",
    "kill",
    "killall",
    "pkill",
    "ps",
    "sudo",
    "su",
    "mount",
    "umount",
    "fdisk",
    "mkfs",
    "dd",
    "sftp",
    "netcat",
    "systemctl",
    "service",
    "crontab",
    "history",
    "export",
    "unset",
    "source",
    "eval",
    "exec",
]

class CryptoAgent:
    """High-level wrapper around an LLM *model* with CTF-specific tooling."""
    
    def __init__(
        self,
        model_config: Dict[str, Any],
        system_prompt: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
        task_info: Dict[str, Any] = None,
        state_callback: Optional[Callable[[], None]] = None
    ):
        """
        Initialize the cryptography agent.
        
        Args:
            model_name: The name of the LLM model to use.
            system_prompt: The system prompt that guides the agent's behavior.
            debug: Whether to print debug information.
            logger: A logger instance for logging messages.
            write_path: The base path for file writing operations.
        """

        self.write_path = Path(task_info["write_path"]).resolve()
        self.timeout: int = task_info["time"]
        self.env = os.environ.copy()
        self.env['NO_COLOR'] = '1'
        
        self.logger = logger
        self.system_prompt = system_prompt
        self.model_config = model_config
        # Callback invoked whenever a new message is appended so that the
        # surrounding TaskRunner can persist state.json frequently.
        self._state_callback = state_callback or (lambda: None)

        self._init_model()
        
    def _init_model(self) -> None:
        self.model = MODEL_MAP[self.model_config["model_name"]](
            self.model_config, self.system_prompt
        )
        self.log(f"Initialized model: {self.model_config['model_name']}")
    
    def log(self, message: str) -> None:
        if self.logger:
            self.logger.log(message)

    def parse_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse the LLM's response to extract reasoning, action type, and action content.
        
        Args:
            response_content: The content of the LLM's response.
            
        Returns:
            Dictionary with reasoning, action_type, and action_content (if applicable).
        """
        self.log("Parsing model response")
        
        result = {
            "reasoning": "",
            "action_type": "unknown",
            "action_content": "",
            "file_path": ""
        }
        
        # ------------------------------------------------------------------
        # Quick sanity-check: make sure all three mandatory tags are present.
        # If any tag is missing we short-circuit and instruct the model to
        # produce a properly formatted response on the next turn.
        # ------------------------------------------------------------------
        mandatory_tags = ["### Reasoning", "### Action", "### Action Content"]
        if not all(tag in response_content for tag in mandatory_tags):
            result["action_type"] = "format error"
            return result
        
        # Extract reasoning (allow with or without trailing colon)
        reasoning_text = ""
        reasoning_match = re.search(r"### Reasoning\s*:?\s*(.*)", response_content, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning_text = reasoning_match.group(1)
            # Trim everything after the subsequent ### Action tag if present
            reasoning_text = reasoning_text.split("### Action", 1)[0].strip()
            result["reasoning"] = reasoning_text
        
        # Extract action (handles both '### Action:' and '### Action' styles)
        action_line = ""
        action_match = re.search(r"### Action\s*:?[\s\n]*(.*)", response_content, re.IGNORECASE)
        if action_match:
            remainder = action_match.group(1).lstrip()
            # Take first non-empty line from remainder as action_line
            for line in remainder.splitlines():
                if line.strip():
                    action_line = line.strip()
                    break

        if action_line:
            if action_line.startswith("create file "):
                result["action_type"] = "create file"
                result["file_path"] = action_line[len("create file "):].strip()
            elif action_line in {"command", "verification", "give up"}:
                result["action_type"] = action_line
            else:
                result["action_type"] = action_line
        
        # Extract action content (accept with or without trailing colon)
        if "### Action Content:" in response_content:
            content_raw = response_content.split("### Action Content:", 1)[1]
        elif "### Action Content" in response_content:
            content_raw = response_content.split("### Action Content", 1)[1]
        else:
            content_raw = None

        if content_raw is not None:
            content = content_raw.strip()
            # Remove any trailing section starting with ### to avoid bleeding
            next_section = content.find("###")
            if next_section != -1:
                content = content[:next_section].strip()
            result["action_content"] = content
        
        return result
    
    def execute_command(self, command: str) -> str:
        """
        Execute a system command and return the output.
        
        Args:
            command: The command to execute.
            
        Returns:
            The command output as a string.
        """
        # Proactive security check
        parts = command.strip().split()
        if parts:
            base = Path(parts[0]).name.lower()
            if base in _PROHIBITED_CMDS:
                msg = f"Error: Command '{base}' is prohibited."
                self.log(msg)
                return msg
        
        try:
            self.log(f"Executing command: {command}")

            # Start the subprocess in a new process group so we can terminate the
            # whole group (the shell and any of its children) on timeout.
            process = subprocess.Popen(
                command,
                cwd=self.write_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.env,
                preexec_fn=os.setsid,  # new process group for safe killing
            )

            try:
                stdout, stderr = process.communicate(timeout=self.timeout)

                if process.returncode == 0:
                    self.log("Command completed successfully")
                    return stdout
                else:
                    error_msg = f"Command failed with error: {stderr}"
                    return error_msg
            except subprocess.TimeoutExpired:
                self._terminate_process_group(process)
                return "Error: Command execution timed out."
        except Exception as e:
            error_msg = f"Error executing command: {e}"
            return error_msg
    
    def create_file(self, file_path: str, content: str) -> str:
        """
        Create a new file with the specified content.
        
        Args:
            file_path: The path where the file should be created.
            content: The content to write to the file.
            
        Returns:
            Success or error message.
        """
        try:
            # Create directories if they don't exist
            real_file_path = self.write_path / file_path
            real_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content to file
            with open(real_file_path, 'w') as f:
                f.write(content)
            self.log(f"Created file at {real_file_path}")
            return f"Successfully created file: {file_path}"
        except Exception as e:
            error_msg = f"Error creating file: {str(e)}"
            return error_msg
    
    def get_model_response(self) -> str:
        """
        Get a response from the LLM using the conversation history.
        
        Returns:
            The model's response as a string.
        """
        try_num = 0
        while True:
            try:
                return self.model.get_response()
            except Exception as e:
                self.log(e)
                if "Error code: 400" in str(e):
                    raise e
                elif "Error code: 429" in str(e):
                    time.sleep(60)
                elif "Error code 403" in str(e):
                    raise e
                error_msg = f"Failed to get response from model: {str(e)}"
                self.log(error_msg)
                try_num += 1
                if try_num > 3:
                    raise e
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """
        Run the crypto agent with a user input.
        
        Args:
            user_input: The user's query or command.
            
        Returns:
            Dictionary with action results.
        """
        last_msg = self.model.messages[-1] if self.model.messages else None

        def _is_same_user(msg_obj):
            if msg_obj is None:
                return False
            # OpenAI / Claude style (dict)
            if isinstance(msg_obj, dict):
                return msg_obj.get("role") == "user" and msg_obj.get("content") == user_input
            # Gemini Content object
            if hasattr(msg_obj, "role") and msg_obj.role == "user":
                # Expect first part with text
                if getattr(msg_obj, "parts", None):
                    part = msg_obj.parts[0]
                    txt = getattr(part, "text", None)
                    return txt == user_input
            return False

        if not _is_same_user(last_msg):
            self.model.add_user_message(user_input)
        # Persist state right after the user message is recorded.
        self._state_callback()
        response = self.get_model_response()
        thinking = response["thinking"]
        response_content = response["answer"]
        self.log(f"Model response:\n{response_content}")
        self.model.add_assistant_message(response_content)
        # Persist state right after the assistant message is recorded.
        self._state_callback()
        
        parsed_response = self.parse_response(response_content)
        
        if parsed_response["action_type"] == "command" and parsed_response["action_content"]:
            command_output = self.execute_command(parsed_response["action_content"])
            output = command_output.replace(str(self.write_path), "")
            
        elif parsed_response["action_type"] == "create file" and parsed_response["action_content"]:
            output = self.create_file(parsed_response["file_path"], parsed_response["action_content"])
            
        elif parsed_response["action_type"] == "verification":
            output = None
        elif parsed_response["action_type"] == "give up":
            output = None
        elif parsed_response["action_type"] == "format error":
            output = None  # Will trigger format reminder below
        else:
            self.log(f"Unknown action type: {parsed_response['action_type']}")
            output = None
        
        return {
            "thinking": thinking,
            "response": response,
            "action_type": parsed_response["action_type"],
            "output": output
        }
            
    @staticmethod
    def _terminate_process_group(proc: subprocess.Popen) -> None:  # noqa: D401
        """Attempt graceful then forced termination of *proc*'s group."""
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            proc.wait(timeout=5)
        except Exception:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
