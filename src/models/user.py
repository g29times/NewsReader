from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    """用户实体"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # 用户名
    email = Column(String, unique=True, index=True)     # 邮箱
    password_hash = Column(String)                      # 密码哈希
    
    # 用户信息
    nickname = Column(String)                           # 昵称
    avatar = Column(String, nullable=True)              # 头像URL
    bio = Column(String, nullable=True)                 # 个人简介
    
    # 状态字段
    is_active = Column(Boolean, default=True)           # 是否激活
    is_admin = Column(Boolean, default=False)           # 是否是管理员
    last_login = Column(DateTime, nullable=True)        # 最后登录时间
    created_at = Column(DateTime, default=func.now())   # 创建时间
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 更新时间

    # 关系
    articles = relationship("Article", back_populates="user", lazy="dynamic")  # 用户的文章

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'bio': self.bio,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
