from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from .user import User

def create_user(db: Session, username: str, email: str, password_hash: str, 
                nickname: Optional[str] = None, avatar: Optional[str] = None, 
                bio: Optional[str] = None, is_admin: bool = False) -> User:
    """创建新用户"""
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        nickname=nickname or username,
        avatar=avatar,
        bio=bio,
        is_admin=is_admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int) -> Optional[User]:
    """通过ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """通过用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """获取用户列表"""
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """更新用户信息"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

def update_last_login(db: Session, user_id: int) -> Optional[User]:
    """更新用户最后登录时间"""
    return update_user(db, user_id, last_login=datetime.now())

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    user = get_user(db, user_id)
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True

def deactivate_user(db: Session, user_id: int) -> Optional[User]:
    """停用用户账户"""
    return update_user(db, user_id, is_active=False)

def activate_user(db: Session, user_id: int) -> Optional[User]:
    """激活用户账户"""
    return update_user(db, user_id, is_active=True)
