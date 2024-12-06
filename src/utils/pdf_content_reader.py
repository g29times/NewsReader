import PyPDF2
import sys
import os


def read_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
            
            # Save content to a temporary file
            temp_file = os.path.join(os.path.dirname(file_path), 'temp_pdf_content.txt')
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.truncate(0)
                f.write(text)
            print(f"Content has been saved to: {temp_file}")
            return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None


def main():
    if len(sys.argv) != 2:
        print("Usage: python pdf_content_reader.py <pdf_file_path>")
        return
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    content = read_pdf(file_path)


if __name__ == '__main__':
    main()
