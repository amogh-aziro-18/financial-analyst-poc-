# OpenRouter / GPT / LLaMA model interface
class AgentModel:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def query_model(self, prompt: str):
        return "model response placeholder"
