from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def fetch_naver_news():
    url = "https://search.naver.com/search.naver?where=news&query=비트코인"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    articles = []
    for item in soup.select("div.news_area"):
        a_tag = item.select_one("a.news_tit")
        date_tag = item.select_one("span.info")

        if not a_tag or not date_tag:
            continue

        title = a_tag.get_text(strip=True)
        link = a_tag["href"]
        date = date_tag.get_text(strip=True)

        articles.append({"title": title, "url": link, "date": date})

    return articles

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(fetch_naver_news())

if __name__ == '__main__':
    app.run(debug=True)
