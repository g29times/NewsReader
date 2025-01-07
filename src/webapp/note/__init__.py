from flask import Blueprint

note_bp = Blueprint('note', __name__, url_prefix='/note')

from webapp.note import note_routes  # 导入路由
