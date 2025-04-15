from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

@app.route("/")
def home():
    return render_template("index.html")

@cache.cached(timeout=300)
@app.route("/api/news")
def news():
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    }
    base_url = "https://m.search.naver.com/search.naver?where=m_news&query=비트코인&start="

    now = datetime.now(timezone('Asia/Seoul'))
    today = now.date()
    
    date_map = {}
    for i in range(4):
        date_key = today - timedelta(days=i)
        date_map[date_key] = []

    def classify_relative_date(date_str):
        date_str = date_str.strip().replace(" ", "").replace("·", "")
        try:
            if "시간전" in date_str:
                hours = int(date_str.replace("시간전", ""))
                return (now - timedelta(hours=hours)).date()
            elif "분전" in date_str:
                minutes = int(date_str.replace("분전", ""))
                return (now - timedelta(minutes=minutes)).date()
            elif "일전" in date_str:
                days = int(date_str.replace("일전", ""))
                return (now - timedelta(days=days)).date()
            elif "." in date_str:
                return datetime.strptime(date_str, "%Y.%m.%d").date()
        except Exception as e:
            print(f"[❌ 날짜 파싱 실패] {date_str} → {e}")
        return None

    count = 0
    for page in range(1, 6):
        url = base_url + str((page - 1) * 10 + 1)
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"⛔ 요청 실패: {e}")
            continue

        for item in soup.select("li"):
            a = item.select_one("a.news_tit")
            date_info = item.select_one("div.news_info") or item.select_one("span.sub_txt")
            if not a or not date_info:
                continue

            meta_text = date_info.get_text(" ", strip=True)
            raw_date = meta_text.split("·")[-1].strip()
            article_date = classify_relative_date(raw_date)

            if article_date and article_date in date_map:
                article = {
                    "title": a.get_text(strip=True),
                    "url": a["href"],
                    "press": meta_text.split("·")[0].strip(),
                    "date": raw_date
                }
                date_map[article_date].append(article)
                count += 1

            if count >= 100:
                break
        if count >= 100:
            break

    result = {dt.strftime("%Y년 %m월 %d일"): date_map.get(dt, []) for dt in sorted(date_map.keys(), reverse=True)}
    return jsonify(result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
