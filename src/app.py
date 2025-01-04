import os
import sys
import json
from flask import request, jsonify

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from webapp import create_app
from database.connection import db_session
from database.connection import init_database
app = create_app()

# 在应用启动时初始化数据库
init_database()

# 在请求结束时移除数据库会话
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='0.0.0.0', port=5000, debug=True)
