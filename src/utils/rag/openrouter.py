from openai import OpenAI
# https://openrouter.ai/google/gemini-2.0-flash-exp:free
# https://docs.llamaindex.ai/en/stable/examples/llm/openrouter/
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="",
)

completion = client.chat.completions.create(
  model="google/gemini-2.0-flash-exp:free",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What's in this image?"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
          }
        }
      ]
    }
  ]
)
print(completion.choices[0].message.content)