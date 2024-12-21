# """
# Document loaders for different data sources
# """
# import logging
# from typing import List, Dict
# import sqlite3
# from pathlib import Path
# from llama_index.readers import PDFReader
# from llama_index.schema import Document

# logger = logging.getLogger(__name__)

# class SQLiteLoader:
#     """Load documents from SQLite database"""
    
#     def __init__(self, db_path: str):
#         """Initialize SQLite loader
        
#         Args:
#             db_path: Path to SQLite database
#         """
#         self.db_path = db_path
        
#     def load_documents(self, query: str = "SELECT * FROM articles") -> List[Document]:
#         """Load documents from SQLite
        
#         Args:
#             query: SQL query to execute
            
#         Returns:
#             List of Document objects
#         """
#         try:
#             conn = sqlite3.connect(self.db_path)
#             cursor = conn.cursor()
#             cursor.execute(query)
#             rows = cursor.fetchall()
            
#             documents = []
#             for row in rows:
#                 # Combine relevant fields into text
#                 text = f"Title: {row[1]}\n"
#                 text += f"Summary: {row[2]}\n" 
#                 text += f"Content: {row[3]}\n"
                
#                 # Create metadata
#                 metadata = {
#                     "id": row[0],
#                     "title": row[1],
#                     "source": "sqlite",
#                     "timestamp": row[4] if len(row) > 4 else None
#                 }
                
#                 doc = Document(text=text, metadata=metadata)
#                 documents.append(doc)
                
#             logger.info(f"Loaded {len(documents)} documents from SQLite")
#             return documents
            
#         except Exception as e:
#             logger.error(f"Error loading from SQLite: {e}")
#             raise
            
#         finally:
#             conn.close()
            
# class PDFLoader:
#     """Load documents from PDF files"""
    
#     def __init__(self):
#         """Initialize PDF loader"""
#         self.reader = PDFReader()
        
#     def load_document(self, file_path: str) -> List[Document]:
#         """Load document from PDF file
        
#         Args:
#             file_path: Path to PDF file
            
#         Returns:
#             List of Document objects (one per page)
#         """
#         try:
#             path = Path(file_path)
#             if not path.exists():
#                 raise FileNotFoundError(f"PDF file not found: {file_path}")
                
#             documents = self.reader.load_data(file=file_path)
            
#             # Add metadata
#             for doc in documents:
#                 doc.metadata.update({
#                     "source": "pdf",
#                     "file_path": file_path,
#                     "file_name": path.name
#                 })
                
#             logger.info(f"Loaded {len(documents)} pages from PDF: {path.name}")
#             return documents
            
#         except Exception as e:
#             logger.error(f"Error loading PDF: {e}")
#             raise
