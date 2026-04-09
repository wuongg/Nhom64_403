import json
from .llm import LLMService
from .prompts import RouterAgentContent

class RouterAgent:
    def __init__(self, faq_structure: str):
        self.faq_structure = faq_structure
        self.llm = LLMService()

    def route(self, question: str) -> tuple:
        system_prompt = RouterAgentContent.SYSTEM_PROMPT.format(faq_structure=self.faq_structure)
        user_prompt = RouterAgentContent.get_prompt(question, self.faq_structure)
        
        response_text, usage = self.llm.call(system_prompt, user_prompt)
        
        try:
            return json.loads(response_text), usage
        except:
            return {
                "file_key": "user",
                "category": "1. An toàn",
                "is_urgent": False,
                "reasoning": "Mock fallback"
            }, usage
