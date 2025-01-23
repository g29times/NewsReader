from flask import render_template, request, jsonify
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
import uuid
import os
import json
from src.utils.redis.redis_service import redis_service
from src.utils.rag.rag_service import MilvusDB
from src.utils.embeddings import jina
import src.utils.embeddings.voyager as voyager
from src.utils.redis.redis_service import RedisService
from src import VECTOR_DB_ARTICLES, CHAT_KEEP_URLS_DEFAULT, KEEP_URLS_DEFAULT, RAG_RECALL_NUM_DEFAULT
import re
from typing import List
from src.utils import async_utils

# from src.utils.memory.memory_service import NotionMemoryService
# # 直接使用NotionMemoryService的单例
# memory_service = NotionMemoryService()

logger = logging.getLogger(__name__)
rag_service = RAGService()
gemini_client = GeminiClient()  # 创建一个全局实例


# --------------------------------- 文章管理 ---------------------------------
# 搜索文章 # TODO 整合到 article_routes
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
        'message': query,
        'data': {
            'articles': [{
                'id': article.id,
                'title': article.title,
                'url': article.url
            } for article in articles]
        }
    })

# 获取文章详情 # TODO 整合到 article_routes
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
        'message': article_id,
        'data': {
            'article': {
                'id': article.id,
                'title': article.title,
                'content': article.content,
                'summary': article.summary,
                'topics': topics,
                'tags': article.tags,
                'source': article.source,
                'vector_ids': article.vector_ids
            }
        }
    })

# --------------------------------- 聊天管理 ---------------------------------
# 聊天页面
@chat_bp.route('/')
def chat_page():
    user_id = '1'
    articles = get_all_articles(db_session)
    # 设置缓存配置
    cache_config = {
        'CHAT_CACHE_TTL': os.getenv('CHAT_CACHE_TTL', 3600),  # 1小时
        'CHAT_CACHE_MAX_SIZE': os.getenv('CHAT_CACHE_MAX_SIZE', 104857600)  # 100MB
    }
    return render_template('chat/chat.html', articles=articles, config=cache_config)

# 普通聊天接口
@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_id = '1'
        # 从form表单中获取参数
        conversation_id = request.form.get('conversation_id', '')
        if not conversation_id:
            return jsonify({
                'success': False,
                'message': 'no conversation_id',
                'data': None
            }), 400
        question = request.form.get('message', '')
        model = request.form.get('model', 'GEMINI_MODEL')
        api_key = request.form.get('api_key', None)
        # 可选参数
        article_ids = request.form.get('article_ids', [])
        keep_urls = request.form.get('keep_urls', CHAT_KEEP_URLS_DEFAULT)
        rag_func = request.form.get('rag_func', 0)
        recall_num = request.form.get('recall_num', RAG_RECALL_NUM_DEFAULT)
        # 获取多文件
        files = request.files.getlist('files')
        
        # 打印完整的请求信息
        # logger.info(f"请求表单数据: {request.form}")
        logger.info(f"请求文件数据: {[f.filename for f in files] if files else []}")
        logger.info(f"收到聊天请求：question={question[:20]}, model={model}, conversation_id={conversation_id}, article_ids={article_ids}, rag_func={rag_func}, recall_num={recall_num}")
        
        # 检查是否包含URL并异步保存URL为文章
        urls = jina._extract_urls(question)
        if urls:
            # 异步保存前两个URL
            async_utils.run_async_task(_save_url_as_article(urls[:KEEP_URLS_DEFAULT], user_id), "异步保存URL失败")

        # 处理问题中的URL
        try:
            question = jina.read_from_jina(question, keep_urls)
        except Exception as e:
            logger.error(f"处理问题URL失败: {str(e)}")
        # 上下文增强
        context = _chat_context(question, files, article_ids, rag_func, recall_num)
        
        # 对话处理
        response = rag_service.chat_with_context(conversation_id, context, question, model, api_key)
        
        # 异步更新LLM记忆 暂停
        # try:
        #     memory_service.update_memory_async(question, str(response))
        # except Exception as e:
        #     logger.error(f"Failed to start memory update: {str(e)}")
        # 这里暂时只返回成功响应，不调用LLM
        return jsonify({
            'success': True,
            'message': conversation_id,
            'data': response
        })
    except Exception as e:
        error_msg = f'处理聊天请求失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'data': None
        }), 500

