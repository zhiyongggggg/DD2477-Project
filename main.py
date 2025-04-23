from elasticsearch import Elasticsearch
import psycopg2
from datetime import datetime
import hashlib

# Constants
RETRIEVAL_SIZE = 10
INDEX_NAME = "test" # CHANGE YOUR INDEX NAME HERE
USER_ID = None

# Elasticsearch config
es = Elasticsearch(
    "http://localhost:9200",
    api_key="dkpKeVlwWUJJZTRQRk40S2pmMnM6UGlEQkJrcF93eVRHd0pSYnRaY1pUZw=="
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

def generic_search(query_text):
    cursor.execute("SELECT query FROM search_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT 5", (USER_ID,))
    past_queries = cursor.fetchall()

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

    res = es.search(
        index=INDEX_NAME,
        query=query,
        size=RETRIEVAL_SIZE
    )

    hits = res["hits"]["hits"]
    if hits:
        print("\n====================================================")
        print("|                Generic Search Results            |")
        print("====================================================")
        for i, hit in enumerate(hits, 1):
            print(f"{i}. {hit['_source'].get('title', 'No Title')} by {hit['_source'].get('author', 'Unknown Author')}")
        log_search_query(USER_ID, f"[generic] {query_text}")
    else:
        print("No results found for that query.")

def search_book(title):
    res = es.search(index=INDEX_NAME, query={"match": {"title": title}}, size=RETRIEVAL_SIZE)
    hits = res["hits"]["hits"]
    if hits:
        print("\n====================================================")
        print("|                  Search Results                  |")
        print("====================================================")
        for i, hit in enumerate(hits, 1):
            print(f"{i}. {hit['_source'].get('title', 'No Title')} by {hit['_source'].get('author', 'Unknown Author')}")
        log_search_query(USER_ID, title)
    else:
        print("No results found for that title.")

def search_by_description_keyword(keyword):
    res = es.search(index=INDEX_NAME, query={"match": {"description": keyword}}, size=RETRIEVAL_SIZE)
    hits = res["hits"]["hits"]
    if hits:
        print("\n====================================================")
        print("|      Books Matching Description or Review        |")
        print("====================================================")
        for i, hit in enumerate(hits, 1):
            print(f"{i}. {hit['_source'].get('title', 'No Title')}")
        log_search_query(USER_ID, f"[desc] {keyword}")
    else:
        print("No books found with that word in the description.")

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
    cursor.execute("SELECT title, timestamp FROM books_read WHERE user_id = %s ORDER BY timestamp DESC", (USER_ID,))
    read_books_rows = cursor.fetchall()
    cursor.execute("SELECT * FROM search_history WHERE user_id = %s", (user_id,))
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
    print(user_info)
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
    cursor.execute("SELECT title, timestamp FROM books_read WHERE user_id = %s ORDER BY timestamp DESC", (user_id,))
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
    while True:
        print("\n====================================================")
        print("|                      Menu                        |")
        print("====================================================")
        print("1. Generic search")
        print("2. Search for a book by title")
        print("3. Search for a keyword in description or reviews")
        print("4. Search by author name")
        print("5. Add a book you've read")
        print("6. View your read books")
        print("7. Logout")
        choice = input("Enter your choice (1-6): ").strip()

        if choice == "1":
            keyword = input("Generic search: ").strip()
            generic_search(keyword)
        if choice == "2":
            title = input("Enter the book title to search: ").strip()
            search_book(title)
        elif choice == "3":
            keyword = input("Enter a keyword to search in book descriptions and reviews: ").strip()
            search_by_description_keyword(keyword)
        elif choice == "4":
            author = input("Enter the author's name: ").strip()
            search_by_author(author)
        elif choice == "5":
            title = input("Enter the title of the book you read: ").strip()
            add_read_book(title)
        elif choice == "6":
            view_read_books(USER_ID)
            print(retrieve_user_information(USER_ID))
        elif choice == "7":
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

if __name__ == "__main__":
    main()
