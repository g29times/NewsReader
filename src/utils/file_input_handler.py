import requests
import logging
from PyPDF2 import PdfReader

# 获取模块特定的logger
logger = logging.getLogger(__name__)

class FileInputHandler:
    """
    Handler for reading text input from local files or URLs
    """

    @staticmethod
    def extract_text_from_pdf(pdf_path):
        """
        Extract text from a PDF file
        """
        reader = PdfReader(pdf_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        return text

    @staticmethod
    def read_from_file(file_path):
        """
        Read text from a local file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None

    # Call JINA Reader to read text from a URL 调用JINA Reader从URL读取文本
    @staticmethod
    def jina_read_from_url(url, use_jina_reader=True):
        """
        Fetch and read text from a URL, optionally using JINA Reader
        """
        if use_jina_reader:
            url = f"https://r.jina.ai/{url}"
            
        logger.info(f"Fetching content from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.info(f"JINA Reader response - Status: {response.status_code}, First 50 chars: {response.text[:50]}")
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {e}")
            return None

# Example usage
if __name__ == "__main__":
    # 使用示例
    local_text = FileInputHandler.read_from_file('M:\WorkSpace\AIGC\Data\Visual\Anime\prompt.txt')
    logger.info(local_text)

    url_text = FileInputHandler.jina_read_from_url('https://www.google.com')
    logger.info(url_text)
