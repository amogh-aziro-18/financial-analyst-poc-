import os
from groq import Groq
from dotenv import load_dotenv
from agent.prompts import SYSTEM_PROMPT

# Load .env correctly
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env")
load_dotenv(env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY in config/.env")
class AgentModel:
    """
    Thin wrapper around Groq chat completion.
    Used only for reasoning / natural language answers.
    Tool selection is handled in financial_agent.py (React-style).
    """

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        # Fast, cheap model – good enough for reasoning / explanations
        self.model_name = "llama-3.1-8b-instant"

    def query_model(self, query: str) -> str:
        """
        Ask the LLM a question and get back a string answer.
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.3,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"[GROQ ERROR] {str(e)}"
