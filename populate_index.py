from elasticsearch import Elasticsearch, helpers
import json

es = Elasticsearch(
    "http://localhost:9200",
    api_key="Y25wVmdaWUJkODhDUmtTa0l0OXQ6RTNrVDdiVl9SYldHdmFLaUVtdkMzZw==" # REPLACE HERE
)

INPUT_FILE = "./webscraper/output/cleaned_books_bulk_30k.jsonl"
INDEX_NAME = "goodread"

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

helpers.bulk(es, generate_bulk_actions(INPUT_FILE))


res = es.search(
    index=INDEX_NAME,
    query={
        "match": {
            "title": "Harry Potter and the Half-Blood Prince"
        }
    },
    size=5
)
for hit in res["hits"]["hits"]:
    print(hit["_source"])
