import re
import os
from typing import List, Dict, Any, Optional, Tuple

class TextInputHandler:

    """
    Handler for processing text input for LLM processing
    """
    # TODO 文本清洗
    @staticmethod
    def preprocess_text(text):
        """
        Preprocess text data by cleaning and formatting
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)

        # Convert to lowercase
        text = text.lower()

        return text

    # 使用JINA API切分文本 免费
    @staticmethod
    def split_text_with_jina(text: str, max_chunk_length: int = 1000) -> List[str]:
        """使用JINA API切分文本
        Args:
            text: 要切分的文本
            max_chunk_length: 最大块长度
        Returns:
            切分后的文本块列表
        """
        url = 'https://segment.jina.ai/'
        JINA_API_KEY = os.getenv("JINA_API_KEY")
        headers = {
            'Content-Type': 'application/json',
            # 'Authorization': f'Bearer {JINA_API_KEY}'
        }
        data = {
            "content": text,
            "return_tokens": False,
            "return_chunks": True,
            "max_chunk_length": max_chunk_length
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return [chunk for chunk in result.get("chunks", [])]
        except Exception as e:
            logger.error(f"JINA切片失败: {str(e)}")
            # 如果JINA API失败，使用简单的长度切分作为后备方案
            return [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]

# Example usage
if __name__ == "__main__":
    handler = TextInputHandler()
    sample_text = "  This is a SAMPLE text, with Special Characters!  "
    processed_text = handler.preprocess_text(sample_text)
    print(processed_text)  # Output: "this is a sample text with special characters"
