from flask import render_template, request, jsonify
from pymilvus import db
from . import chat_bp
from models.article import Article
from models.article_crud import *
from models.chat import Chat
from models.chat_crud import *
from utils.rag.rag_service import RAGService
from utils.file_input_handler import FileInputHandler
from utils.llms.gemini_client import GeminiClient
from webapp.article import article_routes
from database.connection import db_session
import logging
import asyncio
import uuid
import os
import json
import threading
from src.utils.redis.redis_service import redis_service
# from src.utils.memory.memory_service import NotionMemoryService
# # 直接使用NotionMemoryService的单例
# memory_service = NotionMemoryService()

logger = logging.getLogger(__name__)
rag_service = RAGService()
gemini_client = GeminiClient()  # 创建一个全局实例


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

# 普通聊天接口
@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        article_ids = data.get('article_ids', [])
        conversation_id = data.get('conversation_id', '')
        model = data.get('model', '')
        logger.info(f"收到聊天请求：model={model}, conversation_id={conversation_id}, message={message}, article_ids={article_ids}")
        if not conversation_id:
            return jsonify({
                'success': False,
                'message': 'no conversation_id',
                'data': None
            }), 400
        if article_ids in [None, []]:
            response = rag_service.chat(conversation_id, message, os.getenv(model or "GEMINI_MODEL"))
        else: # 对于长文默认使用更快速的模型
            response = rag_service.chat_with_articles(conversation_id, article_ids, message, os.getenv("GEMINI_MODEL"))
        # 异步更新LLM记忆 暂停
        # try:
        #     memory_service.update_memory_async(message, str(response))
        # except Exception as e:
        #     logger.error(f"Failed to start memory update: {str(e)}")
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

# 文件聊天接口
@chat_bp.route('/api/chat/with_file', methods=['POST'])
def chat_with_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未找到上传的文件'})
        file = request.files['file']
        question = request.form.get('question')
        conversation_id = request.form.get('conversation_id')
        logger.info(f"收到文件请求：question={question}, file={file.filename}")
        # 读取文件内容
        content = FileInputHandler.read_from_file(file)
        if not content:
            return jsonify({'success': False, 'message': '文件内容为空或无法读取'})
        # 使用文件内容回答问题
        response = rag_service.chat_with_file(conversation_id, content, question) # gemini_client.query_with_content(content, question)
        if not response:
            return jsonify({'success': False, 'message': '对话失败'})
        # 在后台线程中异步保存文件
        run_async_save(content, file.filename)
        return jsonify({
            'success': True,
            'message': '处理文件请求',
            'data': response
        })
    except Exception as e:
        error_msg = f'文件处理失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({'success': False, 'message': error_msg})

# 异步文件上传
def run_async_save(content: str, filename: str):
    """在新线程中运行异步保存任务"""
    async def _run_save():
        try:
            await save_file_as_article(content, filename)
        except Exception as e:
            logger.error(f"异步保存文件失败: {str(e)}")
    
    def _run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_save())
        finally:
            loop.close()
    
    # 启动后台线程运行异步任务
    thread = threading.Thread(target=_run_in_thread)
    thread.daemon = True  # 设置为守护线程，这样主程序退出时线程会自动结束
    thread.start()

# 异步文件上传
async def save_file_as_article(content: str, filename: str):
    """异步保存文件为文章"""
    try:
        # 处理文件内容，生成文章
        article_data = {
            'title': filename,  # 临时标题，会被LLM更新
            'url': '',  # 文件类型没有URL
            'tags': '',  # 可以后续添加文件类型标签
            'type': 'FILE'
        }
        
        # 先查重 title
        from models.article_crud import get_article_by_title
        if get_article_by_title(db_session, filename):
            logger.info(f"文件已存在，跳过保存: {filename}")
            return None
        
        # 使用公共方法处理文章
        article_data = article_routes.summarize_article_content(content, article_data)
        
        # 再次查重（因为LLM可能生成了一个已存在的标题）
        if get_article_by_title(db_session, article_data['title']):
            logger.info(f"文章标题已存在，跳过保存: {article_data['title']}")
            return None
        
        # 创建新文章
        new_article = Article(**article_data)
        db_session.add(new_article)
        db_session.commit()
        
        # 添加到向量库
        article_routes.add_articles_to_vector_store(new_article)
        
        logger.info(f"文件保存成功: {filename}")
        return new_article
    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}")
        db_session.rollback()
        return None

# 删除消息 (注意 消息只是对话中的一段)
@chat_bp.route('/api/msg/delete', methods=['POST'])
def delete_chat_msg():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        user_id = '1'
        if not conversation_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        message_index = data.get('message_index')
        redis_key = f"user{user_id}_conv{conversation_id}"
        rag_service.delete_chat_msg(redis_key, int(message_index))
        return jsonify({'success': True, 'message': '对话删除成功'})
    except Exception as e:
        error_msg = f'删除对话失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({'success': False, 'message': error_msg}), 500

# 编辑消息 (注意 消息只是对话中的一段)
@chat_bp.route('/api/msg/edit', methods=['POST'])
def edit_chat_msg():
    try:
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        user_id = '1'
        if not conversation_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        message_index = data.get('message_index')
        new_content = data.get('content')
        role = data.get('role', 'user')  # 默认用户消息
        redis_key = f"user{user_id}_conv{conversation_id}"
        if rag_service.edit_chat_msg(redis_key, int(message_index), new_content, role):
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
        # 1. 从Redis模糊搜索对话内容
        if not query or query == '':
            conv_ids = []
        else:
            conv_ids = redis_service.search_conversation_content(int(user_id), query)
        # 2. 从数据库搜索对话
        chats = search_chats(db_session, int(user_id), query, conv_ids)
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
        # 如果Redis中没有，尝试从本地文件加载 (仅用于开发时首次同步数据)
        file_path = f'chat_store/user{user_id}_conv{conv_id}.json'
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages = data['store'].get(f'user{user_id}', [])
                # 缓存到Redis
                rag_service.save_chat(redis_key, messages)
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
@chat_bp.route('/api/conversation/<string:conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    try:
        user_id = '1'
        data = request.get_json()
        title = data.get('title')
        from sqlalchemy.sql import func
        update = func.datetime('now', 'localtime')
        logger.info(f"更新对话：{datetime.now()}")
        if title is not None and title != '':
            update_chat(db_session, user_id, conversation_id, title=title)
        else: # 只更新时间
            update_chat(db_session, user_id, conversation_id, updated_at=update)
        logger.info(f"更新对话成功：{datetime.now()}")
        return jsonify({
            'success': True,
            'data': {
                'updated_at': datetime.now(),
            }
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 删除对话 DONE
@chat_bp.route('/api/conversation/<string:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    try:
        user_id = '1'
        # 删除数据库记录
        delete_chat(db_session, user_id, conversation_id)
        # 删除Redis缓存（开发保留 暂不删除）
        redis_key = f"user{user_id}_conv{conversation_id}"
        rag_service.delete_chat(redis_key)
        # redis_service.delete_keys(redis_key)
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