# 异步将URL保存为文章
async def _save_url_as_article(urls: List[str], user_id: str):
    """异步将URL列表保存为文章"""
    for url in urls:
        try:
            # 1. 构造文章数据
            article_data = {
                'url': url,
                'title': '',  # 由LLM生成
                'content': '',  # 由JINA获取
                'summary': '',  # 由LLM生成
                'key_topics': '',  # 由LLM生成
            }
            
            # 2. 检查URL是否存在
            article = get_article_by_url(db_session, url)
            if article:
                logger.info(f"已经存在同样url的文章：{article.title}")
                continue
                
            # 3. 获取内容
            article_data['content'] = FileInputHandler.jina_read_from_url(url)
            if not article_data['content']:
                logger.warning(f"无法获取URL内容：{url}")
                continue
                
            # 4. 使用LLM处理内容
            from src.webapp.article import article_routes
            article_data = article_routes.summarize_article_content(article_data['content'], article_data)
            
            # 5. 保存到数据库
            article_data.update({
                'type': 'url',
                'user_id': user_id
            })
            new_article = create_article(db_session, article_data)
            logger.info(f"成功将聊天URL保存为文章: {new_article.title}")
        except Exception as e:
            logger.error(f"保存URL为文章失败: {str(e)}")
            continue

# 异步保存文件
async def _save_file_as_article(content: str, filename: str):
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
            return
            
        # 使用公共方法处理文章
        article_data = article_routes.summarize_article_content(content, article_data)
        
        # 再次查重（因为LLM可能生成了一个已存在的标题）
        if get_article_by_title(db_session, article_data['title']):
            logger.info(f"文章标题已存在，跳过保存: {article_data['title']}")
            return
            
        # 创建新文章
        new_article = Article(**article_data)
        db_session.add(new_article)
        db_session.commit()
        
        # 添加到向量库
        # article_routes.add_articles_to_vector_store([new_article])
        
        logger.info(f"文件保存成功: {filename}")
        return new_article
    except Exception as e:
        logger.error(f"文件保存失败: {str(e)}")
        db_session.rollback()
        return None

# 重点方法 上下文增强
def _chat_context(question, files, article_ids, rag_func, recall_num):
    context_parts = []
    # 1. 处理文件内容
    try:
        if files:
            file_content = FileInputHandler.read_from_file(files, query=question)
            if file_content:
                context_parts.append("\n用户上传的媒体文件描述，供非多模态模型，或无法查看媒体的模型参考（相关模型将此参考信息当成自己已了解相关媒介，可用于直接回答用户的问题，无需转述此参考的事实）：")
                context_parts.append(f"\n## 文件内容：\n{file_content}")
                # 对于纯文本文件，异步保存为文章
                for file in files:
                    if file.filename.split('.')[-1].lower() in FileInputHandler.SUPPORTED_TEXT_FILES:
                        async_utils.run_async_task(_save_file_as_article(file_content, file.filename), "异步保存文件失败")
    except Exception as e:
        logger.error(f"处理文件内容失败: {str(e)}")
    
    # 2. 处理勾选的文章
    try:
        if article_ids:
            # 将逗号分隔的字符串转换为整数列表
            id_list = [int(id.strip()) for id in article_ids.split(',') if id.strip()]
            from src.models import article_crud
            articles = article_crud.get_article_by_ids(db_session, id_list)
            if articles:
                articles_text = "\n".join([f"标题：{article.title}\n内容：{article.content if article.content else article.summary}" for article in articles])
                context_parts.append(f"\n## 勾选文章：\n{articles_text}")
    except Exception as e:
        logger.error(f"处理勾选文章失败: {str(e)}")
    
    # 3. 搜索向量RAG
    try:
        if rag_func and int(rag_func) == 1:
            logger.info(f"已开启向量RAG搜索")
            client = MilvusDB()
            children = client.search(
                collection_name=VECTOR_DB_ARTICLES,
                query=question,
                limit=int(recall_num),
                # search_params={"params": {"nprobe": 10}}, # 高级参数 https://milvus.io/docs/v2.0.x/performance_faq.md https://zilliz.com/blog/select-index-parameters-ivf-index
                output_fields=["text", "metadata"],
                # filter='metadata["article_title"] like "%灵魂的 AI%"' # 高级参数 见 zilliz_small_big_chunk_demo.py
            )
            children = children[0]
            logger.info(f"向量库找到文档个数：{len(children)}")
            chunk_ids = []
            for node in children:
                chunk_id = node.get("entity").get("metadata").get("chunk_id")
                if chunk_id not in chunk_ids:
                    chunk_ids.append(chunk_id)
            chunks = []
            redis_client = RedisService()
            for chunk_id in chunk_ids:
                chunk = redis_client.get_hash_value(f"article_chunks", chunk_id)
                chunks.append(chunk)
            chunks = [chunk for chunk in chunks if chunk is not None]
            logger.info(f"Redis找到文档个数：{len(chunks)}")
            rerank_documents = voyager.rerank(query=question, documents=chunks, top_k=int(recall_num))
            rag_context = " ".join([str(chunk) for chunk in rerank_documents])
            if rag_context:
                context_parts.append(f"\n## 相关资料：\n{rag_context}")
    except Exception as e:
        logger.error(f"向量RAG搜索失败: {str(e)}")
    
    # 合并所有上下文
    return "\n\n---\n\n".join(context_parts) if context_parts else ""

