from flask import render_template, request, jsonify
from . import chat_bp
from models.article import Article
from models.article_crud import *
from utils.rag.rag_service import RAGService
from database.connection import db_session
import logging

logger = logging.getLogger(__name__)
rag_service = RAGService()

# 待定
@chat_bp.route('/api/chat/history', methods=['GET'])
def chat_history():
    """获取聊天历史"""
    # TODO: 实现聊天历史记录功能
    return jsonify({
        'success': True,
        'data': {
            'messages': []
        }
    })

# 聊天页
# 可用
@chat_bp.route('/')
def chat_page():
    """聊天页面路由"""
    articles = get_all_articles(db_session)
    return render_template('chat/chat.html', articles=articles)

# 可用
@chat_bp.route('/api/articles/search', methods=['GET'])
def articles_search():
    """搜索文章"""
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

# 可用
@chat_bp.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    """获取文章详情"""
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
                'summary': article.summary,
                'content': article.content,
                'topics': topics
            }
        }
    })

# 可用
@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        article_ids = data.get('article_ids', [])
        
        # 调试日志
        logger.info(f"收到聊天请求：message={message}, article_ids={article_ids}")
        response = rag_service.chat(message)
        
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

# 可用
@chat_bp.route('/api/chat/with_articles', methods=['POST'])
def chat_with_articles():
    """处理多文档RAG对话"""
    try:
        data = request.get_json()
        article_ids = data.get('article_ids', [])
        message = data.get('message', '')
        
        if not article_ids or not message:
            # return jsonify({'error': '缺少必要参数'}), 400
            return jsonify({
                'success': False,
                'message': '缺少必要参数',
                'data': None
            }), 400
            
        # 使用RAG服务处理对话
        logger.info(f"处理聊天请求：message={message}, article_ids={article_ids}")
        if len(article_ids) > 10:
            return jsonify({
                'success': False,
                'message': '最多选择10篇文章',
                'data': None
            }), 400
        response = rag_service.chat_with_articles(article_ids, message)
        
        # return jsonify({'response': response})
        return jsonify({
            'success': True,
            'message': '已成功处理',
            'data': {
                'received_message': message,
                'response': response
            }
        })
    except Exception as e:
        error_msg = f'处理聊天请求失败: {str(e)}'
        logger.error(f"Error in chat_with_articles: {e}")
        # return jsonify({'error': str(e)}), 500
        return jsonify({
            'success': False,
            'message': error_msg,
            'data': None
        }), 500
