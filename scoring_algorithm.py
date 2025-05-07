from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import numpy as np


def semanticScore(query, docs, field='description', model = None):
    if model == None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    
    queryVec = model.encode([query])
    docText = [doc[field] for doc in docs]
    docVecs = model.encode(docText)
    
    similar = cosine_similarity(queryVec, docVecs)[0]

    return sorted(zip(docs, similar), key= lambda x: x[1], reverse = True)

def initializeLexicon(text = 'vader_lexicon'):
    nltk.download(text)
    return SentimentIntensityAnalyzer()

# 1 == positive, 0 == neutral, -1 == negative
def get_sentiment(sia, text):
    score = sia.polarity_scores(text)
    #print(score)
    sentiment = 1 if score['compound'] > 0.4 else -1 if score['compound'] < -0.4 else 0
    return sentiment

def analyse_sentiment_list(sia, list_text):
    if list_text == []:
        return np.array([])
    sentiment_list = np.array([get_sentiment(sia, text) for text in list_text])
    return sentiment_list

def get_mean_sentiment(array):
    if array.any():
        return np.mean(array)
    return 0

def get_general_sentiment(sia, list_text):
    sentiments = analyse_sentiment_list(sia, list_text)
    mean = get_mean_sentiment(sentiments)
    ###### Maybe just leaving the mean as is would be more beneficial
    #correctedValue = 1 if mean > 0.2 else -1 if mean < -0.2 else 0
    correctedValue = mean
    return correctedValue

if __name__ == "__main__":
    sia = initializeLexicon()
    texts = ['I love here', 'I hate here','This place is nice', 'I have a car']
    general_sentiment = get_general_sentiment(sia, texts)
    print(general_sentiment)