# News Scraper (Work in Progress)

This is a personal project to scrape news articles for learning and practice purposes.  
Currently, it only scrapes articles from [Dawn](https://www.dawn.com) and stores them in an **SQLite** database.

## Status

Work in progress.  
Planned updates include:

- Adding more news sources
- Improving data storage and formatting
- Implementing filtering and categorization features

## Setup

Before running the scraper, install the Python packages required to run the scraper:

    pip install -r requirements.txt

This will install:

- `requests` for making HTTP requests
- `beautifulsoup4` for parsing HTML

For viewing and managing the SQLite databases, you can use [DB Browser for SQLite](https://sqlitebrowser.org/), which provides a simple graphical interface to explore your scraped data.

## Data Storage

Scraped articles are saved in the `data` folder as SQLite database files.  
The folder starts empty and will be filled when you run the scraper.  
You can open these database files with DB Browser for SQLite to browse, query and manage your scraped articles.

## Disclaimer

This project is for **educational purposes only**.  
Please respect each source’s terms of service and copyright rules.

## License

This project is licensed under the [MIT License](LICENSE).
