import os
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_FILE = os.path.join(ROOT_DIR, "data", "news_articles.db")
BASE_URL = "https://www.dawn.com/news/{}"
REQUEST_DELAY = 0.3
MAX_NOT_FOUND = 50

CATEGORY_KEYWORDS = {
    "pakistan", "world", "column", "editorial", "letters", "50-years-ago",
    "business", "sport", "sponsored", "culture", "tech", "front-page",
    "back-page", "national", "international"
}

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY,
    title TEXT,
    date TEXT,
    summary TEXT,
    category TEXT,
    full_text TEXT,
    url TEXT,
    source TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS progress (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
conn.commit()

cursor.execute("SELECT value FROM progress WHERE key = 'dawn_last_id'")
row = cursor.fetchone()
start_id = int(row[0]) + 1 if row else 1

cursor.execute("SELECT id FROM articles WHERE source = 'dawn'")
existing_ids = set(row[0] for row in cursor.fetchall())

session = requests.Session()
article_id = start_id
consecutive_not_found = 0
commit_every = 10
counter = 0

def update_progress(last_id, last_date, total):
    cursor.execute("""
        INSERT OR REPLACE INTO progress (key, value) VALUES
        ('dawn_last_id', ?), ('dawn_last_date', ?), ('dawn_total_articles', ?)
    """, (str(last_id), last_date or '', str(total)))

total_articles = 0
cursor.execute("SELECT value FROM progress WHERE key = 'dawn_total_articles'")
row = cursor.fetchone()
if row:
    total_articles = int(row[0])

print(f"Starting scraping from article ID {start_id}.")

while True:
    if article_id in existing_ids:
        print(f"Article {article_id} already in DB, skipping.")
        article_id += 1
        continue

    url = BASE_URL.format(article_id)
    try:
        r = session.get(url, timeout=10)
    except requests.RequestException:
        print(f"Request failed for article {article_id}, retrying after delay.")
        time.sleep(5)
        continue

    if r.status_code == 404:
        consecutive_not_found += 1
        print(f"Article {article_id} not found (404). Consecutive misses: {consecutive_not_found}")
        if consecutive_not_found >= MAX_NOT_FOUND:
            print(f"Stopped scraping after {MAX_NOT_FOUND} consecutive 404s.")
            break
        article_id += 1
        continue

    consecutive_not_found = 0
    soup = BeautifulSoup(r.text, "html.parser")

    body_tag = soup.find("body")
    if not body_tag:
        print(f"No body tag found for ID {article_id}, skipping.")
        article_id += 1
        continue

    classes = body_tag.get("class", [])
    category = None
    for c in classes:
        if c in CATEGORY_KEYWORDS:
            category = c
            break

    article_tag = soup.find("article")
    if not article_tag:
        print(f"No article tag found for ID {article_id}, skipping.")
        article_id += 1
        continue

    headline_tag = soup.find("a", class_="story__link")
    if not headline_tag:
        headline_tag = soup.find(class_="story__title")
    title = headline_tag.get_text(strip=True) if headline_tag else None

    date_tag = soup.find(class_="timestamp--date")
    if date_tag:
        raw_date = date_tag.get_text(strip=True)
        try:
            parsed_date = datetime.strptime(raw_date, "%B %d, %Y").date()
            date = parsed_date.isoformat()
        except ValueError:
            date = None
    else:
        date = None

    story_content = soup.find(class_="story__content")
    p_tags = story_content.find_all("p") if story_content else []
    if p_tags:
        summary = p_tags[0].get_text(strip=True)
        full_text = "\n".join(p.get_text(strip=True) for p in p_tags[1:])
    else:
        summary = None
        full_text = None

    cursor.execute("""
        INSERT OR REPLACE INTO articles (id, title, date, summary, category, full_text, url, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (article_id, title, date, summary, category, full_text, url, "dawn"))
    existing_ids.add(article_id)

    total_articles += 1
    counter += 1

    if counter % commit_every == 0:
        update_progress(article_id, date, total_articles)
        conn.commit()

    print(f"Saved article {article_id} with category: {category}")
    article_id += 1
    time.sleep(REQUEST_DELAY)

update_progress(article_id-1, date, total_articles)
conn.commit()
print("Scraping finished.")
conn.close()
