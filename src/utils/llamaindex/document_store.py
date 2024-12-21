# """
# Vector store implementation using Chroma
# """
# import logging
# from typing import List, Optional
# from llama_index.vector_stores.chroma import ChromaVectorStore
# from llama_index.storage.storage_context import StorageContext
# from llama_index.embeddings.voyageai import VoyageEmbedding
# import chromadb
# import os

# logger = logging.getLogger(__name__)

# class ChromaDocumentStore:
#     def __init__(self, persist_dir: str = "./chroma_db"):
#         """Initialize Chroma document store
        
#         Args:
#             persist_dir: Directory to persist vector store
#         """
#         self.persist_dir = persist_dir
#         self.chroma_client = chromadb.PersistentClient(path=persist_dir)
#         self.collection = self.chroma_client.get_or_create_collection("news_reader")
        
#         # Initialize vector store
#         self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
#         self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
#         # Use Voyage embeddings
#         voyage_api_key = os.getenv("VOYAGE_API_KEY")
#         if not voyage_api_key:
#             raise ValueError("VOYAGE_API_KEY environment variable not set")
            
#         self.embed_model = VoyageEmbedding(
#             model_name="voyage-2", 
#             api_key=voyage_api_key,
#             show_progress_bar=True
#         )
        
#     def add_documents(self, documents: List[str], metadatas: Optional[List[dict]] = None):
#         """Add documents to vector store
        
#         Args:
#             documents: List of document texts
#             metadatas: Optional list of metadata dicts for each document
#         """
#         try:
#             # Create embeddings and add to store
#             embeddings = [
#                 self.embed_model.get_text_embedding(doc) 
#                 for doc in documents
#             ]
            
#             # Add to collection
#             self.collection.add(
#                 embeddings=embeddings,
#                 documents=documents,
#                 metadatas=metadatas if metadatas else [{}] * len(documents),
#                 ids=[f"doc_{i}" for i in range(len(documents))]
#             )
#             logger.info(f"Added {len(documents)} documents to vector store")
            
#         except Exception as e:
#             logger.error(f"Error adding documents to vector store: {e}")
#             raise
            
#     def similarity_search(self, query: str, k: int = 4) -> List[dict]:
#         """Search for similar documents
        
#         Args:
#             query: Query text
#             k: Number of results to return
            
#         Returns:
#             List of documents with similarity scores
#         """
#         try:
#             # Get query embedding
#             query_embedding = self.embed_model.get_text_embedding(query)
            
#             # Search
#             results = self.collection.query(
#                 query_embeddings=[query_embedding],
#                 n_results=k
#             )
            
#             return [
#                 {
#                     "document": doc,
#                     "metadata": meta,
#                     "score": score,
#                     "id": id_
#                 }
#                 for doc, meta, score, id_ in zip(
#                     results["documents"][0], 
#                     results["metadatas"][0],
#                     results["distances"][0],
#                     results["ids"][0]
#                 )
#             ]
            
#         except Exception as e:
#             logger.error(f"Error performing similarity search: {e}")
#             raise
