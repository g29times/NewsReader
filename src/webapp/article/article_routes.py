from flask import render_template, request, jsonify, flash, redirect, url_for
from sqlalchemy.sql.functions import user
from . import article_bp
from models.article import Article
from models.article_crud import *
from database.connection import db_session
from utils.file_input_handler import FileInputHandler
from utils.llms.llm_tasks import LLMTasks
import logging

logger = logging.getLogger(__name__)

# 文章页
@article_bp.route('/')
def article():
    """获取所有文章列表"""
    try:
        articles = get_all_articles(db_session)
        return render_template('article/article.html', articles=articles)
    except Exception as e:
        logger.error(f"获取文章列表失败: {str(e)}")
        return render_template('article/article.html', articles=[])

@article_bp.route('/add_article', methods=['POST'])
def add_article(type: str = "WEB"):
    """添加新文章"""
    try:
        # 获取表单数据
        article_data = {
            'title': request.form.get('title', ''),
            'url': request.form.get('url', ''),
            'tags': request.form.get('tags', ''),
            'content': ''  # 将从URL获取内容
        }
        
        # 如果有URL，通过JINA Reader获取web内容
        if article_data['url']:
            article_data['content'] = FileInputHandler.jina_read_from_url(article_data['url'])
        # 如果没有url、url不正确，或JINA返回的内容为空，则返回400错误
        if not article_data['content']:
            return jsonify({
                'success': False,
                'message': '无法获取文章内容',
                'data': None
            }), 400

        # 使用LLM处理内容
        response = LLMTasks.summarize_and_key_topics(article_data['content'])
        # 异常处理
        if response.state == "ERROR" or response.body.get('title') == "":
            error_msg = f'LLM API 调用出错 - {response.desc}'
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': error_msg,
                'data': None
            }), response.status_code # 原始异常码

        # 更新文章数据
        logger.info(f"LLM SUMMARY: {response}")
        article_data.update({
            'title': response.body.get('title', ''),
            # url
            'content': article_data['content'],
            'summary': response.body.get('summary', ''),
            'key_topics': response.body.get('key_topics', ''),
            # tags
            'source': response.body.get('source', ''),
            'publication_date': response.body.get('publication_date', ''),
            'authors': response.body.get('authors', ''),
            'type': type,
            'user_id': 1 # TODO 从全局获取
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
    try:
        article = get_article_by_id(db_session, article_id)
        if not article:
            return jsonify({
                'success': False,
                'message': '文章不存在',
                'data': None
            }), 404

        delete_article(db_session, article_id)
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
    try:
        update_data = {'tags': request.form.get('tags', '')}
        article = update_article(db_session, article_id, update_data)
        
        if not article:
            return jsonify({
                'success': False,
                'message': '文章不存在',
                'data': None
            }), 404

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
    try:
        query = request.args.get('query', '')
        articles = search_articles(db_session, query)
        logger.info(f"搜到文章：{len(articles)} 篇")
        return render_template('article/article.html', articles=articles, search_query=query)
    except Exception as e:
        logger.error(f"Error searching articles: {e}")
        flash('Error performing search')
        return render_template('article/article.html', articles=[])
