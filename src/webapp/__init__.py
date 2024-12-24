from flask import Flask
from webapp.article import article_bp
from webapp.chat import chat_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = 'super secret key'  # 设置密钥
    
    # 配置静态文件路径
    app.static_url_path = '/static'
    app.static_folder = 'static'
    
    # 注册蓝图
    app.register_blueprint(article_bp)
    app.register_blueprint(chat_bp)
    
    return app
