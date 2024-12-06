import requests

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
            print(f"File not found: {file_path}")
            return None

    # Call JINA Reader to read text from a URL 调用JINA Reader从URL读取文本
    @staticmethod
    def jina_read_from_url(url, use_jina_reader=True):
        """
        Fetch and read text from a URL, optionally using JINA Reader
        """
        if use_jina_reader:
            url = f"https://r.jina.ai/{url}"
        try:
            print(url)
            response = requests.get(url)
            response.raise_for_status()
            print("JINA READER STATUS", response.status_code)
            # print(response.text)
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching URL {url}: {e}")
            return None

# Example usage
if __name__ == "__main__":
    print()
    # handler = FileInputHandler()
    # local_text = handler.read_from_file('M:\WorkSpace\AIGC\Data\Visual\Anime\prompt.txt')
    # print(local_text)

    # url_text = handler.jina_read_from_url('https://www.google.com')
    # print(url_text)
