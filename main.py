from elasticsearch import Elasticsearch, helpers
import json
import scoring_algorithm
from Query import Query
#import scoring_algorithm

es = Elasticsearch(
    "http://localhost:9200",
    api_key="Z0oyUlE1WUJ0N1duRy1Jd2VLTG86VjB6RkVCazBTSkZXSHd1NTAzbWo1dw==" # INSERT YOUR API KEY HERE
)

INPUT_FILE = "cleaned_books_bulk_30k.jsonl"
INDEX_NAME = "books_30k"


def generate_bulk_actions(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        while True:
            action_line = f.readline()
            if not action_line:
                break  # EOF
            doc_line = f.readline()
            if not doc_line:
                break  # Incomplete pair
            try:
                action = json.loads(action_line)
                doc = json.loads(doc_line)
                yield {
                    "_index": INDEX_NAME,
                    "_source": doc
                }
            except json.JSONDecodeError:
                continue  # Skip malformed entries


if not es.indices.exists(index=INDEX_NAME):
    print(f"Creating index '{INDEX_NAME}'...")
    helpers.bulk(es, generate_bulk_actions(INPUT_FILE))
    print(f"Index {INDEX_NAME} created and documents uploaded")
else:
    print(f"Index {INDEX_NAME} already exists. Skipping bulp upload")

queryText = 'space'

queryElastic = Query(queryText)

res = es.search(index=INDEX_NAME, body=queryElastic.getQuery(), size=15)
docs = []

for hit in res["hits"]["hits"]:
    docs.append(hit["_source"])
    print(hit["_source"]['title'])

similar = scoring_algorithm.semanticScore(queryText,docs)
print("''''''''''''''''''''''''''''''''''''''''")

for sim, score in similar:
    print(f"The title '{sim['title']}' received a score of {score}")



"""We can:
    * Implement Cosine similarity
    * Use sentence transformer (?)
    * Embed NLP sentiment
    * Custom python recommendation system
    * Maybe cosine similarity would be better to apply for user's historic data
        - We compute the cosiine similarity of all books
        - We know that user liked book "i"
        - We have the matrix cos[i] and obtain which are the most similar ones
    * 
"""