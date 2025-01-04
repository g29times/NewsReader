dev
    sqlite for RMDB - connection.py
    chromadb for vector DB

prod
    mysql for RMDB
    milvus for vector DB

TODO
    # 需要使用数据库迁移工具(如Alembic)来处理表结构的变更
    数据库优化 字段 索引 取消外键
    table
        article
        user
        note
        chat
            id conversation_id 整合
    cache
    memory

# Alembic
# 1. 初始化 Alembic
alembic init migrations

# 2. 创建迁移脚本
alembic revision --autogenerate -m "update datetime columns"

# 3. 应用迁移
alembic upgrade head