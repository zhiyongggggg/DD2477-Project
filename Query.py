"""

A Query class designed to make queries to Elastic Search easy to create, modify and call

*   There are methods implemented taken into account the documentation of the API. 
*   More methods will be added in the future
"""


from elasticsearch import Elasticsearch, helpers
import json

class Query:

    # Initializing query structure
    def __init__(self, title, numericFieldRanking=None):
        self.title = title
        self.query = dict()
        self.numericFieldRanking = numericFieldRanking
        self.factorNumericField = 1
        self.missingDocVal = 1
        self.createQuery()
    
    def createQuery(self):
        if self.numericFieldRanking == None:
            self.query = {
                "query": {
                    "function_score":{
                        "query":{
                            "match": {
                                "title": self.title
                            }
                        }
                    }
                }
            }
        else:
            self.query = {
                "query": {
                    "function_score":{
                        "query":{
                            "match": {
                                "title": self.title,
                                "content": self.title
                            }
                        },
                        "field_value_factor":{
                            "field": self.numericFieldRanking,
                            "factor": self.factorNumericField,
                            "modifier": "sqrt",
                            "missing": self.missingDocVal
                        },
                        "boost_mode": "multiply"
                    }
                }
            }

    def printQuery(self):
        print(self.query)
    
    def getQuery(self):
        return self.query
    
    def setTitle(self, title):
        self.title = title