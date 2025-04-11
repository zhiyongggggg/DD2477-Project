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

4. Paste the API key into main.py on line 6.
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
    }
  }
}
```

6. Proceed to run the **main.py** file after you have pasted in your API Key. This will import data into the index from our output folder.
7. To view the index, in the search bar at the top, search for "Index Management" and open it.
8. Click into your index, and click on the "Discover Index" at the top right side to create a viewer in order to view the documents.
9. Insert any name you want for the viewer, for index patterns, make sure to input the name of your index.
10. After successful creation of viewer, you can click on Discover Index and it should display the documents.

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




