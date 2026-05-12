import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import json
import re
from datetime import datetime


os.makedirs("data/raw", exist_ok=True)


TARGET_BOOKS = 4000   

# Browser headers - makes scraper look like a real browser
HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Checkpoint file 
CHECKPOINT = "data/raw/goodreads_indian_checkpoint.json"
OUTPUT_CSV = "data/raw/goodreads_indian.csv"

# Indian book lists on Goodreads 
LISTS = [
    # ── Main Indian literature lists ──────────────────────────────
    "https://www.goodreads.com/list/show/6590.Best_Indian_Literature",
    "https://www.goodreads.com/list/show/11290.100_Must_Read_Indian_Novels",
    "https://www.goodreads.com/list/show/3652.Best_Indian_Novels",
    "https://www.goodreads.com/list/show/32339.Best_South_Asian_Fiction",
    "https://www.goodreads.com/list/show/9809.Best_Indian_Fiction_in_English",
    "https://www.goodreads.com/list/show/5670.Best_Books_Set_in_India",
    "https://www.goodreads.com/list/show/107489.Best_Books_by_Indian_Authors",
    "https://www.goodreads.com/list/show/8482.Best_of_Indian_English_Writing",
    "https://www.goodreads.com/list/show/19650.Best_Historical_Fiction_set_in_India",
    "https://www.goodreads.com/list/show/24745.Indian_Mythology_and_Folklore",
    "https://www.goodreads.com/list/show/69279.Indian_Regional_Literature",

    # ── Regional language lists ────────────────────────────────────
    "https://www.goodreads.com/list/show/142441.Best_Malayalam_Novels",
    "https://www.goodreads.com/list/show/15654.Tamil_Literature",
    "https://www.goodreads.com/list/show/44498.Best_Hindi_Novels",
    "https://www.goodreads.com/list/show/16204.Best_Urdu_Literature",
    "https://www.goodreads.com/list/show/25370.Bengali_Literature",

    # ── Goodreads shelves  ─────────────────────
    "https://www.goodreads.com/shelf/show/indian-literature",
    "https://www.goodreads.com/shelf/show/india",
    "https://www.goodreads.com/shelf/show/malayalam",
    "https://www.goodreads.com/shelf/show/tamil-literature",
    "https://www.goodreads.com/shelf/show/hindi-literature",
    "https://www.goodreads.com/shelf/show/bengali-literature",
    "https://www.goodreads.com/shelf/show/kannada",
    "https://www.goodreads.com/shelf/show/telugu",
    "https://www.goodreads.com/shelf/show/marathi",
    "https://www.goodreads.com/shelf/show/gujarati-literature",
    "https://www.goodreads.com/shelf/show/urdu-literature",
    "https://www.goodreads.com/shelf/show/indian-fiction",
    "https://www.goodreads.com/shelf/show/india-fiction",
    "https://www.goodreads.com/shelf/show/indian-mythology",
    "https://www.goodreads.com/shelf/show/indian-history",
    "https://www.goodreads.com/shelf/show/indian-authors",
    "https://www.goodreads.com/shelf/show/indian-english",
    "https://www.goodreads.com/shelf/show/kerala",
    "https://www.goodreads.com/shelf/show/partition-india",
]



def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")



#  Get book URLs from a list/shelf page


def get_book_urls(list_url, max_pages=10):
    """
    Opens a Goodreads list or shelf page and collects all book URLs.
    max_pages = how many pages of the list to go through.
    Each page has about 30 books.
    """
    urls = []

    for page in range(1, max_pages + 1):
        paged_url = f"{list_url}?page={page}"

        try:
            resp = requests.get(paged_url, headers=HEADERS, timeout=15)

            # 403 = blocked, 429 = too many requests — stop this list
            if resp.status_code == 403:
                log(f"  Blocked on {list_url.split('/')[-1]} — skipping")
                break
            if resp.status_code == 429:
                log(f"  Rate limited — sleeping 2 minutes")
                time.sleep(120)
                break
            if resp.status_code != 200:
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Goodreads uses "a.bookTitle" for book links
            links = soup.select("a.bookTitle")

            if not links:
                break  # no more pages

            for a in links:
                full_url = "https://www.goodreads.com" + a["href"]
                if full_url not in urls:
                    urls.append(full_url)

            # polite delay between list pages
            time.sleep(random.uniform(1.5, 2.5))

        except Exception as e:
            log(f"  Error on list page: {e}")
            break

    return urls

