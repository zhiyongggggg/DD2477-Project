# Goodreads Web Scraper & Elasticsearch Indexer

This project scrapes book data from Goodreads and imports it into an Elasticsearch index.

---

## Getting Started

### Step 1: Setting up Kibana

1. Make sure you have docker downloaded.
2. Run the following command in your terminal, this will fetch the docker image. **IMPORTANT:** Take note of the username and password once this curl completes. Save it somewhere so you will have access to it later.
```bash
curl -fsSL https://elastic.co/start-local | sh
```
3. Once the container is running, you can open Kibana at: [http://localhost:5601](http://localhost:5601)

### Step 2: Generate an API Key in Kibana

1. Open Kibana at: [http://localhost:5601](http://localhost:5601)
2. In the search bar at the top, search for "Dev Tools" and open it.
3. Paste the code below into the console and click Run to create an API key with full access:

```json
POST /_security/api_key
{
  "name": "full-access-api-key",
  "role_descriptors": {
    "full_access": {
      "cluster": ["all"],
      "index": [
        {
          "names": ["*"],
          "privileges": ["all"]
        }
      ]
    }
  }
}
```

4. Paste the API key into populate_index.py on line 6.
5. Next, we create an index by running the following code in the same console.

```json
PUT /goodread
{
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "author": { "type": "text" },
      "description": { "type": "text" },
      "genres": { "type": "keyword" },
      "url": { "type": "keyword" },
      "reviews": { "type": "text"}
    }
  }
}
```

6. Install the necessary libraries: (use these version to ensure consistency)
```bash
pip install --upgrade elasticsearch==8.13.0 
pip install sentence-transformers
pip install psycopg2
pip install "numpy<2"
pip install nltk
```
7. Proceed to run the **populate_index.py** file after replacing the **API Key** and **INDEX_NAME**(by default it should be "goodread") with your own. This will import data into the index from our output folder.( Make sure to only execute this code once or there will be duplicate entries in the Index)
8. To view the index, in the search bar at the top, search for "Index Management" and open it.
9. Click into your index, and click on the "Discover Index" at the top right side to create a viewer in order to view the documents.
10. Insert any name you want for the viewer, for index patterns, make sure to input the name of your index.
11. After successful creation of viewer, you can click on Discover Index and it should display the documents.

### Step 3: Setting Up Local Postgres on Docker

1. To creates a new Postgres docker container and also creates the necessary tables which is used to store user information. Run the following:
```bash
docker-compose up --build
```

2. You can run the following code to access into the docker database. Once you are inside the database, you can run your raw SQL queries to view the database.
```bash
docker exec -it books_postgres psql -U user -d books_db
```

## The Search Engine (main.py)

### Step 1: Running the code

1. Run the **main.py** python file, everything should run as per expected.
2. Create an account in the terminal interface, and login with your credentials (Note: This is **NOT** a secure authentication system, your password will not be hashed, so please use a dummy password)
3. Follow the instructions on the terminal interface to query for books, add books read, and view user information.

## How the Web Scraper Works (For Reference Only – You Do Not Need to Run This)

The data collection process is divided into three automated scripts:

1. **`scrape_list_url.py`**  
   Scrapes Goodreads' **Popular Lists** page to collect URLs of various book categories.  
   - **Output:** `book_lists.txt`

2. **`scrape_book_links.py`**  
   Reads the category URLs from `book_lists.txt`, visits each list, and extracts individual book URLs.  
   - **Output:** `book_links.txt`

3. **`get_book_info.py`**  
   Uses the book URLs from `book_links.txt` to scrape detailed metadata for each book, including:  
   - Title  
   - Author  
   - Description  
   - Genres  
   - URL  
   - **Output:** A `books_bulk.jsonl` file formatted for bulk import into Elasticsearch.

4. **`clean_book_data.py`**  
   Cleans and removes the invalid rows in `books_bulk.jsonl`.
   - **Output:** `cleaned_books_bulk.jsonl`



