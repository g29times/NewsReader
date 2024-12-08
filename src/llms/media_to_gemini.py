import os
import sys
import logging
from PyPDF2 import PdfReader
from gemini_client import GeminiClient
import google.generativeai as genai

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.text_input_handler import TextInputHandler
from utils.file_input_handler import FileInputHandler

import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MediaToGemini:
    """
    Class to handle Media and querying Gemini
    """

    # Handle file first at Local 
    @staticmethod
    def query_gemini_with_txt(url=None, question='', retries=2):
        """
        Extract text from a file or URL, preprocess it, and query Gemini with retry logic
        """
        # if file_path:
        #     text = FileInputHandler.extract_text_from_pdf(file_path)
        # elif url:
        text = None
        try:
            text = FileInputHandler.read_from_url(url, use_jina_reader=True)
        except Exception as e:
            logging.error(f"Error reading from JINA {url}: {e}")
        # else:
        #     raise ValueError("Either file_path or url must be provided.")
        if text is None or text.strip() == "":
            logging.error("Failed to extract text from file or URL.")
            return None
        # Preprocess text
        processed_text = TextInputHandler.preprocess_text(text)

        # Initialize Gemini client
        client = GeminiClient()

        # Query Gemini with retry logic
        attempt = 0
        while attempt <= retries:
            try:
                logging.info(f"Querying Gemini (Attempt {attempt + 1})")
                response = client.chat(f"{question}: {processed_text}")
                return response
            except Exception as e:
                logging.error(f"Error querying Gemini: {e}")
                attempt += 1
                if attempt > retries:
                    logging.error("Max retries reached. Failing gracefully.")
                    return None

    # Upload file to remote and Handle on cloud
    # TODO 1 多文件支持 2 多轮对话历史 3 文件处理 小文件和大文件本地处理 中等或有图片的？文件远程处理（没想好）
    @staticmethod
    def upload_and_query_gemini(file_path=None, question='', mime_type=None):
        """
        Upload a file to Google Cloud, wait for processing, and query Gemini
        """
        # Upload the file
        files = [
            GeminiClient.upload_to_gemini(file_path, mime_type=mime_type)
        ]

        # Wait for the file to be active
        GeminiClient.wait_for_files_active(files)

        # Create the model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction="You are an expert scientific researcher who has years of experience in conducting systematic literature surveys and meta-analyses of different topics. You pride yourself on incredible accuracy and attention to detail. You always stick to the facts in the sources provided, and never make up new facts.",
        )

        # Start a chat session
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        "Just answer with a very brief summary.",
                        files[0]
                    ]
                }
            ]
        )

        # Send a message
        response = chat_session.send_message(question)
        return response

# Example usage:
# python .\src\llms\media_to_gemini.py --question 'what is this web about?' --url 'https://browncsci1430.github.io/#home-content'
# python .\src\llms\media_to_gemini.py --question 'describe the image' --file M:\WorkSpace\AIGC\Data\Visual\Anime\FLux.jfif
# python .\src\llms\media_to_gemini.py --question 'write a summary of the paper no more than 100 words' --file M:\WorkSpace\AIGC\Data\Text\Test-Time-Adaptation.pdf
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a file or URL with Gemini.')
    parser.add_argument('--file', dest='file_path', help='Path to the file to process')
    parser.add_argument('--url', dest='url', help='URL to process')
    parser.add_argument('--question', dest='question', required=True, help='Question to ask about the content')
    args = parser.parse_args()

    if not args.file_path and not args.url:
        print("Error: You must provide either a file path or a URL.")
        sys.exit(1)

    if args.file_path:
        response = MediaToGemini.upload_and_query_gemini(file_path=args.file_path, question=args.question)
    else:
        response = MediaToGemini.query_gemini_with_txt(url=args.url, question=args.question)

    print(response)
