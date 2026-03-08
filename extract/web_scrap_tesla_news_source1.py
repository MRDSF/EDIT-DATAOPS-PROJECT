import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
from pathlib import Path


BASE = "https://www.notateslaapp.com"

seen_links = set()
def get_page(page):
    url = f"{BASE}/?page={page}"
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")

    news = []
    
    articles = soup.select("article.news-item")

    for art in articles:
        a = art.select_one("h1 a")
        date_tag = art.select_one("p.date")

        if not a:
            continue

        title = a.text.strip()
        link = a["href"]
        date = date_tag.text.strip() if date_tag else ""
        date = date.replace("Updated: ","") # remove "Updated: " if present
        date_in_format = datetime.strptime(date, "%B %d, %Y").date()

        if link in seen_links:
            continue

        seen_links.add(link)

        news.append((title, link, date_in_format))

    return news



def run_scraper():
    all_news = []
    for page in range(1, 100):  # desired pages
        print(f"Página {page}")
        items = get_page(page)

        if not items:
            break

        all_news.extend(items) # Adds each element from another list. Unlike append which adds the list as a single element

    for title, link, date in all_news:
        print(date)
        print(title)
        print(link)
        print("-" * 80)
    
    return all_news

def save_to_csv(news):
    project_root = Path(__file__).resolve().parents[1] # get the project root directory (two levels up from the current file) [1] because we want the parent of the parent (the project root), not just the parent (the extract directory)
    base_path = project_root / "data" / "tesla_news"
    base_path.mkdir(parents=True, exist_ok=True)

    open_files = {}   # (year, month) -> file handle
    writers = {}      # (year, month) -> csv.writer
    existing_links = {}  # (year, month) -> set of existing links

    try:
        for title, link, date in news:
            key = (date.year, date.month) # key to identify the file (year, month)

            if key not in open_files: # if the file for this month hasn't been opened yet, open it and create the writer
                filename = f"notateslaapp_{key[0]}_{key[1]:02d}.csv" # e.g. file name in format notateslaapp_2024_06.csv
                path = base_path / filename # full file path
                is_new = not path.exists()

                links_for_month = set()
                if path.exists():
                    with open(path, "r", newline="", encoding="utf-8") as existing_file:
                        reader = csv.DictReader(existing_file)
                        for row in reader:
                            existing_link = row.get("link")
                            if existing_link:
                                links_for_month.add(existing_link)
                existing_links[key] = links_for_month

                f = open(path, "a", newline="", encoding="utf-8")
                w = csv.writer(f) # create the writer for this file
                if is_new:
                    w.writerow(["date", "title", "link", "source"]) # write the header only if the file is new

                open_files[key] = f # store the file handle to close later
                writers[key] = w # store the writer to write data

            if link in existing_links[key]:
                continue

            writers[key].writerow([date, title, link, "notateslaapp"])  # write the data row using the writer for the article's year and month
            existing_links[key].add(link)
    finally:
        # ensure all files are closed even if an error occurs
        for f in open_files.values():
            f.close()


if __name__ == "__main__":
    news = run_scraper()
    save_to_csv(news)