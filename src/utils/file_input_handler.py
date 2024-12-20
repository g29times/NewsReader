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
    def jina_read_from_url(url, mode='read'):
        """
        Fetch and read text from a URL using JINA Reader
        Args:
            url: The URL to fetch content from
            mode: 'read' to return content directly, 'write' to write to file and return None
        """
        url = f"https://r.jina.ai/{url}"
        logger.info(f"JINA Reader Fetching content from: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            logger.info(f"JINA Reader SUCCESS: {response.status_code}, First 30 chars: '{response.text[:30]}'")
            
            if mode == 'write':
                with open('src/utils/jina_read_from_url_response_demo.txt', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return None
            else:
                return response.text
        except requests.RequestException as e:
            logger.error(f"JINA Reader Error fetching '{url}': {e}")
            return None

# Example usage
if __name__ == "__main__":
    # 使用示例
    print('READ PDF =====================')
    pdf_text = FileInputHandler.extract_text_from_pdf('./files/temp/ece443-lec01.pdf')
    print(pdf_text)
    print('READ TEXT =====================')
    local_text = FileInputHandler.read_from_file('src/utils/file_input_handler.py')
    print(local_text)
    print('READ URL =====================')
    url_text = FileInputHandler.jina_read_from_url('https://www.google.com')
    print(url_text)
    print('END =====================')
