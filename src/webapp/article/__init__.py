from flask import Blueprint

article_bp = Blueprint('article', __name__, url_prefix='/article')

from webapp.article import article_routes  # 导入路由
