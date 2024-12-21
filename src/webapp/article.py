import os
import sys
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from google.ai.generativelanguage_v1beta.types import content
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.article import Article
from models.article_crud import *
from utils.llms.gemini_client import GeminiClient
from utils.llms.llm_tasks import LLMTasks
from utils.file_input_handler import FileInputHandler
from database.connection import db_session
from utils.rag.rag_service import RAGService
import logging

app = Flask(__name__)
article_bp = Blueprint('article', __name__, url_prefix='/article')
# 获取模块特定的logger
logger = logging.getLogger(__name__)

# 初始化RAG服务
rag_service = RAGService()

# 在请求结束时移除数据库会话
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/')
def article():
    """获取所有文章列表"""
    try:
        articles = get_all_articles(db_session)
        return render_template('article.html', articles=articles)
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        flash('Error loading articles')
        return render_template('article.html', articles=[])

@app.route('/add_article', methods=['POST'])
def add_article():
    """添加新文章"""
    try:
        # 获取表单数据
        article_data = {
            'title': request.form.get('title', ''),
            'url': request.form.get('url', ''),
            'tags': request.form.get('tags', ''),
            'content': ''  # 将从URL获取内容
        }

        # 如果有URL，获取内容
        if article_data['url']:
            article_data['content'] = FileInputHandler.jina_read_from_url(article_data['url'])
        # 如果没有url，url不正确，内容为空，则返回
        if not article_data['content']:
            return jsonify({
                'success': False,
                'message': '无法获取文章内容',
                'data': None
            }), 400
        # 使用LLM处理内容
        response = LLMTasks.summarize_and_key_points(article_data['content'])
        
        # 异常处理
        if response.state == "ERROR" or response.body.get('title') == "":
            error_msg = f'LLM API 调用出错 - {response.desc}'
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'data': None
            }), response.status_code

        # 更新文章数据 关键文章记录原文 其他文章不记录
        logger.debug(f"LLM SUMMARY: {response}")
        article_data.update({
            'title': response.body.get('title', ''),
            'summary': response.body.get('summary', ''),
            'key_points': response.body.get('key_points', ''),
            'content': article_data['content'] # 关键文章记录原文
        })

        # 创建新文章
        new_article = Article(**article_data)
        db_session.add(new_article)
        db_session.commit()

        logger.info(f"成功添加文章: {new_article.title}")
        return jsonify({
            'success': True,
            'message': '文章添加成功',
            'data': {
                'id': new_article.id,
                'title': new_article.title,
                'summary': new_article.summary,
                'key_points': new_article.key_points
            }
        })

    except Exception as e:
        db_session.rollback()
        error_msg = f'添加文章失败: {str(e)}'
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'message': error_msg,
            'data': None
        }), 500

@app.route('/delete_article/<int:article_id>', methods=['POST'])
def delete_article_route(article_id):
    """删除文章"""
    try:
        article = delete_article(db_session, article_id)
        if article:
            flash('Article deleted successfully')
        else:
            flash('Article not found')
    except Exception as e:
        logger.error(f"Error deleting article {article_id}: {e}")
        flash('Error deleting article')
    
    return redirect(url_for('article'))

@app.route('/update_article/<int:article_id>', methods=['POST'])
def update_article_route(article_id):
    """更新文章标签"""
    try:
        update_data = {'tags': request.form['tags']}
        article = update_article(db_session, article_id, update_data)
        if article:
            flash('Tags updated successfully')
        else:
            flash('Article not found')
    except Exception as e:
        logger.error(f"Error updating article {article_id}: {e}")
        flash('Error updating tags')
    
    return redirect(url_for('article'))

@app.route('/search')
def search_articles_route():
    """搜索文章"""
    try:
        query = request.args.get('query', '')
        articles = search_articles(db_session, query)
        logger.info(f"搜到文章：{len(articles)} 篇")
        return render_template('article.html', articles=articles, search_query=query)
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        flash('Error performing search')
        return redirect(url_for('article'))


# 可用
@app.route('/chat')
def chat_page():
    """聊天页面路由"""
    articles = get_all_articles(db_session)
    return render_template('chat.html', articles=articles)

# 待定
@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    """处理聊天请求"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        article_ids = data.get('article_ids', [])
        
        if not message:
            return jsonify({'success': False, 'message': '消息不能为空'})
        
        if not article_ids:
            return jsonify({'success': False, 'message': '请选择至少一篇文章'})
            
        # 获取选中的文章
        articles = get_article_by_ids(db_session, article_ids)
        if not articles:
            return jsonify({'success': False, 'message': '未找到选中的文章'})
            
        # 记录请求信息用于调试
        print(f"收到聊天请求：\n消息：{message}\n文章ID：{article_ids}")
        
        # TODO: 调用 LLM 处理聊天
        # 临时返回成功响应
        return jsonify({
            'success': True,
            'data': {
                'response': f'我收到了你的消息：{message}\n你选择了 {len(articles)} 篇文章。'
            }
        })
        
    except Exception as e:
        print(f"处理聊天请求时出错：{str(e)}")
        return jsonify({'success': False, 'message': '处理请求时出错'})

# 待定
@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    """获取聊天历史"""
    # TODO: 实现聊天历史记录功能
    return jsonify({
        'success': True,
        'data': {
            'messages': []
        }
    })

# 可用
@app.route('/api/articles/search', methods=['GET'])
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
        'data': {
            'articles': [{
                'id': article.id,
                'title': article.title,
                'url': article.url
            } for article in articles]
        }
    })

# 可用
@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    """获取文章详情"""
    article = get_article_by_id(db_session, article_id)
    logger.info(f"获取文章详情成功：{article.title[:30]}")
    if not article:
        return jsonify({'success': False, 'message': '文章未找到'})

    # 从key_points字段中提取Key Topics
    topics = article.key_points.split(',') if article.key_points else []
    
    return jsonify({
        'success': True,
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
@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        article_ids = data.get('article_ids', [])
        
        # 调试日志
        logger.info(f"收到聊天请求：message={message}, article_ids={article_ids}")
        response = rag_service.chat_single(message)
        
        # 这里暂时只返回成功响应，不调用LLM
        return jsonify({
            'success': True,
            'message': '消息已收到',
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
@app.route('/api/chat/with_articles', methods=['POST'])
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
        
        # 清理临时collection
        rag_service.cleanup_collection(article_ids)
        
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

@article_bp.route('/article.css')
def serve_css():
    """提供CSS文件"""
    return send_from_directory('templates', 'article.css')

app.register_blueprint(article_bp)

if __name__ == '__main__':
    app.secret_key = 'super secret key'  # Set the secret key
    app.config['SESSION_TYPE'] = 'filesystem'  # Change to filesystem for initial testing
    # session.init_app(app)

    app.run(host='0.0.0.0', port=5000, debug=True)
