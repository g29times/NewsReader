import requests
import logging
from PyPDF2 import PdfReader

# 获取模块特定的logger
logger = logging.getLogger(__name__)

class FileInputHandler:
    """文件处理工具类"""
    
    # 支持的文件类型
    SUPPORTED_TEXT_FILES = {
        'txt', 'csv', 'md', 'html',  # 简单文本
        'pdf',                        # PDF文件
        'doc', 'docx',               # Word文件
        'xls', 'xlsx',               # Excel文件
        'ppt', 'pptx'                # PowerPoint文件
    }
    SUPPORTED_IMAGE_FILES = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    SUPPORTED_VIDEO_FILES = {'mp4', 'avi', 'mov', 'wmv'}
    SUPPORTED_AUDIO_FILES = {'mp3', 'wav', 'ogg', 'flac'}
    # 统一的文件读取入口
    @classmethod
    def read_from_file(cls, file, mime_type=None):
        """统一的文件读取入口
        Args:
            file: 可以是文件路径(str)或FileStorage对象
            mime_type: 可选的MIME类型
        Returns:
            str: 提取的文本内容
        """
        try:
            # 处理FileStorage对象
            if hasattr(file, 'filename'):
                file_ext = file.filename.split('.')[-1].lower()
                # 保存到临时文件
                temp_path = cls._save_temp_file(file)
                content = cls._process_file(temp_path, file_ext)
                cls._remove_temp_file(temp_path)
                return content
            
            # 处理文件路径
            if isinstance(file, str):
                file_ext = file.split('.')[-1].lower()
                return cls._process_file(file, file_ext)
            
            raise ValueError('不支持的文件类型')
            
        except Exception as e:
            logger.error(f"文件处理失败: {str(e)}")
            return None
    
    @classmethod
    def _process_file(cls, file_path, file_ext):
        """根据文件类型处理文件
        Args:
            file_path: 文件路径
            file_ext: 文件扩展名
        Returns:
            str: 提取的文本内容
        """
        # 文本类文件处理
        if file_ext in cls.SUPPORTED_TEXT_FILES:
            if file_ext == 'pdf':
                return cls._extract_text_from_pdf(file_path)
            elif file_ext in {'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}:
                return cls._extract_text_from_office(file_path)
            else:
                return cls._extract_text_from_plain(file_path)
        
        # 视觉类文件处理（预留） TODO
        elif file_ext in cls.SUPPORTED_IMAGE_FILES:
            return cls._process_image(file_path)
        elif file_ext in cls.SUPPORTED_VIDEO_FILES:
            return cls._process_video(file_path)
            
        # 音频类文件处理（预留） TODO
        elif file_ext in cls.SUPPORTED_AUDIO_FILES:
            return cls._process_audio(file_path)
            
        else:
            raise ValueError(f'不支持的文件类型: {file_ext}')
    
    @staticmethod
    def _extract_text_from_plain(file_path):
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
    def _extract_text_from_pdf(file_path):
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
    
    @staticmethod # TODO
    def _process_image(file_path):
        """处理图片文件（预留）"""
        # TODO: 实现图片处理
        raise NotImplementedError('图片处理功能即将推出')
    
    @staticmethod # TODO
    def _process_video(file_path):
        """处理视频文件（预留）"""
        # TODO: 实现视频处理
        raise NotImplementedError('视频处理功能即将推出')
    
    @staticmethod # TODO
    def _process_audio(file_path):
        """处理音频文件（预留）"""
        # TODO: 实现音频处理
        raise NotImplementedError('音频处理功能即将推出')
    
    @staticmethod
    def _save_temp_file(file):
        """保存上传的文件到临时目录"""
        import tempfile
        import os
        
        # 创建临时文件
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        
        # 保存文件内容
        file.save(temp_path)
        return temp_path
    
    @staticmethod
    def _remove_temp_file(temp_path):
        """删除临时文件"""
        import os
        try:
            os.remove(temp_path)
        except:
            pass
    
    @classmethod
    def jina_read_from_url(cls, url: str, mode='read') -> str:
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
    pdf_text = FileInputHandler.read_from_file('./files/temp/ece443-lec01.pdf')
    print(pdf_text)
    print('READ TEXT =====================')
    local_text = FileInputHandler.read_from_file('src/utils/rag/docs/万字长文梳理2024年的RAG.txt')
    print(local_text)
    print('READ URL =====================')
    url_text = FileInputHandler.jina_read_from_url('https://www.google.com')
    print(url_text)
    print('END =====================')
