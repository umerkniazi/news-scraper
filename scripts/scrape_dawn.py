import os
import time
import requests
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser

# Config
BASE_URL = "https://www.dawn.com/news/{}"
REQUEST_DELAY = 0.05
MAX_NOT_FOUND = 50
COMMIT_EVERY = 50

# Database file
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_FILE = os.path.join(ROOT_DIR, "data", "dawn_news.db")
SOURCE_NAME = "dawn"

CATEGORY_KEYWORDS = {
    "pakistan", "world", "column", "editorial", "letters", "50-years-ago",
    "business", "sport", "sponsored", "culture", "tech", "front-page",
    "back-page", "national", "international"
}

def setup_db():
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)")
    conn.commit()
    return conn, cursor

def get_starting_point(cursor):
    cursor.execute("SELECT value FROM progress WHERE key = 'last_id'")
    row = cursor.fetchone()
    start_id = int(row[0]) + 1 if row else 1

    cursor.execute("SELECT id FROM articles WHERE source = ?", (SOURCE_NAME,))
    existing_ids = set(r[0] for r in cursor.fetchall())

    cursor.execute("SELECT value FROM progress WHERE key = 'total_articles'")
    row = cursor.fetchone()
    total_articles = int(row[0]) if row else 0

    return start_id, existing_ids, total_articles

def update_progress(cursor, last_id, last_date, total):
    cursor.execute("""
        INSERT OR REPLACE INTO progress (key, value) VALUES
        ('last_id', ?), ('last_date', ?), ('total_articles', ?)
    """, (str(last_id), last_date or '', str(total)))

def parse_article(soup):
    body_tag = soup.find("body")
    if not body_tag:
        return None
    category = next((c for c in body_tag.get("class", []) if c in CATEGORY_KEYWORDS), None)
    article_tag = soup.find("article")
    if not article_tag:
        return None
    headline_tag = soup.find("a", class_="story__link") or soup.find(class_="story__title")
    title = headline_tag.get_text(strip=True) if headline_tag else None
    date_tag = soup.find(class_="timestamp--date")
    if date_tag:
        raw_date = date_tag.get_text(strip=True)
        try:
            date = datetime.strptime(raw_date, "%B %d, %Y").date().isoformat()
        except ValueError:
            try:
                date = date_parser.parse(raw_date).date().isoformat()
            except Exception:
                date = None
    else:
        date = None
    story_content = soup.find(class_="story__content")
    p_tags = story_content.find_all("p") if story_content else []
    summary = p_tags[0].get_text(strip=True) if p_tags else ""
    full_text = "\n".join(p.get_text(strip=True) for p in p_tags[1:]) if p_tags else ""
    return title, date, summary, category, full_text

def main():
    conn, cursor = setup_db()
    start_id, existing_ids, total_articles = get_starting_point(cursor)
    print(f"Starting scraping from article ID {start_id} for '{SOURCE_NAME}'.")

    session = requests.Session()
    # Generic browser User-Agent
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/116.0.0.0 Safari/537.36"
    })

    article_id = start_id
    consecutive_not_found = 0
    batch_data = []
    last_date = None

    try:
        while True:
            if article_id in existing_ids:
                print(f"Article {article_id} already in DB, skipping.")
                article_id += 1
                continue

            url = BASE_URL.format(article_id)
            try:
                r = session.get(url, timeout=10)
            except requests.RequestException:
                print(f"Request failed for article {article_id}, retrying...")
                time.sleep(2)
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
            parsed = parse_article(soup)
            if not parsed:
                print(f"No article content found for ID {article_id}, skipping.")
                article_id += 1
                continue

            title, date, summary, category, full_text = parsed
            last_date = date
            batch_data.append((article_id, title, date, summary, category, full_text, url, SOURCE_NAME))
            existing_ids.add(article_id)
            total_articles += 1

            print(f"Saved article {article_id} | Category: {category} | Title: {title}")

            if len(batch_data) >= COMMIT_EVERY:
                cursor.executemany("""
                    INSERT OR REPLACE INTO articles
                    (id, title, date, summary, category, full_text, url, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, batch_data)
                update_progress(cursor, article_id, last_date, total_articles)
                conn.commit()
                batch_data.clear()

            article_id += 1
            time.sleep(REQUEST_DELAY)

    finally:
        if batch_data:
            cursor.executemany("""
                INSERT OR REPLACE INTO articles
                (id, title, date, summary, category, full_text, url, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch_data)
            update_progress(cursor, article_id - 1, last_date, total_articles)
            conn.commit()
        conn.close()
        print(f"Scraping finished for '{SOURCE_NAME}'.")

if __name__ == "__main__":
    main()
