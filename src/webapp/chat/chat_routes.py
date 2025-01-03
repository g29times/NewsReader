from flask import render_template, request, jsonify
from pymilvus import db
from . import chat_bp
from models.article import Article
from models.article_crud import *
from models.chat import Chat
from models.chat_crud import *
from utils.rag.rag_service import RAGService
from database.connection import db_session
import logging
import asyncio
import uuid
import os
import json

logger = logging.getLogger(__name__)
rag_service = RAGService()

# --------------------------------- 文章管理 ---------------------------------
# 搜索文章
@chat_bp.route('/api/articles/search', methods=['GET'])
def articles_search():
    query = request.args.get('query', '').strip()
    if not query:
        articles = get_all_articles(db_session)
    else:
        articles = search_articles(db_session, query)
    logger.info(f"搜到文章：{len(articles)} 篇")
    return jsonify({
        'success': True,
        'message': '搜索文章',
        'data': {
            'articles': [{
                'id': article.id,
                'title': article.title,
                'url': article.url
            } for article in articles]
        }
    })

# 获取文章详情
@chat_bp.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    article = get_article_by_id(db_session, article_id)
    logger.info(f"获取文章详情成功：{article.title[:30]}")
    if not article:
        return jsonify({'success': False, 'message': '文章未找到'})

    # 从key_topics字段中提取Key Topics
    topics = article.key_topics.split(',') if article.key_topics else []
    
    return jsonify({
        'success': True,
        'message': '获取文章详情',
        'data': {
            'article': {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'summary': article.summary,
                'topics': topics,
                'tags': article.tags,
                'source': article.source,
            }
        }
    })

# --------------------------------- 聊天管理 ---------------------------------
# 聊天页面
@chat_bp.route('/')
def chat_page():
    articles = get_all_articles(db_session)
    return render_template('chat/chat.html', articles=articles)

# 聊天
@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        article_ids = data.get('article_ids', [])
        conversation_id = data.get('conversation_id', '')
        
        # 调试日志
        logger.info(f"收到聊天请求：conversation_id={conversation_id}, message={message}, article_ids={article_ids}")
        if article_ids in [None, []]:
            response = rag_service.chat(conversation_id, message)
        else:
            response = rag_service.chat_with_articles(conversation_id, article_ids, message)
        # 这里暂时只返回成功响应，不调用LLM
        return jsonify({
            'success': True,
            'message': '处理聊天请求',
            'data': {
                'received_message': message,
                'article_count': len(article_ids),
                'response': str(response)
            }
        })

    except Exception as e:
        error_msg = f'处理聊天请求失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'data': None
        }), 500

# # 聊资料 合并
# @chat_bp.route('/api/chat/with_articles', methods=['POST'])
# def chat_with_articles():
#     """处理多文档RAG对话"""
#     try:
#         data = request.get_json()
#         article_ids = data.get('article_ids', [])
#         message = data.get('message', '')
        
#         if not article_ids or not message:
#             # return jsonify({'error': '缺少必要参数'}), 400
#             return jsonify({
#                 'success': False,
#                 'message': '缺少必要参数',
#                 'data': None
#             }), 400
            
#         # 使用RAG服务处理对话
#         logger.info(f"处理聊天请求：message={message}, article_ids={article_ids}")
#         if len(article_ids) > 10:
#             return jsonify({
#                 'success': False,
#                 'message': '最多选择10篇文章',
#                 'data': None
#             }), 400
#         response = rag_service.chat_with_articles(article_ids, message)
        
#         # return jsonify({'response': response})
#         return jsonify({
#             'success': True,
#             'message': '已成功处理',
#             'data': {
#                 'received_message': message,
#                 'response': response
#             }
#         })
#     except Exception as e:
#         error_msg = f'处理聊天请求失败: {str(e)}'
#         logger.error(f"Error in chat_with_articles: {e}")
#         # return jsonify({'error': str(e)}), 500
#         return jsonify({
#             'success': False,
#             'message': error_msg,
#             'data': None
#         }), 500

# 删除消息
@chat_bp.route('/api/chat/delete', methods=['POST'])
def delete_talk():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        message_index = data.get('message_index')
        rag_service.delete_chat(conversation_id, int(message_index))
        return jsonify({'success': True, 'message': '对话删除成功'})
    except Exception as e:
        error_msg = f'删除对话失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({'success': False, 'message': error_msg}), 500

