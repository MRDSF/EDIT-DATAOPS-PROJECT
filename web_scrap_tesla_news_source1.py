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
    #print(r.text)

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
        date = date.replace("Updated: ","") # remover "Updated: " se presente
        date_in_format = datetime.strptime(date, "%B %d, %Y").date()

        if link in seen_links:
            continue

        seen_links.add(link)

        news.append((title, link, date_in_format))

    return news



def run_scraper():
    all_news = []
    #pages = [1, 3, 5, 10,25,30,32,40,50,60,70,80,90,100]
    for page in range(1, 100):  # páginas desejadas
    #for page in pages:
        print(f"Página {page}")
        items = get_page(page)

        if not items:
            break

        all_news.extend(items) # Adiciona cada elemento de outra lista. Diferente de append que adiciona a lista como um único elemento

    for title, link, date in all_news:
        print(date)
        print(title)
        print(link)
        print("-" * 80)
    
    return all_news

def save_to_csv(news):
    path = Path("data/tesla_news/notateslaapp.csv")
    path.parent.mkdir(parents=True, exist_ok=True) # cria o diretório se não existir
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # cabeçalho
        writer.writerow(["date", "title", "link", "source"])

        # dados
        for title, link, date in news:
            writer.writerow([date, title, link, "notateslaapp"])


if __name__ == "__main__":
    news = run_scraper()
    save_to_csv(news)