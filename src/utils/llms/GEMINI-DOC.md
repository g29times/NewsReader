# Google AI Labs
## API KEY
Use your API keys securely. Do not share them or embed them in code the public can view.

## V2 
https://aistudio.google.com/prompts/new_chat

## V1 Quick Start
Quickly test the API by running a cURL command
[API quickstart guide](https://developers.generativeai.google/tutorials/text_quickstart)
### FIRST DEMO
- REQUEST
```
curl \
  -H "Content-Type: application/json" \
  -d "{\"contents\":[{\"parts\":[{\"text\":\"Explain how AI works\"}]}]}" \
  -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY"
```
- RESPONSE
```
{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Artificial intelligence (AI) is a broad field encompassing many techniques, but at its core, it aims to create systems that can perform tasks that typically require human intelligence.  These tasks include things like learning, reasoning, problem-solving, perception, and natural language understanding.  There's no single \"how\" AI works, as different AI approaches use different methods. However, many rely on these fundamental principles:\n\n**1. Data as Fuel:**  AI 
systems, particularly modern ones, are heavily reliant on data.  The more data they are trained on, the better they generally perform. This data can be anything from images and text to sensor readings and financial transactions.\n\n**2. Algorithms as the Engine:**  Algorithms are sets of rules and statistical techniques that process data.  These algorithms are the \"brain\" of the AI system, guiding how it 
learns, makes decisions, and performs tasks.  Different algorithms are suited for 
different tasks.\n\n**3. Learning Paradigms:** Several core learning paradigms exist:\n\n* **Supervised Learning:** The AI is trained on a labeled dataset, meaning 
the data is already tagged with the correct answers.  For example, showing the AI 
thousands of images of cats labeled \"cat\" and dogs labeled \"dog\" allows it to 
learn to distinguish between them.\n* **Unsupervised Learning:** The AI is trained on an unlabeled dataset, and it must find patterns and structures in the data on 
its own.  This is useful for tasks like clustering similar data points or dimensionality reduction.\n* **Reinforcement Learning:** The AI learns through trial and error by interacting with an environment.  It receives rewards for desirable actions and penalties for undesirable ones, learning to maximize its cumulative reward over time.  This is commonly used in robotics and game playing.\n* **Deep Learning:** A subfield of machine learning that uses artificial neural networks with multiple layers (\"deep\") to extract higher-level features from data.  This approach has been incredibly successful in areas like image recognition, natural language processing, and speech recognition.\n\n**4. Neural Networks as a Key Tool (in Deep Learning):** Inspired by the human brain, neural networks consist of interconnected 
nodes (neurons) organized in layers.  Information flows through these layers, with each layer transforming the data in some way.  The connections between neurons have weights, which are adjusted during the learning process to improve the network's performance.  The process of adjusting these weights is often done through backpropagation, an algorithm that calculates the error and propagates it back through 
the network to update the weights.\n\n**5. Model Evaluation and Improvement:**  Once an AI system is trained, its performance is evaluated on a separate dataset (a 
test set) that wasn't used during training.  This helps to assess how well it generalizes to new, unseen data.  Based on the evaluation results, the model can be further refined, retrained, or improved through various techniques like hyperparameter tuning or model architecture changes.\n\n\nIn summary, AI works by combining large datasets, sophisticated algorithms, and powerful learning techniques to create systems capable of performing complex tasks.  The specific methods employed depend heavily on the task at hand and the available data.  The field is constantly evolving, with new techniques and approaches being developed all the time.\n"        
          }
        ],
        "role": "model"
      },
      "finishReason": "STOP",
      "citationMetadata": {
        "citationSources": [
          {
            "startIndex": 136,
            "endIndex": 268,
            "uri": "https://marine-charts.com/voyage-optimisation/bringing-cutting-edge-ai-artificial-intelligence-to-the-maritime-shipping-industry/"
          }
        ]
      },
      "avgLogprobs": -0.22848429241237017
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 4,
    "candidatesTokenCount": 674,
    "totalTokenCount": 678
  },
  "modelVersion": "gemini-2.0-flash-exp"
}
```
### 列出所有模型
手册地址 https://ai.google.dev/api/models?hl=zh-cn
curl接口 https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_API_KEY

## PRODUCT LEVEL API
- LIBRARY
Python: `pip install google-generativeai`
[](https://ai.google.dev/gemini-api/docs/downloads?_gl=1*vrxsn2*_ga*OTk0NjAyODgzLjE3MzIzNzc2NjA.*_ga_P1DBVKWT6V*MTczMzIwMTYyMS4yOS4xLjE3MzMyMDIxMDEuNTcuMC4xMzI0NDY2NTY1&hl=zh-cn)

- DOCUMENTATION
[](https://ai.google.dev/gemini-api/docs/get-started/python?_gl=1*5z6uyn*_ga*OTk0NjAyODgzLjE3MzIzNzc2NjA.*_ga_P1DBVKWT6V*MTczMzIwMTYyMS4yOS4xLjE3MzMyMDI3NjAuNjAuMC4xMzI0NDY2NTY1)

- Research Assistant API
```
import os
import time
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp", "gemini-exp-1121", "gemini-exp-1206",
  generation_config=generation_config,
  system_instruction="You are an expert scientific researcher who has years of experience in conducting systematic literature surveys and meta-analyses of different topics. You pride yourself on incredible accuracy and attention to detail. You always stick to the facts in the sources provided, and never make up new facts.",
)

# TODO Make these files available on the local file system
# You may need to update the file paths
files = [
  upload_to_gemini("技术报告 - A Comprehensive Survey on Test-Time Adaptation under Distribution Shifts.pdf", mime_type="application/pdf"),
]

# Some files have a processing delay. Wait for them to be ready.
wait_for_files_active(files)

chat_session = model.start_chat(
  history=[
    {
      "role": "user",
      "parts": [
        "You are an expert scientific researcher who has years of experience in conducting systematic literature surveys and meta-analyses of different topics. You pride yourself on incredible accuracy and attention to detail. You always stick to the facts in the sources provided, and never make up new facts. ",
        files[0],
        "Now look at the research paper below, and answer the following questions in 1-2 sentences.\n1. When was the paper published?\n2. What is the sample size?\n3. What is the study methodology? in particular, is it a randomized control trial? \n4. How was the study funded? in particular, was the funding from commercial funders?\n5. What was the key question being studied?\n6. What were the key findings to the key question being studied?",
      ],
    },
    {
      "role": "model",
      "parts": [
        "Here are the answers to your questions based on the provided research paper:\n\n1. The paper was published on March 27, 2023, as indicated by the arXiv metadata.\n\n\n2. The sample size is not explicitly stated in the provided text. The study focuses on a comprehensive review of existing methods and does not involve a new empirical study with human participants.\n\n\n3. The study methodology is a systematic literature survey and meta-analysis, not a randomized controlled trial. It categorizes and analyzes existing test-time adaptation (TTA) methods from different perspectives, compiling a comprehensive overview of existing algorithms and their applications.\n\n\n4. The funding source is not specified in the provided text excerpt. There is no information regarding commercial funding.\n\n\n5. The key question being studied is how to improve the robustness of machine learning models against distribution shifts between training and testing data using test-time adaptation techniques.\n\n\n6. The key findings identify four main categories of test-time adaptation (TTA): source-free domain adaptation, test-time batch adaptation, online test-time adaptation, and test-time prior adaptation. For each category, the study offers a taxonomy of existing algorithms, discusses different learning scenarios, analyzes the application of TTA in various areas, and highlights open challenges and future directions.",
      ],
    },
  ]
)

response = chat_session.send_message("INSERT_INPUT_HERE")

print(response.text)
```