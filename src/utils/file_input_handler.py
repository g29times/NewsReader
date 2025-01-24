import requests
import logging
from PyPDF2 import PdfReader
import os
import sys
import tempfile
from typing import List, Union
from werkzeug.datastructures import FileStorage

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src.utils.embeddings import jina

# 获取模块特定的logger
logger = logging.getLogger(__name__)

class FileInputHandler:
    """文件处理工具类"""
    
    # 支持的文件类型
    # 前端 fileInput.accept = '.txt,.csv,.html,.md,json,.pdf,.doc,.xlsx,.ppt,.jpg,.jpeg,.png,.gif';
    SUPPORTED_TEXT_FILES = {
        'txt', 'csv', 'md', 'html', 'json',  # 简单文本
        'pdf',                       # PDF文件
        'doc', 'docx',               # Word文件
        'xls', 'xlsx',               # Excel文件
        'ppt', 'pptx'                # PowerPoint文件
    }
    SUPPORTED_IMAGE_FILES = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    SUPPORTED_VIDEO_FILES = {'mp4', 'avi', 'mov', 'wmv'}
    SUPPORTED_AUDIO_FILES = {'mp3', 'wav', 'ogg', 'flac'}
    
    # 统一的文件读取入口
    @staticmethod
    def read_from_file(files: List[Union[str, FileStorage]], mime_types: List[str] = None, query: str=None):
        """统一的文件读取入口
        Args:
            files: 文件列表，每个元素可以是文件路径(str)或FileStorage对象
            mime_types: 可选的MIME类型列表，若提供则必须与files等长
        Returns:
            str: 提取的文本内容
        """
        try:
            if mime_types and len(files) != len(mime_types):
                raise ValueError("mime_types长度必须与files匹配")
            
            file_paths = []
            file_exts = []
            
            # 处理所有文件
            for file in files:
                if isinstance(file, FileStorage):
                    file_ext = file.filename.split('.')[-1].lower()
                    temp_path = FileInputHandler._save_temp_file(file)
                    file_paths.append(temp_path)
                elif isinstance(file, str):
                    file_ext = file.split('.')[-1].lower()
                    file_paths.append(file)
                else:
                    raise ValueError(f'不支持的文件类型: {type(file)}')
                file_exts.append(file_ext)
            
            # 按类型分组处理文件
            text_files = []
            media_files = []
            for path, ext in zip(file_paths, file_exts):
                if ext in FileInputHandler.SUPPORTED_TEXT_FILES:
                    text_files.append(path)
                else:
                    media_files.append(path)
            
            results = []
            # 处理非纯文本文件（图片、视频、音频等）
            if media_files:
                from src.utils.llms.gemini_client import GeminiClient
                media_result = GeminiClient.query_with_file(media_files, '请解析和提取媒体文件的主要内容', '你是一个多媒体助手')
                if media_result:
                    results.append(media_result)
            
            # 处理文本文件
            if text_files:
                text_result = FileInputHandler._process_text(text_files)
                if text_result:
                    results.append(text_result)
            
            return '\n\n'.join(results) if results else None

        except Exception as e:
            logger.error(f"文件处理失败: {str(e)}")
            return None
        finally:
            # 清理临时文件
            for path in file_paths:
                if path.startswith(tempfile.gettempdir()):
                    FileInputHandler._remove_temp_file(path)

    @staticmethod
    def _process_text(file_paths):
        """处理文本文件
        Args:
            file_paths: 文本文件路径列表
        Returns:
            str: 合并后的文本内容
        """
        contents = []
        for file_path in file_paths:
            ext = file_path.split('.')[-1].lower()
            content = None
            if ext in ['txt', 'csv', 'md', 'html', 'json']:
                content = FileInputHandler._extract_text_from_plain(file_path)
            elif ext == 'pdf':
                content = FileInputHandler._extract_text_from_pdf(file_path)
            elif ext in {'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}:
                content = FileInputHandler._extract_text_from_office(file_path)
            if content:
                contents.append(content)
                
        return '\n\n'.join(contents) if contents else None

    @staticmethod
    def _extract_text_from_plain(file_path: str):
        """处理普通文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # 如果UTF-8失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except:
                logger.error(f"无法读取文件: {file_path}")
                return None
    
    @staticmethod
    def _extract_text_from_pdf(file_path: str):
        """处理PDF文件"""
        try:
            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            return text
        except Exception as e:
            logger.error(f"PDF处理失败: {str(e)}")
            return None
    
    @staticmethod # TODO
    def _extract_text_from_office(file_path):
        """处理Office文件（待实现）"""
        # TODO: 实现Office文件的文本提取
        raise NotImplementedError('Office文件处理功能即将推出')
    
    @staticmethod
    def _save_temp_file(file):
        """保存上传的文件到临时目录，保留原始扩展名
        Args:
            file: FileStorage对象
        Returns:
            str: 临时文件路径
        """
        import tempfile
        import os
        
        # 获取原始文件扩展名
        ext = os.path.splitext(file.filename)[1]
        
        # 创建临时文件，保留扩展名
        fd, temp_path = tempfile.mkstemp(suffix=ext)
        os.close(fd)  # 关闭文件描述符
        
        # 保存文件内容
        file.save(temp_path)
        logger.info(f"已保存临时文件: {temp_path}")
        return temp_path
    
    @staticmethod
    def _remove_temp_file(temp_path: str):
        """删除临时文件"""
        import os
        try:
            os.remove(temp_path)
            logger.info(f"已删除临时文件: {temp_path}")
        except:
            pass
    
    @staticmethod
    def jina_read_from_url(url: str, mode='read') -> str:
        return jina.jina_reader(url, mode)


# Example usage
if __name__ == "__main__":
    # 使用示例
    print('READ PDF =====================')
    pdf_text = FileInputHandler.read_from_file('./files/temp/ece443-lec01.pdf')
    print(pdf_text)
    print('READ TEXT =====================')
    local_text = FileInputHandler.read_from_file('src/utils/rag/docs/万字长文梳理2024年的RAG.txt')
    print(local_text)
    print('READ URL =====================')
    url_text = FileInputHandler.jina_read_from_url('https://www.google.com')
    print(url_text)
    print('END =====================')
