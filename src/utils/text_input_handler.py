import re

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

# Example usage
if __name__ == "__main__":
    handler = TextInputHandler()
    sample_text = "  This is a SAMPLE text, with Special Characters!  "
    processed_text = handler.preprocess_text(sample_text)
    print(processed_text)  # Output: "this is a sample text with special characters"
