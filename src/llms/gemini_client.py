import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Usage: python src\utils\llms\gemini_client.py
# python -c from src.utils.gemini_client import GeminiClient; client = GeminiClient(); print(client.chat('What dimensions should be considered for designing a multidimensional weight system for recording research and generating ideas?'))
class GeminiClient:
    """
    Client to interact with Google's Gemini API
    """
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

    def chat(self, input_text):
        """
        Generate content using the Gemini API
        """
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [{"parts": [{"text": input_text}]}]
        }
        try:
            response = requests.post(f"{self.base_url}?key={self.api_key}", headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to call Gemini API: {e}")
            return None

    @staticmethod
    def upload_to_gemini(path, mime_type=None):
        """
        Upload a file to Google Gemini and return the file object
        See https://ai.google.dev/gemini-api/docs/prompting_with_media
        """
        file = genai.upload_file(path, mime_type=mime_type)
        logging.info(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file

    @staticmethod
    def wait_for_files_active(files):
        """
        Wait for the given files to be active
        """
        logging.info("Waiting for file processing...")
        for name in (file.name for file in files):
            file_status = genai.get_file(name)
            while file_status.state.name == "PROCESSING":
                logging.info(f"File {name} is still processing...")
                file_status = genai.get_file(name)
        logging.info("All files are ready.")
