from .llm import LLMService
from .prompts import QAAgentContent

class QAAgent:
    def __init__(self):
        self.llm = LLMService()

    def generate_answer(self, question: str, context: str) -> tuple:
        system_prompt = QAAgentContent.SYSTEM_PROMPT.format(context=context)
        user_prompt = QAAgentContent.get_prompt(question)
        
        response_text, usage = self.llm.call(system_prompt, user_prompt)
        return response_text, usage
