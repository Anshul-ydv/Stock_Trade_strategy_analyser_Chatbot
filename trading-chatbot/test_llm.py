import os
from src.llm_client import LLMClient

client = LLMClient()
print("Provider:", client.settings.llm_provider)
print("Ollama URL:", client.settings.ollama_base_url)
print("Ollama Model:", client.settings.ollama_model)
response = client.generate("Say hello")
print("Response:", response)
