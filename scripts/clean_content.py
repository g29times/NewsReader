import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入数据库配置和模型
from src.models.article import Article

# 创建数据库连接
DATABASE_URL = "sqlite:///m:/WorkSpace/Dev/NewsReader/articles.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_content():
    """检查数据库中有 content 的记录"""
    session = Session()
    try:
        # 查询有 content 的记录总数
        total_with_content = session.query(Article).filter(
            Article.content.isnot(None),
            Article.content != ''
        ).count()
        print(f"\n总共有 {total_with_content} 条记录包含 content")

        # 查询同时有 URL 和 content 的记录数
        url_with_content = session.query(Article).filter(
            Article.content.isnot(None),
            Article.content != '',
            Article.url.isnot(None),
            Article.url != ''
        ).count()
        print(f"其中 {url_with_content} 条记录同时包含 URL 和 content")

        # 显示一些示例记录
        print("\n示例记录:")
        samples = session.query(Article).filter(
            Article.content.isnot(None),
            Article.content != ''
        ).limit(3).all()
        
        for i, article in enumerate(samples, 1):
            print(f"\n记录 {i}:")
            print(f"标题: {article.title}")
            print(f"URL: {article.url}")
            print(f"Content 长度: {len(article.content) if article.content else 0} 字符")
            if article.content:
                preview = article.content[:200] + "..." if len(article.content) > 200 else article.content
                print(f"Content 预览: {preview}")

    finally:
        session.close()

def clean_content():
    """清除有 URL 的记录的 content"""
    session = Session()
    try:
        # 更新有 URL 的记录，清除其 content
        affected_rows = session.query(Article).filter(
            Article.content.isnot(None),
            Article.content != '',
            Article.url.isnot(None),
            Article.url != ''
        ).update({Article.content: ''})
        
        session.commit()
        print(f"\n已清除 {affected_rows} 条记录的 content")

    except Exception as e:
        session.rollback()
        print(f"错误: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # 首先显示当前状态
    print("=== 当前数据库状态 ===")
    check_content()

    # 询问是否清理
    response = input("\n是否清除有 URL 的记录的 content? (y/n): ")
    if response.lower() == 'y':
        clean_content()
        print("\n=== 清理后的数据库状态 ===")
        check_content()
    else:
        print("操作已取消")
