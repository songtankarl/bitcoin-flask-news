from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def scrape_coinreaders_news(query="비트코인"):
    url = f"https://www.coinreaders.com/search?search={query}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    for item in soup.select("div.item"):
        a_tag = item.select_one("h2.tit a")
        date_tag = item.select_one("span.date")

        if not a_tag or not date_tag:
            continue

        title = a_tag.get_text(strip=True)
        link = a_tag["href"]
        if not link.startswith("http"):
            link = "https://www.coinreaders.com" + link
        date = date_tag.get_text(strip=True)

        articles.append({"title": title, "url": link, "date": date})

    return articles

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(scrape_coinreaders_news())

if __name__ == '__main__':
    app.run(debug=True)
