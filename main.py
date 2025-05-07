from elasticsearch import Elasticsearch, helpers
import psycopg2
from datetime import datetime
import hashlib
import json
import scoring_algorithm
from Query import Query
import re

# Constants
RETRIEVAL_SIZE = 40
INDEX_NAME = "goodread" # REPLACE HERE
#INDEX_NAME = "books_30k"
USER_ID = None
INPUT_FILE = "cleaned_books_bulk_30k.jsonl"


# Elasticsearch config
es = Elasticsearch(
    "http://localhost:9200",
    api_key="Y25wVmdaWUJkODhDUmtTa0l0OXQ6RTNrVDdiVl9SYldHdmFLaUVtdkMzZw==" # REPLACE HERE
    #api_key="Z0oyUlE1WUJ0N1duRy1Jd2VLTG86VjB6RkVCazBTSkZXSHd1NTAzbWo1dw==" 
)

# PostgreSQL config
conn = psycopg2.connect(
    dbname="books_db",
    user="user",
    password="password",
    host="127.0.0.1",
    port="5432"
)
cursor = conn.cursor()

"""
    Searches
"""
def calculate_term_frequency(current_query, past_queries):
    current_terms = set(current_query.lower().split())
    term_frequency = {}


    for query in past_queries:
        past_terms = set(query[0].lower().split())  
        common_terms = current_terms.intersection(past_terms)  

     
        for term in common_terms:
            if term in term_frequency:
                term_frequency[term] += 1
            else:
                term_frequency[term] = 1

    return term_frequency

def generic_search(query_text, sia):

    reviews_flag = True
    historic_flag = True
    read_books_flag = True 

    cursor.execute("SELECT query FROM search_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT 5", (USER_ID,))
    rows = cursor.fetchall()

    # Start of the block that takes historical data into the query
    past_queries_raw = [row[0] for row in rows]
    tag_pattern = re.compile(r'^\[(?:generic|author|title|desc)\]\s*')
    past_queries = [tag_pattern.sub("", tag) for tag in past_queries_raw]

    historical_text = " ".join(past_queries)

    # Get read books
    book_genres = set()
    cursor.execute("SELECT title FROM books_read WHERE user_id = %s", (str(USER_ID),))
    read_rows = cursor.fetchall()
    read_books = [row[0] for row in read_rows]
    for b in read_books:
        current_book_genre = get_book_genre(b)
        for genre in current_book_genre:
            book_genres.add(genre)
    read_books_genres = " ".join(book_genres)
    
    es_query = {
      "bool": {
        "should": [
          {   # current query — full weight
            "multi_match": {
              "query":   query_text,
              "fields":  ["title^2","author^1.5","description^1"],
              "type":    "best_fields",
              "tie_breaker": 0.3,
              "boost":   1.0
            }
          }#
        ]
      }
    }

    if historic_flag and historical_text.strip():
        es_query["bool"]["should"].append({
            "multi_match": {
                "query": historical_text,
                "fields": ["title^1.5", "author^1.125", "description^0.75"],
                "type": "best_fields",
                "tie_breaker": 0.3,
                "boost": 1.0
            }
        })

    if read_books_flag and read_books_genres.strip():
        es_query["bool"]["should"].append({
            "multi_match": {
                "query": read_books_genres,
                "fields": ["title^1", "author^0.75", "description^0.5"],
                "type": "best_fields",
                "tie_breaker": 0.3,
                "boost": 1.0
            }
        })

    """
    term_frequency = calculate_term_frequency(query_text, past_queries)
    
    query = {
        "multi_match": {
            "query": query_text,  
            "fields": ["title^2", "author^1.5", "description^1"],  
            "type": "best_fields"
        }
    }

    for term, freq in term_frequency.items():
        if freq > 0:
            query["multi_match"]["fields"].append(f"title^{freq * 1.5}")

    """

    print("TOKENS FROM SEARCH HISTORY:", historical_text)
    res = es.search(
        index=INDEX_NAME,
        query=es_query,
        size=RETRIEVAL_SIZE
    )

    
    if not res:
        print("No results found for that query.")
        return

    ranking = ranking_algorithm(res, query_text, sia, reviews = reviews_flag)
    sorted_results = ranking[0]
    review_books = ranking[1]
    log_search_query(USER_ID, f"[generic] {query_text}")
    print("\n====================================================")
    print("|                Generic Search Results            |")
    print("====================================================")
    for i, book in enumerate(sorted_results):
        #print(f"{book[0]}*{book[1]:.2f}*{review_books[book[0]]}")
        print(f"{i+1: }{book[0]}")
    

