# https://ramnes.github.io/notion-sdk-py/
import os
from notion_client import Client
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NOTE_DATABASE_ID = os.getenv('NOTE_DATABASE_ID')
CHAT_DATABASE_ID = os.getenv('CHAT_DATABASE_ID')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')

def split_text_into_chunks(text: str, chunk_size: int = 1900) -> list:
    """
    将文本分割成小块，确保每块不超过指定大小
    
    Args:
        text: 要分割的文本
        chunk_size: 每块的最大大小（默认1900字符，留出余量）
        
    Returns:
        list: 分割后的文本块列表
    """
    chunks = []
    current_chunk = ""
    
    # 按段落分割
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        # 如果段落本身超过chunk_size，需要进一步分割
        if len(paragraph) > chunk_size:
            # 按句子分割
            sentences = paragraph.replace('. ', '.\n').split('\n')
            for sentence in sentences:
                # 如果句子本身超过chunk_size，按chunk_size直接分割
                if len(sentence) > chunk_size:
                    for i in range(0, len(sentence), chunk_size):
                        chunk = sentence[i:i + chunk_size]
                        if chunk:
                            chunks.append(chunk)
                else:
                    # 检查添加这个句子是否会导致当前块超过限制
                    if len(current_chunk) + len(sentence) + 2 > chunk_size:  # +2 是为了考虑换行符
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += '\n'
                        current_chunk += sentence
        else:
            # 检查添加这个段落是否会导致当前块超过限制
            if len(current_chunk) + len(paragraph) + 2 > chunk_size:  # +2 是为了考虑换行符
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
            else:
                if current_chunk:
                    current_chunk += '\n'
                current_chunk += paragraph
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk)
    
    # 最后检查一遍，确保没有块超过限制
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > chunk_size:
            # 如果还有超过限制的块，按chunk_size强制分割
            for i in range(0, len(chunk), chunk_size):
                final_chunks.append(chunk[i:i + chunk_size])
        else:
            final_chunks.append(chunk)
    
    return final_chunks

def save_simple_content(types, title, content, database_id=None):
    """
    保存简单内容到Chat数据库，支持长文本自动分页
    :param types: 笔记类型列表 [ARTICLE/CHAT/NOTE/BLOG/IDEA/MEMORY]
    :param title: 聊天标题
    :param content: 聊天内容
    :param database_id: 目标数据库ID，默认使用CHAT_DATABASE_ID
    :return: 创建的第一个页面ID
    """
    try:
        return create_long_note_sdk(types, title, content, database_id=database_id or CHAT_DATABASE_ID)
    except Exception as e:
        logger.error(f"保存简单内容失败: {str(e)}")
        raise e

def create_note_sdk(title, content, articles=None, chats=None, source="Personal", types=None):
    """
    使用Notion SDK创建笔记
    :param title: 笔记标题
    :param content: 笔记内容
    :param articles: 关联的文章ID列表
    :param chats: 关联的对话ID列表
    :param source: 来源 (NewsReader/Personal/LLM)
    :param types: 笔记类型列表 [NOTE/BLOG/IDEA/MEMORY]
    :return: 创建的笔记信息
    """
    try:
        notion = Client(auth=NOTION_API_KEY)
        if types is None:
            types = ["NOTE"]
            
        # 构建页面属性
        properties = {
            "title": {"title": [{"text": {"content": title}}]},
            "articles": {"rich_text": [{"text": {"content": ','.join(articles) if articles else ""}}]},
            "chats": {"rich_text": [{"text": {"content": ','.join(chats) if chats else ""}}]},
            "source": {"select": {"name": source}},
            "type": {"multi_select": [{"name": t} for t in types]}
        }
        
        # 将内容分割成多个块
        content_chunks = split_text_into_chunks(content)
        
        # 构建页面内容块
        children = []
        for chunk in content_chunks:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })
        
        return notion.pages.create(
            parent={"database_id": NOTE_DATABASE_ID},
            properties=properties,
            children=children
        )
    except Exception as e:
        logger.error(f"使用SDK创建笔记失败: {str(e)}")
        raise

