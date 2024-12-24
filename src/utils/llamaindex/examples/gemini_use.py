from llama_index.llms.gemini import Gemini
import os

# https://docs.llamaindex.ai/en/stable/api_reference/llms/gemini/
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
print(GEMINI_MODEL)
llm = Gemini(
    model="models/" + GEMINI_MODEL, api_key=API_KEY,
    system_prompt="You are a helpful assistant."
)
resp = llm.complete("Suppose there are two COI classes {Bank of America, Citibank, Bank of the West}"
"and {Shell Oil, Union’76, Standard Oil, ARCO} in an investment house using Chinese Wall Model."
"Alice would like to read 4 objects following the sequence a, b, c, d."
"Assume CD(a)=Citibank, CD(b)=ARCO, CD(c)=Citibank, CD(d)=Standard Oil."
"Show whether each read is granted and why.")
print(resp)