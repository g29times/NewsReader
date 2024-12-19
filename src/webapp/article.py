import os
import sys
from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from sqlalchemy.exc import IntegrityError

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.article import Article
from models.article_crud import *
from utils.llms.gemini_client import GeminiClient
from utils.llms.llm_tasks import LLMTasks
from utils.file_input_handler import FileInputHandler
from database.connection import db_session
import logging

app = Flask(__name__)
article_bp = Blueprint('article', __name__, url_prefix='/article')
# 获取模块特定的logger
logger = logging.getLogger(__name__)

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

        # 更新文章数据
        logger.debug(f"LLM SUMMARY: {response}")
        article_data.update({
            'title': response.body.get('title', ''),
            'summary': response.body.get('summary', ''),
            'key_points': response.body.get('key_points', '')
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
def search_articles():
    """搜索文章"""
    try:
        query = request.args.get('query', '')
        articles = db_session.query(Article).filter(
            Article.title.contains(query) |
            Article.summary.contains(query) |
            Article.key_points.contains(query) |
            Article.tags.contains(query)
        ).all()
        return render_template('article.html', articles=articles, search_query=query)
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        flash('Error performing search')
        return redirect(url_for('article'))

@app.route('/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        article_ids = data.get('article_ids', [])
        
        # 调试日志
        logger.info(f"收到聊天请求：message={message}, article_ids={article_ids}")
        
        # 这里暂时只返回成功响应，不调用LLM
        return jsonify({
            'success': True,
            'message': '消息已收到',
            'data': {
                'received_message': message,
                'article_count': len(article_ids)
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
