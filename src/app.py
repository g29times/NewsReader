import os
import sys
import json
from flask import request, jsonify

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from webapp import create_app
from database.connection import db_session

app = create_app()

# 在请求结束时移除数据库会话
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/api/chat/history')
def get_chat_history():
    try:
        uid = request.args.get('uid', '1')  # 默认用户ID为1
        with open('chat_store.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 获取指定用户的历史记录
            history = data.get('store', {}).get(f'user{uid}', [])
            return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host='0.0.0.0', port=5000, debug=True)
