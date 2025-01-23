# notion sdk https://github.com/ramnes/notion-sdk-py
import requests
import json
import logging
import os
from flask import Blueprint, request, jsonify
from os import getenv
from . import note_bp
from .notionsdk import save_simple_content, create_long_note_sdk

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Notion API配置
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_API_KEY = getenv('NOTION_API_KEY')
NOTION_VERSION = "2022-06-28"

@note_bp.route('/create', methods=['POST'])
def create_note_route():
    """处理创建笔记的请求"""
    try:
        data = request.get_json()
        # 获取请求参数
        title = data.get('title', '新笔记')
        content = data.get('content', '')
        types = data.get('types', ['NOTE'])

        # 根据类型选择保存方法
        if types[0] == 'CHAT':
            result = save_simple_content(types, title, content, os.getenv("CHAT_DATABASE_ID"))
        elif types[0] == 'ARTICLE':
            # 收集文章属性
            properties = {
                'url': data.get('url', ''),
                'topics': data.get('topics', []),
                'summary': data.get('summary', '')
            }
            result = create_long_note_sdk(types, title, content, properties, os.getenv("ARTICLE_DATABASE_ID"))
        else:
            # 收集笔记属性
            properties = {
                'articles': data.get('articles', []),
                'chats': data.get('chats', []),
                'source': data.get('source', 'Personal')
            }
            result = create_long_note_sdk(types, title, content, properties, os.getenv("NOTE_DATABASE_ID"))
        
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