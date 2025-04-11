"""
This python script scrapes the "popular list" page on GoodRead and retrieves the links of the category.
Output: The output of this script is the book_lists.txt in the "output" folder.
"""

import requests
import time
from bs4 import BeautifulSoup

LIST_PAGE_RANGE = range(1, 20) # CHANGE THIS ACCORDINGLY

BASE_URL = "https://www.goodreads.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}
SLEEP = 2
OUTPUT_FILE = "./webscraper/output/book_lists.txt"

list_urls = set()



for page_number in LIST_PAGE_RANGE:
    print(f"Fetching list page {page_number}...")

    try:
        response = requests.get(f"{BASE_URL}/list/popular_lists?page={page_number}", headers=HEADERS)
        if response.status_code != 200:
            print(f"Skipping page {page_number} (status {response.status_code})")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        anchors = soup.select("a.listTitle")

        for a in anchors:
            href = a.get("href")
            if href and href.startswith("/list/show/"):
                full_url = BASE_URL + href
                list_urls.add(full_url)

        time.sleep(SLEEP)

    except Exception as e:
        print(f"Error on page {page_number}: {e}")

# Save URLs to file
with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    for url in sorted(list_urls):
        file.write(url + "\n")

print(f"\nDone. Collected {len(list_urls)} list URLs and saved to '{OUTPUT_FILE}'.")
