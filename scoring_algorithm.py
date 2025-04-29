from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def semanticScore(query, docs, field='description', model = None):
    if model == None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    
    queryVec = model.encode([query])
    docText = [doc[field] for doc in docs]
    docVecs = model.encode(docText)
    
    similar = cosine_similarity(queryVec, docVecs)[0]

    return sorted(zip(docs, similar), key= lambda x: x[1], reverse = True)