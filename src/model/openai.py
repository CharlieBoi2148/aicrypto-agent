
import openai
import os
import dotenv
from typing import Dict, Any
dotenv.load_dotenv()

from .base_model import BaseModel

class OpenAIChatModel(BaseModel):
    def __init__(self, model_config: Dict[str, Any], system_prompt: str):
        super().__init__(model_config)
        self.init_client()
        self.system_prompt = system_prompt
        self.init_prompt()
        
    def init_client(self):
        if self.client_type == 'openai':
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.client_type == 'azure':
            self.client = openai.AzureOpenAI(
                azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
                api_key=os.getenv("OPENAI_API_KEY"),
                api_version=os.getenv("OPENAI_API_VERSION")
            )
        else:
            raise ValueError(f"Invalid client type: {self.client_type}")    
    
    def init_prompt(self):
        if self.system_prompt:
            self.messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        else:
            self.messages = []
    
    def get_response(self) -> str:
        response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=self.messages,
                    max_tokens=12400,
                )
        return {
            'thinking': "",
            "answer": response.choices[0].message.content}



class OpenAIReasoningModel(BaseModel):
    def __init__(self, model_config: Dict[str, Any], system_prompt: str =None):
        super().__init__(model_config)
        self.init_client()
        self.system_prompt = system_prompt
        self.init_prompt()
        self.reasoning_effort = model_config['reasoning_effort']
        
    def init_client(self):
        if self.client_type == 'openai':
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.client_type == 'azure':
            self.client = openai.AzureOpenAI(
                azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
                api_key=os.getenv("OPENAI_API_KEY"),
                api_version=os.getenv("OPENAI_API_VERSION")
            )
        else:
            raise ValueError(f"Invalid client type: {self.client_type}")    
    
    def init_prompt(self):
        if self.system_prompt:
            self.messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        else:
            self.messages = []
    
    def get_response(self) -> str:
        response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=self.messages,
                    max_completion_tokens=65535,
                    reasoning_effort=self.reasoning_effort
                )
        return {
            'thinking': "",
            "answer": response.choices[0].message.content}
