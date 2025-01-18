from flask import render_template, request, jsonify, flash, redirect, url_for
from typing import List, Dict, Any, Optional, Tuple, Union
from . import article_bp
from models.article import Article
from models.article_crud import *
from database.connection import db_session
from utils.file_input_handler import FileInputHandler
from utils.llms.article_service import ArticleTasks
import logging
from src.utils.rag.rag_service import RAGService
from src import VECTOR_DB_ARTICLES

logger = logging.getLogger(__name__)
rag_service = RAGService()

# 文章页
@article_bp.route('/')
def article():
    """获取所有文章列表"""
    user_id = '1'
    try:
        articles = get_all_articles(db_session)
        return render_template('article/article.html', articles=articles)
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}")
        return render_template('article/article.html', articles=[])

@article_bp.route('/add_article', methods=['POST'])
def add_article(type: str = "WEB"):
    """添加新文章"""
    user_id = '1'
    try:
        # 1 获取表单数据
        article_data = {
            'title': request.form.get('title', ''),
            'url': request.form.get('url', ''),
            'tags': request.form.get('tags', ''),
            'content': ''  # 将从URL获取内容
        }
        
        # 2 先判断库内是否已经有同样url的文章，如果有，退出
        article = get_article_by_url(db_session, article_data['url'])
        if article:
            logger.info(f"已经存在同样url的文章：{article.title}")
            return jsonify({    
                'success': False,
                'message': '已经存在同样url的文章',
                'data': None
            }), 400
        # 3 如果是通过URL方式，通过JINA Reader获取web内容
        if article_data['url']:
            article_data['content'] = FileInputHandler.jina_read_from_url(article_data['url'])
        # else if FILE ... see chat_routes.chat_with_file

        # 如果没有内容，则返回400错误
        if not article_data['content']:
            return jsonify({
                'success': False,
                'message': '无法获取文章内容',
                'data': None
            }), 400

        # 4 处理勾选的文章，进行内容关联
        article_ids = request.form.getlist('article_ids')
        origin_article_content = article_data['content']
        if article_ids:
            logger.info(f"勾选了文章，进行内容关联：{article_ids}")
            from src.models import article_crud
            articles = article_crud.get_article_by_ids(db_session, article_ids)
            articles_text = "\n".join([f"标题：{article.title}\n内容：{article.content}" for article in articles])
            article_data['content'] = origin_article_content + " ** 关联文章： ** " + articles_text
        # 使用LLM处理内容 进行文章摘要/概要/概括，url和tags来自前端，content来自JINA，6个来自LLM的返回-summary.body.get
        article_data = summarize_article_content(article_data['content'], article_data)
        # 还原article content 摘除相关资料
        article_data['content'] = origin_article_content

        # 5 文章数据入库
        logger.info(f"LLM SUMMARY: SUCCESSED - {article_data['title']}")
        article_data.update({
            'type': type,
            'user_id': user_id
        })
        # 文章入库
        new_article = article_crud.create_article(db_session, article_data)
        logger.info(f"成功添加文章到数据库: {new_article.title}")

        # 6 存向量数据库
        add_articles_to_vector_store([new_article])
        return jsonify({
            'success': True,
            'message': '文章添加成功',
            'data': {
                'id': new_article.id,
                'title': new_article.title,
                'summary': new_article.summary,
                'key_topics': new_article.key_topics
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

@article_bp.route('/delete_article/<int:article_id>', methods=['POST'])
def delete_article_route(article_id):
    """删除文章"""
    user_id = '1'
    try:
        article = get_article_by_id(db_session, article_id)
        if not article:
            return jsonify({
                'success': False,
                'message': '文章不存在',
                'data': None
            }), 404

        delete_article(db_session, article_id)
        # 删除文章后，也删除向量数据库中该文章的信息
        rag_service.delete_articles_from_vector_store([article], collection_name=VECTOR_DB_ARTICLES)
        return jsonify({
            'success': True,
            'message': '文章删除成功',
            'data': {'id': article_id}
        })
    except Exception as e:
        logger.error(f"删除文章失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除文章失败: {str(e)}',
            'data': None
        }), 500

@article_bp.route('/update_article/<int:article_id>', methods=['POST'])
def update_article_route(article_id):
    """更新文章标签"""
    user_id = '1'
    try:
        update_data = {'tags': request.form.get('tags', '')}
        article = update_article(db_session, article_id, update_data)
        
        if not article:
            return jsonify({
                'success': False,
                'message': '文章不存在',
                'data': None
            }), 404

        # 更新文章后，将文章转存向量数据库
        article = get_article_by_id(db_session, article_id)
        add_articles_to_vector_store([article])

        return jsonify({
            'success': True,
            'message': '标签更新成功',
            'data': {
                'id': article_id,
                'tags': article.tags
            }
        })
    except Exception as e:
        logger.error(f"更新文章标签失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新文章标签失败: {str(e)}',
            'data': None
        }), 500

@article_bp.route('/search')
def search_articles_route():
    """搜索文章"""
    user_id = '1'
    try:
        query = request.args.get('query', '')
        articles = search_articles(db_session, query)
        logger.info(f"搜到文章：{len(articles)} 篇")
        return render_template('article/article.html', articles=articles, search_query=query)
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        flash('Error performing search')
        return render_template('article/article.html', articles=[])

@article_bp.route('/vector_article', methods=['POST'])
def batch_vector_store():
    """批量添加文章到向量数据库"""
    user_id = '1'
    try:
        # 1 获取表单数据
        article_ids = request.form.get('article_ids', '')
        articles = get_article_by_ids(db_session, article_ids.split(","))
        # 在后台处理向量数据库操作
        rag_service.add_articles_to_vector_store_background(articles, collection_name=VECTOR_DB_ARTICLES)
        logger.info(f"开始在后台添加文章到向量数据库：{article_ids}")
        return jsonify({
                'success': True,
                'message': '开始在后台添加文章到向量数据库',
                'data': None
            }), 200
    except Exception as e:
        logger.error(f"启动后台向量数据库任务失败: {str(e)}")
        return jsonify({
                'success': False,
                'message': '启动后台向量数据库任务失败',
                'data': None
            }), 200

# 文章摘要
def summarize_article_content(content: str, article_data: dict = None) -> dict:
    """处理文章内容的公共方法
    Args:
        content: 文章内容
        article_data: 可选的文章基础数据
    Returns:
        处理后的文章数据字典
    """
    user_id = '1'
    if article_data is None:
        article_data = {}
    
    if not content:
        raise ValueError('文章内容为空')
    
    # 使用LLM处理内容
    summary = ArticleTasks.summarize_and_key_topics(content)
    if summary.state == "ERROR" or summary.body.get('title') == "":
        raise ValueError(f'LLM API 调用出错 - {summary.desc}')
    
    # 组合文章数据
    article_data.update({
        'content': content,
        'title': summary.body.get('title', ''),
        'summary': summary.body.get('summary', ''),
        'key_topics': summary.body.get('key_topics', ''),
        'source': summary.body.get('source', ''),
        'publication_date': summary.body.get('publication_date', ''),
        'authors': summary.body.get('authors', ''),
        'type': article_data.get('type', 'FILE'),
        'user_id': article_data.get('user_id', 1)  # TODO 从全局获取
    })
    
    return article_data

def add_articles_to_vector_store(articles: List[Article]):
    """将文章添加到向量数据库"""
    user_id = '1'
    try:
        # 在后台处理向量数据库操作
        rag_service.add_articles_to_vector_store_background(articles, collection_name=VECTOR_DB_ARTICLES)
        logger.info(f"开始在后台添加文章到向量数据库: <{article.title}>")
        return True
    except Exception as e:
        logger.error(f"启动后台向量数据库任务失败: {str(e)}")
        return False