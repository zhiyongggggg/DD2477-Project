from elasticsearch import Elasticsearch

es = Elasticsearch(
    "http://localhost:9200",
    api_key="WlZ0X0lKWUJSOFAweXR2MEd2TnU6enVUUVIxYk9TbmlGVlVvc1Fub3g1QQ=="
    
)

doc = {
    "title": "Introduction to Distributed Systems",
    "author": "John Doe",
    "year": 2023
}

# Index it (auto-generates a document ID)
response = es.index(index="goodread", document=doc)

res = es.search(index="goodread", query={"match_all": {}})
print(res["hits"]["hits"])
