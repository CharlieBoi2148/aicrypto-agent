import openai
import os
import dotenv
from typing import Dict, Any
dotenv.load_dotenv()

from .base_model import BaseModel

class Doubao(BaseModel):
    def __init__(self, model_config: Dict[str, Any], system_prompt: str):
        super().__init__(model_config)
        self.init_client()
        self.system_prompt = system_prompt
        self.init_prompt()
        self.thinking = model_config['thinking']
        
    def init_client(self):
        if self.client_type == 'doubao':
            self.client = openai.OpenAI(
                api_key=os.getenv("DOUBAO_API_KEY"),
                base_url = "https://ark.cn-beijing.volces.com/api/v3"
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
        completion = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=self.messages,
                    max_tokens=16000,
                    timeout=1800
                )
        thinking = completion.choices[0].message.reasoning_content if self.thinking=='enabled' else ""
        answer = completion.choices[0].message.content
        
        return {
            'thinking': thinking,
            'answer': answer
        }