def search_by_author(author_name):
    res = es.search(index=INDEX_NAME, query={"match": {"author": author_name}}, size=RETRIEVAL_SIZE)
    hits = res["hits"]["hits"]
    if hits:
        print("\n====================================================")
        print("|                 Books by Author                  |")
        print("====================================================")
        for i, hit in enumerate(hits, 1):
            print(f"{i}. {hit['_source'].get('title', 'No Title')} by {hit['_source'].get('author')}")
        log_search_query(USER_ID, f"[author] {author_name}")
    else:
        print("No books found by that author.")

def get_book_genre(title):
    res = es.search(index=INDEX_NAME, query={"match": {"title": title}}, size=1)
    return res["hits"]["hits"][0]["_source"]["genres"]

"""
    Adding into Database
"""
def book_exists(title):
    res = es.search(index=INDEX_NAME, query={"match": {"title": title}}, size=1)
    return bool(res["hits"]["hits"])

def add_read_book(title):
    if book_exists(title):
        cursor.execute("INSERT INTO books_read (user_id, title) VALUES (%s, %s)", (USER_ID, title))
        conn.commit()
        print(f"'{title}' has been added to your read books list.")
    else:
        print(f"Book titled '{title}' not found in the database.")

def log_search_query(user_id, query):
    print(f"Logging query: {query} for user {user_id}")  
    cursor.execute("""
        INSERT INTO search_history (user_id, query)
        VALUES (%s, %s)
    """, (user_id, query))
    conn.commit()



"""
    Retrieving Information from Database
"""
def retrieve_user_information(user_id):
    cursor.execute("SELECT title, timestamp FROM books_read WHERE user_id = %s ORDER BY timestamp DESC", (str(USER_ID),))
    read_books_rows = cursor.fetchall()
    cursor.execute("SELECT query, timestamp FROM search_history WHERE user_id = %s", (user_id,))
    past_queries_rows = cursor.fetchall()
    user_info = {
        "read_books": [
            {"title": title, "timestamp": timestamp.strftime('%Y-%m-%d %H:%M')}
            for title, timestamp in read_books_rows
        ],
        "search_queries": [
            {"query": query, "timestamp": timestamp.strftime('%Y-%m-%d %H:%M')}
            for query, timestamp in past_queries_rows
        ]
    }
    return user_info

def fetch_user_search_history(user_id):
    cursor.execute("SELECT query FROM search_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT 5", (user_id,))
    return cursor.fetchall()




"""
    Menu Options
"""
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register():
    print("\n====================================================")
    print("|                Register an Account               |")
    print("====================================================")
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    hashed = hash_password(password)

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        print("Registration successful. You can now log in.")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print("Username already exists. Try a different one.")

def login():
    global USER_ID
    print("\n====================================================")
    print("|                      Login                       |")
    print("====================================================")
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    hashed = hash_password(password)

    cursor.execute("SELECT id FROM users WHERE username = %s AND password = %s", (username, hashed))
    result = cursor.fetchone()

    if result:
        USER_ID = result[0]
        print(f"Login successful. Welcome back, {username}.")
        return True
    else:
        print("Invalid username or password.")
        return False

def view_read_books(user_id):
    cursor.execute("SELECT title, timestamp FROM books_read WHERE user_id = %s ORDER BY timestamp DESC", (str(USER_ID),))
    rows = cursor.fetchall()
    if rows:
        print("\n====================================================")
        print("|                  Your Read Books                  |")
        print("====================================================")
        for i, (title, timestamp) in enumerate(rows, 1):
            print(f"{i}. {title} (added on {timestamp.strftime('%Y-%m-%d %H:%M')})")
    else:
        print("You have not added any books yet.")

