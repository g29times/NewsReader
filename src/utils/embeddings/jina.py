import os
import sys
import requests
import logging
from typing import List
import aiohttp
import re

# 添加项目根目录到 Python 路径 标准方式
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.append(project_root)
from src import logy

# 配置日志
logger = logging.getLogger(__name__)

JINA_API_KEY = os.getenv("JINA_API_KEY")

# JINA的Embedding task：多种下游任务优化 必须带token
@logy
@staticmethod
async def get_doc_embeddings_jina(documents, task="text-matching"):
    # text-matching，retrieval.passage文档, retrieval.query查询, separation 聚类, classification分类
    url = 'https://api.jina.ai/v1/embeddings'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {JINA_API_KEY}'
    }
    print(f"---------------- jina embedding task: `{len(documents)}` ----------------")
    embeddings = []
    data = {
        "model": "jina-embeddings-v3",
        "task": task,
        "late_chunking": True, # late_chunking 技术
        "dimensions": 128, # MRL技术 可以根据需要减少嵌入的维度（甚至可以降到单个维度！）。较小的嵌入对向量数据库更友好
        "embedding_type": "float",
        "input": documents
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    response_json = response.json()
    # JINA API 返回格式中，嵌入向量在 data[i].embedding 中
    if response_json.get('data'):
        embeddings.extend([item['embedding'] for item in response_json['data']])
    logger.info(f"JINA embedding success")
    return embeddings

# 使用JINA API切分文本 不带token则免费 但速度慢
@logy
@staticmethod
async def split_text_with_jina(text: str, max_chunk_length: int = 1000) -> List[str]:
    """使用JINA API切分文本
    Args:
        text: 要切分的文本
        max_chunk_length: 最大块长度 推荐1024 但是长文某些embedding会报错 可增大到2000 使得分段减少
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
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error {response.status}")
                result = await response.json()
                chunks = result.get("chunks", [])
                if not chunks:  # 如果JINA返回的chunks为空，使用简单的长度切分
                    return [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
                return chunks
    except Exception as e:
        logger.error(f"JINA切片失败: {str(e)}")
        # 如果JINA API失败，使用简单的长度切分作为后备方案
        return [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]

# JINA Reader 不需要token 免费
@logy
@staticmethod
def read_from_url_jina(url: str, mode='read') -> str:
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
        logger.info(f"JINA Reader Fetching {url} SUCCESS: {response.status_code}, Length: {len(response.text)}, First 30 chars: '{response.text[:30]}'")
        
        if mode == 'write':
            with open('src/utils/jina_read_from_url_response_demo.txt', 'w', encoding='utf-8') as f:
                f.write(response.text)
            return None
        else:
            return response.text
    except requests.RequestException as e:
        logger.error(f"JINA Reader Fetching Error'{url}': {e}")
        return None

@logy
@staticmethod
def read_from_jina(message):
    # 提取URL
    urls = extract_urls(message)
    print(f"URLs extracted: {urls}")
    # 插入解析后的内容
    text_with_content = insert_content(message, urls)
    return text_with_content

def extract_urls(text):
  """
  从文本中提取 URL 的函数。
  Returns:
    一个包含提取到的 URL 的列表。
  """
  url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)')
  urls = url_pattern.findall(text)
  return urls

def insert_content(text, urls):
    for url in urls:
        content = read_from_url_jina(url)
        # 直接在 URL 后面插入内容
        text = text.replace(url, f"{url} '''{content}'''")
    return text

# main
if __name__ == "__main__":
    # print(read_from_url_jina("https://www.jina.ai/"))

    # 示例用法
    message = "看看 这篇文章 https://www.sanwenwang.com/sanwen/vivymkqf.html 和 另一篇 https://m.mashhad24.com/html/708/707377.html 说了什么"
    # 提取URL
    urls = extract_urls(message)
    print(f"URLs extracted: {urls}")

    # 插入解析后的内容
    text_with_content = insert_content(message, urls)
    print(text_with_content)
