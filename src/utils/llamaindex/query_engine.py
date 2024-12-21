# """
# RAG query engine implementation
# """
# import logging
# from typing import List, Optional
# from llama_index.core import VectorStoreIndex
# from llama_index.core import Document
# from llama_index.llms.gemini import Gemini
# from .document_store import ChromaDocumentStore
# import os

# logger = logging.getLogger(__name__)

# class RAGQueryEngine:
#     """Query engine for RAG"""
    
#     def __init__(self, document_store: ChromaDocumentStore):
#         """Initialize query engine
        
#         Args:
#             document_store: Document store instance
#         """
#         self.document_store = document_store
        
#         # Initialize LLM
#         google_api_key = os.getenv("GOOGLE_API_KEY")
#         if not google_api_key:
#             raise ValueError("GOOGLE_API_KEY environment variable not set")
            
#         self.llm = Gemini(
#             api_key=google_api_key,
#             model_name="models/gemini-pro",
#             temperature=0.7,
#             max_tokens=2048
#         )
        
#         # Create index
#         self.index = VectorStoreIndex.from_vector_store(
#             vector_store=document_store.vector_store,
#             storage_context=document_store.storage_context
#         )
        
#         # Create query engine with Chinese system prompt
#         system_prompt = """你是一个专业的AI助手，负责帮助用户理解和分析文档内容。
#         请基于检索到的相关文档回答用户的问题。
#         如果文档中没有相关信息，请明确告知用户。
#         回答应该：
#         1. 准确且基于事实
#         2. 清晰且结构化
#         3. 适当引用来源
#         4. 使用中文回答
#         """
        
#         self.query_engine = self.index.as_query_engine(
#             llm=self.llm,
#             streaming=True,
#             system_prompt=system_prompt
#         )
        
#     def query(self, query_text: str) -> str:
#         """Query the RAG system
        
#         Args:
#             query_text: Query text
            
#         Returns:
#             Response text
#         """
#         try:
#             # Get response
#             response = self.query_engine.query(query_text)
            
#             # Get source documents
#             source_docs = response.source_nodes
            
#             # Format response with sources
#             response_text = str(response)
#             if source_docs:
#                 response_text += "\n\n参考来源:\n"
#                 for doc in source_docs:
#                     if "title" in doc.metadata:
#                         response_text += f"- {doc.metadata['title']}\n"
#                     elif "file_name" in doc.metadata:
#                         response_text += f"- {doc.metadata['file_name']}\n"
                        
#             return response_text
            
#         except Exception as e:
#             logger.error(f"Error querying RAG system: {e}")
#             raise
            
#     def add_documents(self, documents: List[Document]):
#         """Add documents to the system
        
#         Args:
#             documents: List of Document objects
#         """
#         try:
#             # Add to vector store
#             texts = [doc.text for doc in documents]
#             metadatas = [doc.metadata for doc in documents]
#             self.document_store.add_documents(texts, metadatas)
            
#             # Refresh index
#             self.index = VectorStoreIndex.from_vector_store(
#                 vector_store=self.document_store.vector_store,
#                 storage_context=self.document_store.storage_context
#             )
            
#             # Refresh query engine with Chinese system prompt
#             system_prompt = """你是一个专业的AI助手，负责帮助用户理解和分析文档内容。
#             请基于检索到的相关文档回答用户的问题。
#             如果文档中没有相关信息，请明确告知用户。
#             回答应该：
#             1. 准确且基于事实
#             2. 清晰且结构化
#             3. 适当引用来源
#             4. 使用中文回答
#             """
            
#             self.query_engine = self.index.as_query_engine(
#                 llm=self.llm,
#                 streaming=True,
#                 system_prompt=system_prompt
#             )
            
#             logger.info(f"Added {len(documents)} documents to RAG system")
            
#         except Exception as e:
#             logger.error(f"Error adding documents to RAG system: {e}")
#             raise
