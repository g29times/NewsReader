# """
# Test RAG system functionality
# """
# import os
# import logging
# from pathlib import Path
# from dotenv import load_dotenv
# from src.utils.rag import ChromaDocumentStore, RAGQueryEngine, SQLiteLoader, PDFLoader

# # 设置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # 加载环境变量
# load_dotenv()

# def test_document_store():
#     """测试文档存储功能"""
#     try:
#         # 初始化存储
#         store = ChromaDocumentStore("src/database/chroma_db")
        
#         # 测试文档
#         test_docs = [
#             "人工智能正在改变我们的生活方式",
#             "机器学习是AI的一个重要分支",
#             "深度学习在图像识别领域取得了突破性进展"
#         ]
#         test_metadata = [
#             {"source": "test", "category": "AI"},
#             {"source": "test", "category": "ML"},
#             {"source": "test", "category": "DL"}
#         ]
        
#         # 添加文档
#         store.add_documents(test_docs, test_metadata)
        
#         # 测试搜索
#         results = store.similarity_search("什么是机器学习", k=2)
#         logger.info("Search results:")
#         for result in results:
#             logger.info(f"Document: {result['document']}")
#             logger.info(f"Score: {result['score']}")
#             logger.info(f"Metadata: {result['metadata']}")
#             logger.info("---")
            
#         return True
        
#     except Exception as e:
#         logger.error(f"Document store test failed: {e}")
#         return False

# def test_query_engine():
#     """测试查询引擎功能"""
#     try:
#         # 初始化
#         store = ChromaDocumentStore("src/database/chroma_db")
#         engine = RAGQueryEngine(store)
        
#         # 从SQLite加载文章
#         db_path = Path("src/database/articles.db")
#         if db_path.exists():
#             sqlite_loader = SQLiteLoader(str(db_path))
#             articles = sqlite_loader.load_documents()
#             engine.add_documents(articles)
#             logger.info(f"Loaded {len(articles)} articles from SQLite")
        
#         # 测试PDF加载（如果有测试PDF）
#         pdf_path = Path("src/test_data/test.pdf")
#         if pdf_path.exists():
#             pdf_loader = PDFLoader()
#             pdf_docs = pdf_loader.load_document(str(pdf_path))
#             engine.add_documents(pdf_docs)
#             logger.info(f"Loaded {len(pdf_docs)} pages from PDF")
        
#         # 测试查询
#         test_queries = [
#             "总结一下文章的主要话题",
#             "这些文章中有哪些关于AI的讨论？",
#             "深度学习在这些文章中是如何被描述的？"
#         ]
        
#         for query in test_queries:
#             logger.info(f"\nQuery: {query}")
#             response = engine.query(query)
#             logger.info(f"Response: {response}")
            
#         return True
        
#     except Exception as e:
#         logger.error(f"Query engine test failed: {e}")
#         return False

# def main():
#     """运行所有测试"""
#     # 检查环境变量
#     required_vars = ["VOYAGE_API_KEY", "GOOGLE_API_KEY"]
#     missing_vars = [var for var in required_vars if not os.getenv(var)]
#     if missing_vars:
#         logger.error(f"Missing required environment variables: {missing_vars}")
#         return False
        
#     # 运行测试
#     tests = [
#         ("Document Store", test_document_store),
#         ("Query Engine", test_query_engine)
#     ]
    
#     results = []
#     for test_name, test_func in tests:
#         logger.info(f"\nRunning {test_name} test...")
#         success = test_func()
#         results.append((test_name, success))
#         logger.info(f"{test_name} test: {'PASSED' if success else 'FAILED'}")
        
#     # 输出总结
#     logger.info("\nTest Summary:")
#     for test_name, success in results:
#         logger.info(f"{test_name}: {'PASSED' if success else 'FAILED'}")
        
#     return all(success for _, success in results)

# if __name__ == "__main__":
#     success = main()
#     exit(0 if success else 1)