def user_menu():
    # Initialization Sentiment Analyzer
    sia = initializeLexicon()

    while True:
        print("\n====================================================")
        print("|                      Menu                        |")
        print("====================================================")
        print("1. Generic search")
        print("2. Search by author name")
        print("3. Add a book you've read")
        print("4. View your read books")
        print("5. Logout")
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            keyword = input("Generic search: ").strip()
            generic_search(keyword, sia)
        elif choice == "2":
            author = input("Enter the author's name: ").strip()
            search_by_author(author)
        elif choice == "3":
            title = input("Enter the title of the book you read: ").strip()
            add_read_book(title)
        elif choice == "4":
            
            output = retrieve_user_information(USER_ID)
            print("Books Read:")
            for book in output['read_books']:
                print(f"  - {book['title']} (at {book['timestamp']})")

            print("\nSearch History:")
            for query in output['search_queries']:
                print(f"  - \"{query['query']}\" at {query['timestamp']}")

        elif choice == "5":
            print("Logging out...\n")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 6.")    

def main():

    while True:
        print("\n====================================================")
        print("|              Welcome to Book Tracker             |")
        print("====================================================")
        print("1. Login")
        print("2. Register")
        print("3. Quit")
        choice = input("Select an option (1-3): ").strip()

        if choice == "1" and login():
            user_menu()
        elif choice == "2":
            register()
        elif choice == "3":
            print("Exiting program...")
            break
        else:
            print("Invalid option. Please choose 1, 2, or 3.")

def generate_bulk_actions(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        while True:
            action_line = f.readline()
            if not action_line:
                break
            doc_line = f.readline()
            if not doc_line:
                break
            try:
                action = json.loads(action_line)
                doc = json.loads(doc_line)
                yield {
                    "_index": INDEX_NAME,
                    "_source": doc
                }
            except json.JSONDecodeError:
                continue



def isDataBase(INPUT_FILE, INDEX_NAME):
    if not es.indices.exists(index=INDEX_NAME):
        print(f"Creating index '{INDEX_NAME}'...")
        helpers.bulk(es, generate_bulk_actions(INPUT_FILE))
        print(f"Index {INDEX_NAME} created and documents uploaded")
    else:
        print(f"Index {INDEX_NAME} already exists. Skipping bulp upload")


def get_docs_reviews(es_query_result, sia):
    docs = []
    reviews_books = dict()
    for hit in es_query_result["hits"]["hits"]:
        main_body_book = hit["_source"]
        title = main_body_book['title']
        reviews = main_body_book['reviews']
        docs.append(main_body_book)
        score_sentiment = scoring_algorithm.get_general_sentiment(sia, reviews)
        reviews_books[title] = score_sentiment
    return docs, reviews_books

def get_cosine_similarity_docs(queryText,docs):
    return scoring_algorithm.semanticScore(queryText,docs)

def add_reviews_factor(corpus, reviews_books, weight_factor = 0.2):
    final_recommendation = dict()
    for sim, score in corpus:
        title = sim['title']
        final_score = score + reviews_books[title] * score * weight_factor
        final_recommendation[title] = final_score
    
    sorted_results = sorted(final_recommendation.items(), key = lambda x: x[1], reverse=True)
    return sorted_results

def initializeLexicon():
    return scoring_algorithm.initializeLexicon()

def ranking_algorithm(es_query, queryText, sia, reviews = True):
    docs = []
    reviews_books = dict()
    #sia = scoring_algorithm.initializeLexicon()

    # Get the documents and the reviews per book 
    docs, reviews_books = get_docs_reviews(es_query, sia)

    # Then we perform cosine similarity in between the queryText and all the highest ranked documents
    similar = get_cosine_similarity_docs(queryText, docs)

    if reviews:
        sorted_results = add_reviews_factor(similar, reviews_books, 0.4)
    else:
        sorted_results = [(book['title'], score)for book, score in similar]

    
    return sorted_results, reviews_books
    


if __name__ == "__main__":
    # Make sure the input file in docker exists
    isDataBase(INPUT_FILE, INDEX_NAME)

    # Test the current ranking algorithm
    #queryText = 'Cowboys'
    #queryElastic = Query(queryText)

    # First we let Elastic Search use its scoring system "BM25" and get the highest ranked 30 results
    #res = es.search(index=INDEX_NAME, body=queryElastic.getQuery(), size=50)
    #sorted_results = ranking_algorithm(res, queryText, reviews = True)

    #print(sorted_results)

    main()