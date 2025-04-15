from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone

app = Flask(__name__)
CORS(app)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

@app.route("/")
def index():
    return render_template("index.html")

@cache.cached(timeout=300)
@app.route("/api/news")
def get_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://m.search.naver.com/search.naver?where=m_news&query=비트코인&start="

    now = datetime.now(timezone('Asia/Seoul'))
    today = now.date()

    date_map = {}
    for i in range(4):
        date_key = today - timedelta(days=i)
        date_map[date_key] = []

    count = 0
    for page in range(1, 11):
        start = (page - 1) * 10 + 1
        url = base_url + str(start)
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"요청 실패: {e}")
            continue

        for item in soup.select("li.bx"):
            a = item.select_one("a.news_tit")
            if a:
                title = a.get_text(strip=True)
                link = a["href"]
                article = {
                    "title": title,
                    "url": link,
                    "press": "N/A",
                    "date": now.strftime("%Y.%m.%d")
                }
                date_map[today].append(article)
                count += 1
                if count >= 30:
                    break
        if count >= 30:
            break

    result = {dt.strftime("%Y년 %m월 %d일"): date_map.get(dt, []) for dt in sorted(date_map.keys(), reverse=True)}
    return jsonify(result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