# Scrape one book page

def scrape_book(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)

        if resp.status_code == 429:
            log("  Rate limited — sleeping 3 minutes")
            time.sleep(180)
            return None
        if resp.status_code == 403:
            log("  Blocked — sleeping 5 minutes")
            time.sleep(300)
            return None
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "lxml")

        # ── title ───────────────────────────────────────────────────
        title = None
        title_el = soup.select_one("h1.Text__title1")
        if title_el:
            title = title_el.text.strip()

        # ── author ──────────────────────────────────────────────────
        author = None
        author_el = soup.select_one("span.ContributorLink__name")
        if author_el:
            author = author_el.text.strip()

        # ── rating ──────────────────────────────────────────────────
        rating = None
        rating_el = soup.select_one("div.RatingStatistics__rating")
        if rating_el:
            try:
                rating = float(rating_el.text.strip())
            except:
                pass

        # skip if no title or rating
        if not title or not rating:
            return None

        # ── ratings count ───────────────────────────────────────────
        ratings_count = None
        rc_el = soup.select_one("span[data-testid='ratingsCount']")
        if rc_el:
            try:
                clean = rc_el.text.replace(",","").replace("ratings","").strip()
                ratings_count = int(clean.split()[0])
            except:
                pass

        # ── reviews count (NEW) ─────────────────────────────────────
        reviews_count = None
        rv_el = soup.select_one("span[data-testid='reviewsCount']")
        if rv_el:
            try:
                clean = rv_el.text.replace(",","").replace("reviews","").strip()
                reviews_count = int(clean.split()[0])
            except:
                pass

        # ── pages ───────────────────────────────────────────────────
        pages = None
        pages_el = soup.select_one("p[data-testid='pagesFormat']")
        if pages_el:
            try:
                pages = int(pages_el.text.strip().split()[0])
            except:
                pass

        # ── year ────────────────────────────────────────────────────
        year = None
        pub_el = soup.select_one("p[data-testid='publicationInfo']")
        if pub_el:
            yr = re.search(r"\d{4}", pub_el.text)
            if yr:
                year = int(yr.group())

        # ── genre ───────────────────────────────────────────────────
        genre = None
        genre_els = soup.select("span.BookPageMetadataSection__genreButton")
        if genre_els:
            genre = ", ".join([g.text.strip() for g in genre_els[:3]])

        # ── language  ──────────────────────────────────────────
        language = None
        detail_items = soup.select("div.DescListItem")
        for item in detail_items:
            label = item.select_one("dt")
            value = item.select_one("dd")
            if label and value and "language" in label.text.lower():
                language = value.text.strip()
                break

        # ── publisher ───────────────────────────────────────────────
        publisher = None
        pub_details = soup.select("div.BookDetails div.TruncatedContent__text")
        for detail in pub_details:
            text = detail.text.strip()
            if any(w in text.lower() for w in
                   ["publish","press","books","house","publications"]):
                publisher = text[:100]
                break
        if not publisher:
            pb_el = soup.select_one("div[data-testid='publicationInfo']")
            if pb_el:
                publisher = pb_el.text.strip()[:100]

        # ── description ─────────────────────────────────────────────
        description = None
        desc_el = soup.select_one(
            "div.BookPageMetadataSection__description span.Formatted"
        )
        if desc_el:
            description = desc_el.text.strip()[:200]

        return {
            "title":          title,
            "author":         author,
            "genre":          genre,
            "pages":          pages,
            "rating":         rating,
            "ratings_count":  ratings_count,
            "reviews_count":  reviews_count,  # NEW
            "year":           year,
            "publisher":      publisher,
            "language":       language,        # NEW
            "description":    description,
        }

    except Exception as e:
        return None

#  Save checkpoint


def save_checkpoint(books, scraped_urls):
    """Save progress to JSON so we can resume if crashed"""
    with open(CHECKPOINT, "w") as f:
        json.dump({
            "books":   books,
            "scraped": list(scraped_urls)
        }, f)



