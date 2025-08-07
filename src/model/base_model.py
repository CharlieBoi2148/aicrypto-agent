import logging
from typing import Dict, Any

class BaseModel:
    def __init__(self, model_config: Dict[str, Any]):
        self.config = model_config
        self.client_type = self.config['client']
        self.model_name = self.config['model_name']
        self.deployment = self.config['deployment']
       
        self.messages = []
    
  
    
    def init_client(self):
        pass

    def get_response(self, message: str) -> str:
        pass
    
    def init_prompt(self):
        pass
    
    def add_user_message(self, message: str):
        self.messages.append({"role": "user", "content": message})
    
    def add_assistant_message(self, message: str):
        self.messages.append({"role": "assistant", "content": message})
    
    def dump_messages(self):
        """Return the full conversation history as a serialisable list."""
        return self.messages

    def load_messages(self, messages):
        """Restore *messages* previously obtained via :py:meth:`dump_messages`."""
        self.messages = list(messages) if messages else []
    