def create_long_note_sdk(types: list, title: str, content: str, properties=None, database_id=None):
    """创建长文章，如果内容超过限制会自动分页
    
    Args:
        types: 类型列表 [ARTICLE/CHAT/NOTE/BLOG/IDEA/MEMORY]
        title: 文章标题
        content: 文章内容
        properties: 额外的属性，根据类型不同而不同
            - ARTICLE: url, topics, summary
            - NOTE: articles, chats, source
        database_id: 目标数据库ID，默认使用NOTE_DATABASE_ID
        
    Returns:
        str: 第一个页面的ID
    """
    try:
        # 初始化notion客户端
        notion = Client(auth=NOTION_API_KEY)
        properties = properties or {}
        
        # 使用指定的数据库ID或默认的笔记数据库ID
        target_db_id = database_id or NOTE_DATABASE_ID
        
        # 分割内容为多个块
        chunks = split_text_into_chunks(content, chunk_size=1900)
        
        # 计算需要的页数（每页最多99个内容块，为导航块预留1个位置）
        total_pages = (len(chunks) + 98) // 99  
        if total_pages == 0:
            total_pages = 1
            
        # 创建所有页面
        page_ids = []
        for page_num in range(total_pages):
            # 构建页面标题
            page_title = title if page_num == 0 else f"{title}-{page_num + 1}"
            
            # 计算当前页面的块范围（每页最多99个内容块）
            start_idx = page_num * 99  
            end_idx = min((page_num + 1) * 99, len(chunks))  
            current_chunks = chunks[start_idx:end_idx]
            
            # 构建页面属性
            page_properties = {
                "title": {"title": [{"text": {"content": page_title}}]},
            }
            
            # 根据类型添加不同的属性
            if types[0] == 'ARTICLE':
                # Articles: url, topics, summary
                if url := properties.get('url'):
                    page_properties["url"] = {"rich_text": [{"text": {"content": url}}]}
                if topics := properties.get('topics'):
                    page_properties["key_topics"] = {"rich_text": [{"text": {"content": ", ".join(topics)}}]}
                if summary := properties.get('summary'):
                    page_properties["summary"] = {"rich_text": [{"text": {"content": summary}}]}
            elif types[0] == 'NOTE':
                # Notes: articles, chats, source
                if source := properties.get('source'):
                    page_properties["source"] = {"select": {"name": source}}
                if articles := properties.get('articles'):
                    page_properties["articles"] = {"rich_text": [{"text": {"content": ", ".join(articles)}}]}
                if chats := properties.get('chats'):
                    page_properties["chats"] = {"rich_text": [{"text": {"content": ", ".join(chats)}}]}
            # Chat类型不需要额外属性
            
            # 创建页面
            page = notion.pages.create(
                parent={"database_id": target_db_id},
                properties=page_properties
            )
            
            # 保存页面ID
            page_id = page["id"]
            page_ids.append(page_id)
            
            # 添加内容块
            children = []
            for chunk in current_chunks:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    }
                })
            
            # 添加导航信息
            if total_pages > 1:
                nav_text = f"\n\n页面 {page_num + 1}/{total_pages}"
                
                # 添加导航链接
                nav_links = []
                if page_num > 0:  # 不是第一页，添加上一页链接
                    prev_id = page_ids[page_num - 1].replace('-', '')
                    nav_links.append(f"[上一页](notion://www.notion.so/{prev_id})")
                
                if page_num < total_pages - 1:  # 不是最后一页，创建下一页占位符
                    nav_links.append("下一页")  # 先添加占位符
                
                if nav_links:
                    nav_text += " | " + " | ".join(nav_links)
                
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": nav_text}}]
                    }
                })
            
            # 批量添加块
            notion.blocks.children.append(page_id, children=children)
            
            # 如果不是最后一页，更新上一页的下一页链接
            if page_num > 0:
                prev_page_id = page_ids[page_num - 1]
                prev_page_blocks = notion.blocks.children.list(prev_page_id)
                last_block = prev_page_blocks["results"][-1]
                
                # 更新导航文本，添加实际的下一页链接
                nav_text = last_block["paragraph"]["rich_text"][0]["text"]["content"]
                nav_text = nav_text.replace("下一页", f"[下一页](notion://www.notion.so/{page_id.replace('-', '')})")
                
                notion.blocks.update(
                    last_block["id"],
                    paragraph={
                        "rich_text": [{"type": "text", "text": {"content": nav_text}}]
                    }
                )
            
        return page_ids[0]  # 返回第一个页面的ID
        
    except Exception as e:
        logger.error(f"创建长文章失败: {str(e)}")
        raise e


if __name__ == "__main__":
    save_simple_content("title-test", "content", "17430c2067b4808c9aa6ed12f334753e")
    
#     create_long_note_sdk("title-test", """
#  1
#  2
#  3
# """, ["1", "3"], ["2", "3"], "Personal", ["NOTE"])