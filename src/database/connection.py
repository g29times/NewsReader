from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./src/database/articles.db')

# Create engine
engine = create_engine(
    DATABASE_URL, 
    echo=False, # echo 打印数据库日志
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {},
    # 连接池配置
    pool_size=20,  # 连接池大小
    max_overflow=30,  # 最大溢出连接数
    pool_timeout=60,  # 连接超时时间（秒）
    pool_recycle=3600,  # 连接回收时间（1小时）
    pool_pre_ping=True  # 连接前ping一下，确保连接有效
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a thread-local session
db_session = scoped_session(SessionLocal)

# Base class for declarative models
Base = declarative_base()

def get_db():
    """
    Dependency that creates a new database session for each request
    """
    db = db_session()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize the database, create all tables"""
    logger.info("Initializing database...")
    from models import article, chat, idea, relation, user
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")

# 测试方法：验证数据库连接
def test_connection():
    try:
        # 创建一个Session实例
        with get_db() as session:
            # 起个简单的sql命令来验证连接（例如：查询当前时间）
            result = session.execute(text("SELECT CURRENT_TIMESTAMP")).fetchone()
            print("Database connection successful. Current timestamp:", result[0])
    except Exception as e:
        print("Database connection failed:", e)


# 如果直接运行这个文件，则执行测试
if __name__ == "__main__":
    test_connection()