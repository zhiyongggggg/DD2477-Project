import os
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}
BOOK_LINKS_FILE = "./webscraper/output/book_links_30k.txt"
OUTPUT_FILE = "./webscraper/output/books_bulk.jsonl"
MAX_RETRIES = 2
RETRY_DELAY = 1.0
NUM_THREADS = 6
BATCH_SIZE = 50

with open(BOOK_LINKS_FILE, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]
print(f"Loaded {len(urls)} book URLs.")

def scrape_book(index, url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                time.sleep(RETRY_DELAY)
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            title = soup.find("h1", {"data-testid": "bookTitle"})
            description_block = soup.find("div", class_="DetailsLayoutRightParagraph")
            description = (description_block.find("span", class_="Formatted").text.strip()
                           if description_block and description_block.find("span", class_="Formatted")
                           else "Description not found")
            genres = [g.find("span", class_="Button__labelItem").text.strip()
                      for g in soup.find_all("span", class_="BookPageMetadataSection__genreButton")
                      if g.find("span", class_="Button__labelItem")]
            author_tag = soup.find("span", class_="ContributorLink__name", attrs={"data-testid": "name"})
            review_spans = soup.select("div.TruncatedContent__text span.Formatted")[:3] # get top 3 reviews
            reviews = [span.get_text(separator="\n").strip()[:200] for span in review_spans if span.get_text(strip=True)] # get first 200 chars in each review


            book_data = {
                "title": title.text.strip() if title else "Title not found",
                "author": author_tag.text.strip() if author_tag else "Author not found",
                "description": description,
                "genres": genres,
                "url": url,
                "reviews": reviews
            }

            action_line = json.dumps({ "index": { "_index": "books" } })
            doc_line = json.dumps(book_data, ensure_ascii=False)

            return f"{action_line}\n{doc_line}\n"

        except Exception:
            time.sleep(RETRY_DELAY)
    return None

buffer = []

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        tasks = [executor.submit(scrape_book, i, url) for i, url in enumerate(urls)]
        for i, future in enumerate(as_completed(tasks), 1):
            result = future.result()
            if result:
                buffer.append(result)
            if len(buffer) >= BATCH_SIZE:
                f.writelines(buffer)
                buffer.clear()
                print(f"[{i}/{len(urls)}] Processed")

    if buffer:
        f.writelines(buffer)

print(f"\nDone! Bulk-formatted book data saved to '{OUTPUT_FILE}'.")
