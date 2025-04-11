"""
This python script uses the link in book_lists.txt to scrape each category, retrieving the links of the books in the category.
Output: The output of this script is the book_lists.txt in the "output" folder.
"""

import os
import time
import requests
from bs4 import BeautifulSoup

MAX_PAGES = 10 # CHANGE THIS ACCORDINGLY

BASE_URL = "https://www.goodreads.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
}
LISTS_FILE = "./webscraper/output/book_lists.txt"
OUTPUT_FILE = "./webscraper/output/book_links.txt"
SLEEP = 1.0

if not os.path.exists(LISTS_FILE):
    raise FileNotFoundError(f"Missing required file: {LISTS_FILE}")

with open(LISTS_FILE, "r", encoding="utf-8") as f:
    list_pages = [line.strip() for line in f if line.strip()]

print(f"Loaded {len(list_pages)} list URLs.")

existing_links = set()
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        existing_links = set(line.strip() for line in f)

new_links_found = False

for i, list_url in enumerate(list_pages, start=1):
    print(f"\n[{i}/{len(list_pages)}] Scraping list: {list_url}")
    
    for page_num in range(1, MAX_PAGES + 1):
        page_url = f"{list_url}?page={page_num}"
        print(f"   Page {page_num}")

        try:
            res = requests.get(page_url, headers=HEADERS, timeout=10)
            if res.status_code != 200:
                print(f"    Page failed (status {res.status_code})")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            anchors = soup.find_all("a", class_="bookTitle")

            if not anchors:
                print("    No books found — moving to next list.")
                break

            links = {BASE_URL + a["href"] for a in anchors if "href" in a.attrs}
            new_links = links - existing_links

            if new_links:
                existing_links.update(new_links)
                new_links_found = True
                print(f"    Found {len(new_links)} new books (Total: {len(existing_links)})")

                # Save to file after each page
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    for link in sorted(existing_links):
                        f.write(link + "\n")

            time.sleep(SLEEP)

        except requests.RequestException as e:
            print(f"   Request error: {e}")
            break

print("\nDone scraping!")
print(f"Saved {len(existing_links)} unique book URLs to '{OUTPUT_FILE}'.")
