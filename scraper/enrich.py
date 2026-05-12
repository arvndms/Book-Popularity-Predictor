import requests
import pandas as pd
import time
import os
import json
 
os.makedirs("data/processed", exist_ok=True)
 

GOOGLE_API_KEY = "your_key_here"   
 

INPUT_FILE     = "data/raw/goodreads_indian.csv"
OUTPUT_FILE    = "data/raw/goodreads_enriched.csv"
CHECKPOINT     = "data/raw/enrichment_checkpoint.json"
 
# FETCH language + publisher from Google Books API
 
def fetch_language_publisher(title, author):
    """
    Search Google Books API by title + author.
    Returns language, publisher, price.
    Returns None, None, None if not found.
    """
    try:
        # clean author — use first name only for better matching
        first_author = str(author).split(",")[0].strip()
        query = f"intitle:{title} inauthor:{first_author}"
 
        params = {
            "q":          query,
            "maxResults": 1,
            "printType":  "books",
            "key":        GOOGLE_API_KEY
        }
 
        resp = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params=params,
            timeout=10
        )
 
        # handle quota exceeded
        if resp.status_code == 429:
            print("  Daily quota hit — stopping for today")
            return "QUOTA_HIT", None, None
 
        if resp.status_code != 200:
            return None, None, None
 
        items = resp.json().get("items", [])
        if not items:
            return None, None, None
 
        info = items[0].get("volumeInfo", {})
        sale = items[0].get("saleInfo",   {})
 
        language  = info.get("language")
        publisher = info.get("publisher")
 
        # price — only available for ebooks on Google Play
        price = None
        if sale.get("saleability") == "FOR_SALE":
            price = sale.get("listPrice", {}).get("amount")
 
        return language, publisher, price
 
    except Exception as e:
        return None, None, None
 
 

# MAIN
 
if __name__ == "__main__":
 
    # Load Goodreads data
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded: {len(df):,} books")
    print(f"Language null:  {df['language'].isna().sum()}")
    print(f"Publisher null: {df['publisher'].isna().sum()}")
 
    # Resume from checkpoint if exists
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT) as f:
            checkpoint = json.load(f)
        enriched_dict = checkpoint["enriched"]
        print(f"\nResuming — {len(enriched_dict):,} already done")
    else:
        enriched_dict = {}
        print("\nStarting fresh enrichment...")
 
    # Process each book
    print(f"\nFetching language + publisher from Google Books API...")
    print(f"(runs at ~0.3s per book — ~20 mins for 3,965 books)\n")
 
    quota_hit = False
 
    for i, (idx, row) in enumerate(df.iterrows()):
 
        title = str(row["title"])
 
        # skip if already done
        if title in enriched_dict:
            continue
 
        # fetch from Google Books
        lang, pub, price = fetch_language_publisher(
            title, row.get("author", "")
        )
 
        # stop if quota hit
        if lang == "QUOTA_HIT":
            print(f"\nQuota hit at row {i+1} — run again tomorrow to continue")
            quota_hit = True
            break
 
        # store result
        enriched_dict[title] = {
            "language":  lang,
            "publisher": pub,
            "price":     price,
        }
 
        # progress every 100 books
        if (i + 1) % 100 == 0:
            filled_lang  = sum(1 for v in enriched_dict.values() if v["language"])
            filled_pub   = sum(1 for v in enriched_dict.values() if v["publisher"])
            filled_price = sum(1 for v in enriched_dict.values() if v["price"])
            print(f"[{i+1:,}/{len(df):,}] "
                  f"language: {filled_lang:,} | "
                  f"publisher: {filled_pub:,} | "
                  f"price: {filled_price:,}")
 
            # save checkpoint
            with open(CHECKPOINT, "w") as f:
                json.dump({"enriched": enriched_dict}, f)
 
        time.sleep(0.3)   #  delay
 
    #  Save final checkpoint 
    with open(CHECKPOINT, "w") as f:
        json.dump({"enriched": enriched_dict}, f)
 
    # Apply enriched data back to dataframe 
    print("\nApplying enriched data to dataset...")
 
    languages  = []
    publishers = []
    prices     = []
 
    for _, row in df.iterrows():
        title   = str(row["title"])
        enriched = enriched_dict.get(title, {})
        languages.append(enriched.get("language"))
        publishers.append(enriched.get("publisher"))
        prices.append(enriched.get("price"))
 
    df["language"]  = languages
    df["publisher"] = publishers
    df["price"]     = prices
