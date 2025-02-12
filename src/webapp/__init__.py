from flask import Flask, send_from_directory
from webapp.article import article_bp
from webapp.chat import chat_bp
from webapp.note import note_bp
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())  # 从环境变量读取密钥，如果没有则生成随机密钥
    
    # 配置静态文件路径
    app.static_url_path = '/static'
    app.static_folder = 'static'
    
    # 自定义静态文件处理
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        # 根据文件类型和大小设置不同的缓存策略
        if filename.endswith(('.js', '.css')):
            cache_timeout = 2592000  # 30天
            # 对于核心JS/CSS文件，建议浏览器优先使用内存缓存
            response = send_from_directory(app.static_folder, filename)
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}, immutable'
        elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
            cache_timeout = 31536000  # 1年
            # 图片等大文件，建议浏览器使用磁盘缓存
            response = send_from_directory(app.static_folder, filename)
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}, must-revalidate'
        else:
            cache_timeout = 86400  # 其他文件1天
            response = send_from_directory(app.static_folder, filename)
            response.headers['Cache-Control'] = f'public, max-age={cache_timeout}, must-revalidate'
        
        # 添加其他有用的头部
        response.headers['Vary'] = 'Accept-Encoding'  # 支持压缩
        response.headers['X-Content-Type-Options'] = 'nosniff'  # 安全相关
        
        return response
    
    # 注册蓝图
    app.register_blueprint(article_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(note_bp)
    
    return app
