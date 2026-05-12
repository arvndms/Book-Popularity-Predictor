## WebScraper (Data Collection)

### Web Scraping
This project includes a Python-based web scraper that collects book metadata from publicly available pages on Goodreads. 
It gathers information such as title, author, ratings, genres, and publication details for books related to Indian literature.

The scraper works by iterating through curated book lists and extracting structured data from individual book pages. 
It includes rate limiting, retry handling, and checkpointing to ensure reliable large-scale data collection.

### Data Enrichment

The collected dataset is further enriched using the Google Books API to fill missing fields like language, publisher, and price . This improves data completeness and consistency