# 编辑消息
@chat_bp.route('/api/chat/edit', methods=['POST'])
def edit_talk():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        message_index = data.get('message_index')
        new_content = data.get('content')
        role = data.get('role', 'user')  # 默认用户消息
        if rag_service.edit_chat(conversation_id, int(message_index), new_content, role):
            return jsonify({'success': True, 'message': '对话编辑成功'})
        else:
            return jsonify({'success': False, 'message': '对话编辑失败'})
    except Exception as e:
        error_msg = f'编辑对话失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({'success': False, 'message': error_msg}), 500

# --------------------------------- 对话管理 ---------------------------------
# 对话=会话 是指一次完整的聊天记录 而“聊天”则是针对每段话的内容交互

# 获取用户的所有对话列表 只显示标题 DONE # TODO: 从session获取用户ID
@chat_bp.route('/api/conversations', methods=['GET'])
def get_conversations():
    try:
        user_id = '1'
        conversations = rag_service.load_conversations(user_id)
        logger.info(f"User {user_id} has {len(conversations)} conversations")
        return jsonify(conversations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 搜索对话
@chat_bp.route('/api/conversations/search', methods=['GET'])
def search_chats_api():
    try:
        query = request.args.get('query')
        user_id = request.args.get('user_id', '1')
        chats = search_chats(db_session, int(user_id), query)
        logger.info(f"Searched chats: {len(chats)}")
        return jsonify([{
                    'id': chat.id,
                    'title': chat.title,
                    'conversation_id': chat.conversation_id,
                } for chat in chats])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取指定对话 DONE
@chat_bp.route('/api/conversation', methods=['GET'])
def get_conversation():
    try:
        user_id = request.args.get('user_id', '1')
        conv_id = request.args.get('conversation_id')
        redis_key = f"user{user_id}_conv{conv_id}"
        # TODO: 检查用户权限
        
        # 从Redis加载对话历史
        messages = rag_service.load_conversation_from_redis(redis_key)
        if messages:
            return jsonify(messages)
        # 如果Redis中没有，尝试从本地文件加载
        file_path = f'chat_store/user{user_id}_conv{conv_id}.json'
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages = data['store'].get(f'user{user_id}', [])
                # 缓存到Redis TODO (仅用于刷数据，开发)
                asyncio.run(rag_service.save_chat(redis_key, messages))
                return jsonify(messages)
        return jsonify([])
    except Exception as e:
        logger.error(f"Error in get_chat_history: {e}")
        return jsonify({'error': str(e)}), 500

# 创建新对话 DONE
@chat_bp.route('/api/conversation', methods=['POST'])
def create_conversation():
    try:
        data = request.get_json()
        title = data.get('title', '新对话')
        user_id = '1'
        # 创建新对话
        chat = Chat(
            user_id=user_id,
            title=title,
            conversation_id=uuid.uuid4().hex[:8]
        )
        db_session.add(chat)
        db_session.commit()
        return jsonify({
            'success': True,
            'data': {
                'id': chat.id,
                'title': chat.title,
                'conversation_id': chat.conversation_id
            }
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 更新对话 DONE
@chat_bp.route('/api/conversation/<int:chat_id>', methods=['PUT'])
def update_conversation(chat_id):
    try:
        data = request.get_json()
        title = data.get('title')
        if title is not None and title != '':
            update_chat(db_session, chat_id, title=title, updated_at=datetime.now())
        else: # 只更新时间
            update_chat(db_session, chat_id, updated_at=datetime.now())
        return jsonify({
            'success': True,
            'data': {
                'title': title,
            }
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 删除对话 DONE
@chat_bp.route('/api/conversation/<int:chat_id>', methods=['DELETE'])
def delete_conversation(chat_id):
    try:
        chat = get_chat(db_session, chat_id)
        # TODO: 检查用户权限
        user_id = '1'
        conv_id = chat.conversation_id
        # 删除Redis缓存（开发保留 暂不删除）
        redis_key = f"user{user_id}_conv{conv_id}"
        rag_service.chat_store.delete_messages(redis_key)
        # 删除数据库记录
        delete_chat(db_session, chat_id)
        # 删除本地文件（开发保留 暂不删除）
        # file_path = f'chat_store/user{user_id}_conv{conv_id}.json'
        # if os.path.exists(file_path):
        #     os.remove(file_path)
        return jsonify({
            'success': True
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# --------------------------------- 笔记管理 ---------------------------------