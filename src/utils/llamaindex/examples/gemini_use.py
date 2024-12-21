from llama_index.llms.gemini import Gemini
import os

# https://docs.llamaindex.ai/en/stable/api_reference/llms/gemini/
API_KEY = os.getenv("GEMINI_API_KEY1")
MODEL = "gemini-1.5-flash-latest"

llm = Gemini(model="models/" + MODEL, api_key=API_KEY)
resp = llm.complete("Write a poem about a magic backpack")
print(resp)