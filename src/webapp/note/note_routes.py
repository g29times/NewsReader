# notion sdk https://github.com/ramnes/notion-sdk-py
import requests
import json
import logging
from flask import Blueprint, request, jsonify
from os import getenv
from . import note_bp
from .notionsdk import create_long_note_sdk

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Notion API配置
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_DATABASE_ID = "17430c2067b4805280dfe476b6facef1"  # 后续可以移到环境变量
NOTION_API_KEY = getenv('NOTION_API_KEY')  # 后续从环境变量获取
NOTION_VERSION = "2022-06-28"


def create_note(title, content, articles=None, chats=None, source="Personal", types=None):
    """
    创建Notion笔记
    :param title: 笔记标题
    :param content: 笔记内容
    :param articles: 关联的文章ID列表
    :param chats: 关联的对话ID列表
    :param source: 来源 (NewsReader/Personal/LLM)
    :param types: 笔记类型列表 [NOTE/BLOG/IDEA/MEMORY]
    :return: 创建的笔记信息
    """
    try:
        if types is None:
            types = ["NOTE"]
            
        # 构建请求体
        payload = {
            "parent": {
                "database_id": NOTION_DATABASE_ID
            },
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "articles": {
                    "rich_text": [
                        {
                            "text": {
                                "content": ','.join(articles) if articles else ""
                            }
                        }
                    ]
                },
                "chats": {
                    "rich_text": [
                        {
                            "text": {
                                "content": ','.join(chats) if chats else ""
                            }
                        }
                    ]
                },
                "source": {
                    "select": {
                        "name": source
                    }
                },
                "type": {
                    "multi_select": [{"name": t} for t in types]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ]
        }

        headers = {
            'Authorization': f'Bearer {NOTION_API_KEY}',
            'Content-Type': 'application/json',
            'Notion-Version': NOTION_VERSION
        }

        response = requests.post(NOTION_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        logger.error(f"创建笔记失败: {str(e)}")
        raise

@note_bp.route('/create', methods=['POST'])
def create_note_route():
    """处理创建笔记的请求"""
    try:
        data = request.get_json()
        
        # 获取请求参数
        title = data.get('title', '新笔记')
        content = data.get('content', '')
        articles = data.get('articles', [])
        chats = data.get('chats', [])
        source = data.get('source', 'Personal')
        types = data.get('types', ['NOTE'])

        # 创建笔记
        result = create_long_note_sdk(title, content, articles, chats, source, types)
        
        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        logger.error(f"处理创建笔记请求失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print(create_long_note_sdk("title-test", """
 1
 3
""", ["1", "2"], ["1", "2"], "Personal", ["NOTE"]))