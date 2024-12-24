from flask import Blueprint

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

from webapp.chat import chat_routes  # 导入路由
