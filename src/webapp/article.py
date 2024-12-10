import os
import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
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
            'title': request.form['title'],
            'url': request.form['url'],
            'tags': request.form['tags'],
            'content': '' # TODO 1 文件形式来源
        }

        # 如果有URL，获取内容
        if article_data['url']:
            article_data['content'] = FileInputHandler.jina_read_from_url(article_data['url'])

        # 使用LLM处理内容
        response = LLMTasks.summarize_and_key_points(article_data['content'])
        
        if response.title == "ERROR" or response.title == "":
            flash(f'Error processing resource: {article_data["url"]}')
            return redirect(url_for('article'))
        logger.info(f"Title: {response.title}")
        logger.info(f"Summary: {response.summary}")
        logger.info(f"Key Points: {response.key_points}")
        
        # 更新文章数据
        article_data.update({
            'title': response.title,
            'summary': response.summary,
            'key_points': response.key_points
        })

        # 创建文章
        create_article(db_session, article_data)
        flash('Article added successfully')

    except IntegrityError:
        db_session.rollback()
        flash('Article with this URL already exists.')
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error adding article: {e}")
        flash(f'Error processing article: {str(e)}')

    return redirect(url_for('article'))

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
    data = request.get_json()
    message = data.get('message', '')
    article_ids = data.get('articles', [])
    print(f"Message: {message}")
    print(f"Selected articles: {article_ids}")
    # 获取选中的文章地址
    article_urls = []
    articles = get_article_by_ids(db_session, article_ids)
    for article in articles:
        article_urls.append({
            'url': article.url
        })
    
    # selected_articles = []
    # for article_id in article_ids:
    #     article = Article.query.get(article_id)
    #     if article:
    #         selected_articles.append({
    #             'title': article.title,
    #             'summary': article.summary,
    #             'key_points': article.key_points,
    #             'tags': article.tags
    #         })
    
    # TODO: 调用LLM处理文章和消息
    # response = llm_client.process_articles_and_message(selected_articles, message)
    client = GeminiClient()
    response = client.chat(message, selected_articles)
    
    return jsonify({
        'status': 'success',
        'message': 'Feature coming soon!'
    })

if __name__ == '__main__':
    app.secret_key = 'super secret key'  # Set the secret key
    app.config['SESSION_TYPE'] = 'filesystem'  # Change to filesystem for initial testing
    # session.init_app(app)

    app.run(debug=True)