# 文件聊天接口 准备depre
@chat_bp.route('/api/chat/with_file', methods=['POST'])
def chat_with_file():
    try:
        user_id = '1'
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未找到上传的文件'})
        file = request.files['file']
        conversation_id = request.form.get('conversation_id', '')
        if not conversation_id:
            return jsonify({
                'success': False,
                'message': 'no conversation_id',
                'data': None
            }), 400
        message = request.form.get('message', '')
        model = request.form.get('model', 'GEMINI_MODEL')
        # 可选参数
        article_ids = request.form.getlist('article_ids', [])
        keep_urls = request.form.get('keep_urls', CHAT_KEEP_URLS_DEFAULT)
        rag_func = request.form.get('rag_func', 0)
        recall_num = request.form.get('recall_num', RAG_RECALL_NUM_DEFAULT)
        logger.info(f"收到文件请求：message={message[:20]}, file={file.filename}, model={model}, conversation_id={conversation_id}, article_ids={article_ids}, rag_func={rag_func}, recall_num={recall_num}")
        # 读取文件内容
        content = FileInputHandler.read_from_file(file)
        if not content:
            return jsonify({'success': False, 'message': '文件内容为空或无法读取'})
        # 上下文增强
        context = _chat_context(content, [file], article_ids, rag_func, recall_num)
        if isinstance(context, tuple):  # 如果返回错误信息
            return jsonify({'success': False, 'message': context[0]})
        # 使用文件内容回答问题 # 简易 gemini_client.query_with_content(content, message)
        response = rag_service.chat_with_context(conversation_id, context, message, model)
        # 在后台线程中异步保存文件
        _run_async_save_article(content, file.filename)
        return jsonify({
            'success': True,
            'message': '处理文件请求',
            'data': response
        })
    except Exception as e:
        error_msg = f'文件处理失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({'success': False, 'message': error_msg})

# 删除消息 (注意 消息只是对话中的一段)
@chat_bp.route('/api/msg/delete', methods=['POST'])
def delete_chat_msg():
    try:
        user_id = '1'
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        message_index = data.get('message_index')
        redis_key = f"user{user_id}_conv{conversation_id}"
        
        def delete_message():
            rag_service.delete_chat_msg(redis_key, int(message_index))
            logger.info(f'消息删除成功: conversation_id={conversation_id}, message_index={message_index}')
        async_utils.run_simple_async(delete_message, error_msg=f'后台删除消息失败')
        return jsonify({'success': True, 'message': '对话删除请求已提交'})
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
        
        def edit_message():
            success = rag_service.edit_chat_msg(redis_key, int(message_index), new_content, role)
            logger.info(f'消息编辑成功: conversation_id={conversation_id}, message_index={message_index}')
        async_utils.run_simple_async(edit_message, error_msg=f'后台编辑消息失败')
        return jsonify({'success': True, 'message': '对话编辑请求已提交'})
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
        conversations = rag_service.load_conversations(int(user_id))
        logger.info(f"User {user_id} has {len(conversations)} conversations")
        return jsonify(conversations)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 搜索对话
@chat_bp.route('/api/conversations/search', methods=['GET'])
def search_conversations():
    try:
        query = request.args.get('query')
        user_id = request.args.get('user_id', '1')
        # 1. 从Redis模糊搜索对话内容
        if not query or query == '':
            conv_ids = []
        else:
            conv_ids = redis_service.search_conversation_content(int(user_id), query)
        # 2. 从数据库搜索对话
        # chats = search_chats(db_session, int(user_id), query, conv_ids)
        conversations = rag_service.load_conversations(int(user_id), query, conv_ids)
        logger.info(f"Searched User {user_id} has {len(conversations)} conversations")
        return jsonify(conversations)
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
