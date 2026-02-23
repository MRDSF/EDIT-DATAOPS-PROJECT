import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import csv
from pathlib import Path

URL = "https://euronews.com/search?query=tesla"


def scraper():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=opts)

    rows = []
    seen = set()

    i = 1
    while i < 30:
        if i == 1:
            driver.get(URL)
        else:
            driver.get(f"{URL}&p={i}") 

        time.sleep(10)  # wait for the page to fully load
        articles = driver.find_elements(By.CSS_SELECTOR, "article")
        for art in articles:
            try:
                
                a = art.find_elements(By.CSS_SELECTOR, "a.the-media-object__link") # find_elements returns a list and doesn't raise an error if not found
                title_class = art.find_elements(By.CSS_SELECTOR, "h2.the-media-object__title") 
                date_class = art.find_elements(By.CSS_SELECTOR, "div.the-media-object__date[data-timestamp]") 

                if not a or not title_class or not date_class:
                    continue
                
                href = a[0].get_attribute("href") # [0] because find_elements returns a list
                title = title_class[0].text.strip() # returns the h2 web element and we get its text
                ts = int(date_class[0].get_attribute("data-timestamp")) # returns the div web element and we get the data-timestamp attribute
                date = datetime.utcfromtimestamp(ts).isoformat()

                if not href or not title or not date:
                    continue
                
                tl = title.lower()
                if ("tesla" not in tl) and ("elon" not in tl) and ("musk" not in tl):
                    continue

                if href in seen: # evitar duplicados
                    continue
                seen.add(href)

                rows.append((date, title, href))


            except Exception as e:
                print("Error:", e)
                continue

        i+=1
        
    driver.quit()

    for date, title, href in rows:
        print(date)
        print(title)
        print(href)
        print("-" * 80)

    return rows

def save_to_csv(news):
    base_path = Path("data/tesla_news")
    base_path.mkdir(parents=True, exist_ok=True)

    open_files = {}   # (year, month) -> file handle
    writers = {}      # (year, month) -> csv.writer

    try:
        for date, title, link in news:
            date = datetime.fromisoformat(date).date()
            key = (date.year, date.month) # key to identify the file (year, month)

            if key not in open_files: # if the file for this month hasn't been opened yet, open it and create the writer
                filename = f"euronews_{key[0]}_{key[1]:02d}.csv" 
                path = base_path / filename # full file path
                is_new = not path.exists()

                f = open(path, "a", newline="", encoding="utf-8")
                w = csv.writer(f) # create the writer for this file
                if is_new:
                    w.writerow(["date", "title", "link", "source"]) # write the header only if the file is new

                open_files[key] = f # store the file handle to close later
                writers[key] = w # store the writer to write data

            writers[key].writerow([date, title, link, "euronews"])  # write the data row using the writer for the article's year and month
    finally:
        # ensure all files are closed even if an error occurs
        for f in open_files.values():
            f.close()

if __name__ == "__main__":
    rows = scraper()
    save_to_csv(rows)