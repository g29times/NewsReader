import os
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.models.user import Base, User
from src.models.user_crud import (
    create_user, get_user_by_username, get_users,
    update_user, delete_user
)
from src.utils.security import hash_password, generate_random_password
from connection import db_session, engine

def init_database():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功")

def init_admin_user(session):
    """初始化管理员用户"""
    admin_username = "admin"
    admin = get_user_by_username(session, admin_username)
    
    if not admin:
        # 生成随机密码
        password = generate_random_password()
        
        # 创建管理员用户
        admin = create_user(
            db=session,
            username=admin_username,
            email="admin@newsreader.local",
            password_hash=hash_password(password),
            nickname="管理员",
            bio="系统管理员账户",
            is_admin=True
        )
        
        print(f"""
成功创建管理员账户:
用户名: {admin_username}
密码: {password}
请妥善保管密码信息！
        """)
    else:
        print("管理员账户已存在")

def get_all_users():
    """获取所有用户"""
    session = db_session
    try:
        users = get_users(session, 0, -1)  # -1 表示获取所有用户
        for user in users:
            print(f"用户 {user.username}:")
            print(f"  邮箱: {user.email}")
            print(f"  昵称: {user.nickname}")
            print(f"  是否管理员: {'是' if user.is_admin else '否'}")
            print(f"  是否激活: {'是' if user.is_active else '否'}")
            print(f"  创建时间: {user.created_at}")
            print("---")
    finally:
        session.close()

if __name__ == '__main__':
    # 初始化数据库表
    init_database()
    
    # 初始化管理员用户
    init_admin_user(db_session)
    
    # 显示所有用户
    print("\n当前用户列表:")
    get_all_users()
