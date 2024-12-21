from file_input_handler import FileInputHandler
import logging

# Cascade阅读PDF工具
# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    pdf_path = './files/temp/LlamaIndex-RAG.pdf'
    output_file = './src/utils/temp_article_content.txt'
    try:
        text = FileInputHandler.extract_text_from_pdf(pdf_path)
        # 保存提取的文本到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.info(f"PDF内容已保存到：{output_file}")
    except Exception as e:
        logger.error(f"处理PDF时出错：{e}")

if __name__ == "__main__":
    main()
