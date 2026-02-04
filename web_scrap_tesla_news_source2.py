import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import csv
from pathlib import Path

URL = "https://euronews.com/search?query=tesla"

opts = Options()
opts.add_argument("--start-maximized")
driver = webdriver.Chrome(options=opts)

rows = []
seen = set()

def scraper():
    i = 1
    while i < 30:
        if i == 1:
            driver.get(URL)
        else:
            driver.get(f"{URL}&p={i}") 

        time.sleep(10)  # espera a página carregar completamente
        articles = driver.find_elements(By.CSS_SELECTOR, "article")
        for art in articles:
            try:
                
                a = art.find_elements(By.CSS_SELECTOR, "a.the-media-object__link") # find_elements retorna uma lista e nao da erro se nao encontrar
                title_class = art.find_elements(By.CSS_SELECTOR, "h2.the-media-object__title") 
                date_class = art.find_elements(By.CSS_SELECTOR, "div.the-media-object__date[data-timestamp]") 

                if not a or not title_class or not date_class:
                    continue
                
                href = a[0].get_attribute("href") # o [0] é pq o find_elements retorna uma lista
                title = title_class[0].text.strip() # devolve webelement h2 e pegamos o texto
                ts = int(date_class[0].get_attribute("data-timestamp")) # devolve o webelement div e pegamos o atributo data-timestamp
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
                print("Erro:", e)
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
    path = Path("data/tesla_news/euronews.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # cabeçalho
        writer.writerow(["date", "title", "link", "source"])

        # dados
        for date, title, link in news:
            writer.writerow([date, title, link, "euronews"])

if __name__ == "__main__":
    rows = scraper()
    save_to_csv(rows)