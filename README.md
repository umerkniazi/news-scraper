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

Before running the scraper, install the required Python packages:

    pip install -r requirements.txt

This will install:

- `requests` for making HTTP requests
- `beautifulsoup4` for parsing HTML

## Data Storage

Scraped articles are saved in the `data` folder as SQLite database files.  
The `data` folder is empty in the repo and will be populated when you run the script.

## Disclaimer

This project is for **educational purposes only**.  
I do not encourage or support misuse of the data. Please respect each source’s terms of service and copyright rules.

## License

This project is licensed under the [MIT License](LICENSE).