# MAIN SCRIPT

if __name__ == "__main__":

    log("=" * 55)
    log("Goodreads Indian Books Scraper")
    log(f"Target: {TARGET_BOOKS:,} books")
    log("=" * 55)

    # ──  Collect all book URLs from lists ───────────────────
    log("\nPhase 1: Collecting book URLs from lists...")

    all_urls  = []
    seen_urls = set()

    for i, list_url in enumerate(LISTS):
        list_name = list_url.split("/")[-1]
        log(f"  [{i+1}/{len(LISTS)}] {list_name}")

        urls     = get_book_urls(list_url, max_pages=10)
        new_urls = [u for u in urls if u not in seen_urls]
        seen_urls.update(new_urls)
        all_urls.extend(new_urls)

        log(f"  +{len(new_urls)} new URLs | total: {len(all_urls)}")

        # polite delay between lists
        time.sleep(random.uniform(1.5, 3.0))

    log(f"\nTotal unique book URLs found: {len(all_urls)}")

    # ──  Resume from checkpoint if it exists ────────────────
    books       = []
    scraped_urls = set()

    if os.path.exists(CHECKPOINT):
        log(f"\nFound checkpoint — resuming...")
        with open(CHECKPOINT) as f:
            state = json.load(f)
        books        = state["books"]
        scraped_urls = set(state["scraped"])

        # remove already-scraped URLs from queue
        all_urls = [u for u in all_urls if u not in scraped_urls]

        rated = sum(1 for b in books if b.get("rating"))
        log(f"Already scraped: {len(books):,} books ({rated:,} rated)")
        log(f"Remaining URLs:  {len(all_urls):,}")
    else:
        log("\nStarting fresh scrape...")

    # ──  Scrape each book page ──────────────────────────────
    log(f"\nPhase 2: Scraping {len(all_urls):,} book pages...")
    log("(Press Ctrl+C anytime to stop — progress is saved)\n")

    failed = 0

    for i, url in enumerate(all_urls):

        # stop when target reached
        if len(books) >= TARGET_BOOKS:
            log(f"Target of {TARGET_BOOKS:,} books reached!")
            break

        # scrape the book
        data = scrape_book(url)

        if data:
            books.append(data)
            scraped_urls.add(url)
        else:
            failed += 1

        # progress update every 50 books
        if (i + 1) % 50 == 0:
            rated = sum(1 for b in books if b.get("rating"))
            log(
                f"[{i+1:,}] scraped: {len(books):,} | "
                f"rated: {rated:,} | "
                f"failed: {failed} | "
                f"rating%: {round(rated / max(len(books), 1) * 100, 1)}%"
            )

        # save checkpoint every 200 books
        if (i + 1) % 200 == 0:
            save_checkpoint(books, scraped_urls)
            log(f"  💾 Checkpoint saved ({len(books):,} books so far)")

        # ── POLITE DELAY — critical for legal/ethical scraping ──────
        # random 2.5-4.5 seconds between each request
        # this ensures we don't overload Goodreads servers
        time.sleep(random.uniform(2.5, 4.5))

    # ──  Save final checkpoint and CSV ───────────────────────
    save_checkpoint(books, scraped_urls)

    df = pd.DataFrame(books)

    # remove duplicates
    before = len(df)
    df.drop_duplicates(subset=["title", "author"], keep="first", inplace=True)
    df.reset_index(drop=True, inplace=True)
    log(f"\nRemoved {before - len(df)} duplicates")

    # save CSV
    df.to_csv(OUTPUT_CSV, index=False)

    # ── Summary ──────────────────────────────────────────────────────
    log("\n" + "=" * 55)
    log("SCRAPING COMPLETE")
    log("=" * 55)
    log(f"Total books:    {len(df):,}")
    log(f"Rated:          {df['rating'].notna().sum():,} ({round(df['rating'].notna().sum()/len(df)*100,1)}%)")
    log(f"With genre:     {df['genre'].notna().sum():,}")
    log(f"With pages:     {df['pages'].notna().sum():,}")
    log(f"With year:      {df['year'].notna().sum():,}")
    log(f"\nNull counts:")
    log(str(df.isnull().sum()))
    log(f"\n Saved  {OUTPUT_CSV}")
