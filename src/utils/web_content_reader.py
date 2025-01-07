from file_input_handler import FileInputHandler
import os
import sys

# 给cascade的工具
def fetch_and_save_web_content(url, output_file='temp_article_content.txt'):
    """
    Fetch web content from a given URL using the JINA Reader and write it to a file.

    :param url: The URL to fetch content from.
    :param output_file: The file path to write the content to.
    """
    print(f"Fetching content from URL: {url}")
    content = FileInputHandler.jina_read_from_url(url)
    if content:
        # Write content directly to the file
        with open(output_file, 'w', encoding='utf-8') as file:
            file.truncate(0)
            file.write(content)
        print(f"Content written to {output_file}")
    else:
        print("Failed to fetch content.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python web_content_reader.py <URL>")
        return
    url = sys.argv[1]
    fetch_and_save_web_content(url)

if __name__ == "__main__":
    main()
