import sqlite3
import pandas as pd
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'dawn_news.db')
conn = sqlite3.connect(db_path)

def get_articles_per_year():
    query = '''
        SELECT strftime('%Y', date) AS year, COUNT(*) AS total_articles
        FROM articles
        WHERE date BETWEEN '2001-01-01' AND '2025-12-31'
        GROUP BY year
        ORDER BY year;
    '''
    df_yearly = pd.read_sql(query, conn)
    return df_yearly

def get_articles_per_category():
    query = '''
        SELECT category, COUNT(*) AS total_articles
        FROM articles
        GROUP BY category
        ORDER BY total_articles DESC;
    '''
    df_category = pd.read_sql(query, conn)
    return df_category

def get_total_articles():
    query = '''
        SELECT COUNT(*) AS total_articles
        FROM articles;
    '''
    total_articles = pd.read_sql(query, conn)
    return total_articles.iloc[0, 0]

def main():
    articles_per_year = get_articles_per_year()
    articles_per_category = get_articles_per_category()
    total_articles = get_total_articles()

    print("Total Articles: ", total_articles)
    print("\nArticles Per Year:")
    print(articles_per_year)
    print("\nArticles Per Category:")
    print(articles_per_category)

if __name__ == '__main__':
    main()

conn.close()
