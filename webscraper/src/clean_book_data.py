import json

INPUT_FILE = "./webscraper/output/books_bulk.jsonl"
OUTPUT_FILE = "./webscraper/output/cleaned_books_bulk_30k.jsonl"

with open(INPUT_FILE, "r", encoding="utf-8") as infile, open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    counter = 0
    while True:
        counter += 1
        if counter % 100 == 0:
            print(counter)
        action_line = infile.readline()
        if not action_line:
            break  # EOF

        doc_line = infile.readline()
        if not doc_line:
            break  # Incomplete pair

        try:
            doc = json.loads(doc_line)
            if doc.get("title") != "Title not found":
                outfile.write(action_line)
                outfile.write(doc_line)
        except json.JSONDecodeError:
            continue  # Skip malformed entries
