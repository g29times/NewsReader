import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# k最邻近 余弦相似度
def k_nearest_neighbors(query_embedding, documents_embeddings, k=5):
    query_embedding = np.array(query_embedding) # convert to numpy array
    documents_embeddings = np.array(documents_embeddings) # convert to numpy array

    # Reshape the query vector embedding to a matrix of shape (1, n) to make it compatible with cosine_similarity
    query_embedding = query_embedding.reshape(1, -1)

    # Calculate the similarity for each item in data
    cosine_sim = cosine_similarity(query_embedding, documents_embeddings)

    # Sort the data by similarity in descending order and take the top k items
    sorted_indices = np.argsort(cosine_sim[0])[::-1]

    # Take the top k related embeddings
    top_k_related_indices = sorted_indices[:k]
    top_k_related_embeddings = documents_embeddings[top_k_related_indices]
    top_k_scores = cosine_sim[0][top_k_related_indices]
    top_k_related_embeddings = [list(row[:]) for row in top_k_related_embeddings] # convert to list

    return top_k_related_embeddings, top_k_related_indices, top_k_scores
