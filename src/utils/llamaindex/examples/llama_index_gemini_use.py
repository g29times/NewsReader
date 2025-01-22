from llama_index.llms.gemini import Gemini
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if project_root not in sys.path:
    sys.path.append(project_root)
from src import GEMINI_MODELS

# https://docs.llamaindex.ai/en/stable/api_reference/llms/gemini/
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = GEMINI_MODELS[0]
print(GEMINI_MODEL)
llm = Gemini(
    model="models/" + GEMINI_MODEL, api_key=API_KEY,
    system_prompt="You are a helpful assistant."
)
resp = llm.complete("hi LlamaIndex")
print(resp)

# https://python.langchain.com/docs/integrations/providers/google/
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=API_KEY)
resp = llm.invoke("hi LangChain.")
print(resp)

from langchain_voyageai import VoyageAIEmbeddings

embeddings = VoyageAIEmbeddings(model="voyage-3")
resp = embeddings.embed_query("Hello, world!")
print(resp)