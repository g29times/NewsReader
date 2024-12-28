import json
from typing import List, Dict, Any, Callable, Union
from tqdm import tqdm

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file and return a list of dictionaries."""
    with open(file_path, 'r') as file:
        return [json.loads(line) for line in file]

def evaluate_retrieval(queries: List[Dict[str, Any]], retrieval_function: Callable, db, k: int = 20) -> Dict[str, float]:
    total_score = 0
    total_queries = len(queries)
    
    for query_item in tqdm(queries, desc="Evaluating retrieval"):
        query = query_item['question']  
        golden_content = query_item['golden_chunk']  
        
        if not golden_content:
            print(f"Warning: No golden content found for query: {query}")
            continue
        
        retrieved_docs = retrieval_function(query, db, k=k)
        
        chunk_found = False
        for doc in retrieved_docs[:k]:
            retrieved_content = doc['metadata'].get('original_content', doc['metadata'].get('content', '')).strip()
            if retrieved_content == golden_content.strip():
                chunk_found = True
                break
        
        query_score = 1.0 if chunk_found else 0.0
        total_score += query_score
    
    average_score = total_score / total_queries
    pass_at_n = average_score * 100
    return {
        "pass_at_n": pass_at_n,
        "average_score": average_score,
        "total_queries": total_queries
    }

def retrieve_base(query: str, db, k: int = 20) -> List[Dict[str, Any]]:
    """
    Retrieve relevant documents using either VectorDB or ContextualVectorDB.
    
    :param query: The query string
    :param db: The VectorDB or ContextualVectorDB instance
    :param k: Number of top results to retrieve
    :return: List of retrieved documents
    """
    return db.search(query, k=k)

def evaluate_db(db, evaluation_set_path: str, k):
    with open(evaluation_set_path, 'r', encoding='utf-8') as f:
        evaluation_data = json.load(f)
    
    results = evaluate_retrieval(evaluation_data, retrieve_base, db, k)
    print(f"Pass@{k}: {results['pass_at_n']:.2f}%")
    print(f"Average Score: {results['average_score']:.4f}")
    print(f"Total queries: {results['total_queries']}")
    return results

# def prepare_evaluation_data(evaluation_set_path: str) -> List[Dict]:
#     """准备评估数据集。
    
#     Args:
#         evaluation_set_path: 评估数据集的路径
        
#     Returns:
#         包含文档的列表，每个文档包含text和metadata
#     """
#     with open(evaluation_set_path, 'r', encoding='utf-8') as f:
#         evaluation_data = json.load(f)
    
#     documents = []
#     for item in evaluation_data:
#         # 从golden_chunk中提取信息
#         chunk = item['golden_chunk']
#         chunk_id = item['chunk_id']
        
#         # 构建metadata
#         metadata = {
#             'chunk_id': chunk_id,
#             'original_content': chunk,  # 保存原始内容用于评估
#         }
        
#         # 如果item中有metadata字段，更新metadata
#         if 'metadata' in item:
#             metadata.update(item['metadata'])
            
#         documents.append({
#             'text': chunk,
#             'metadata': metadata
#         })
    
#     return documents

# def add_documents_to_db(documents: List[Dict], db) -> None:
#     """将文档添加到向量数据库。
    
#     Args:
#         documents: 文档列表，每个文档包含text和metadata
#         db: 向量数据库实例
#     """
#     for doc in tqdm(documents, desc="Adding documents to vector store"):
#         db.add_texts(
#             texts=[doc['text']],
#             metadatas=[doc['metadata']]
#         )

# def prepare_and_add_documents(evaluation_set_path: str, db) -> None:
    """准备数据并添加到向量数据库。
    
    Args:
        evaluation_set_path: 评估数据集的路径
        db: 向量数据库实例
    """
    documents = prepare_evaluation_data(evaluation_set_path)
    add_documents_to_db(documents, db)