from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from sqlalchemy.exc import IntegrityError
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.article import Base, Article
from llms.llm_tasks import LLMTasks
from utils.file_input_handler import FileInputHandler
import logging

app = Flask(__name__)
# 获取模块特定的logger
logger = logging.getLogger(__name__)

# Database setup
engine = create_engine('sqlite:///articles.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
def article():
    articles = session.query(Article).all()
    return render_template('article.html', articles=articles)

@app.route('/add_article', methods=['POST'])
def add_article():
    # from frontend form directly
    title = request.form['title']
    url = request.form['url']
    tags = request.form['tags']
    # from tools TODO 1 no save content
    content = FileInputHandler.jina_read_from_url(url)
    
    try:
        # 创建文章对象但不立即提交
        new_article = Article(
            title=title, 
            url=url, 
            tags=tags,
            # content=content, #暂不保存原文 节省空间
            collection_date=func.now()
        )
        
        # 使用LLM处理内容
        response = LLMTasks.summarize_and_keypoints(content)
        new_article.title = response.title
        new_article.summary = response.summary
        new_article.key_points = response.key_points
        logger.info(f"Title: {new_article.title}")
        logger.info(f"Summary: {new_article.summary}")
        logger.info(f"Key Points: {new_article.key_points}")
        if response.title == "ERROR" or response.title == "": # do not save db
            flash(f'Error processing resource: {url}')
        else: # 保存文章
            session.add(new_article)
            session.commit()
        
    except IntegrityError:
        session.rollback()
        flash('Article with this URL already exists.')
    except Exception as e:
        session.rollback()
        flash(f'Error processing article: {str(e)}')
        
    return redirect(url_for('article'))

@app.route('/delete_article/<int:article_id>', methods=['POST'])
def delete_article(article_id):
    article = session.query(Article).get(article_id)
    if article:
        session.delete(article)
        session.commit()
    return redirect(url_for('article'))

@app.route('/update_article/<int:article_id>', methods=['POST'])
def update_article(article_id):
    article = session.query(Article).get(article_id)
    if article:
        article.tags = request.form['tags']
        session.commit()
    return redirect(url_for('article'))

@app.route('/search', methods=['GET'])
def search_articles():
    query = request.args.get('query', '')
    articles = session.query(Article).filter(
        Article.title.contains(query) |
        Article.summary.contains(query) |
        Article.key_points.contains(query) |
        Article.tags.contains(query)
    ).all()
    return render_template('article.html', articles=articles)

if __name__ == '__main__':
    app.secret_key = 'super secret key'  # Set the secret key
    app.config['SESSION_TYPE'] = 'filesystem'  # Change to filesystem for initial testing
    # session.init_app(app)
    app.debug = True

    app.run(debug=True)
