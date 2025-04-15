from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
cache = Cache(app, config={{'CACHE_TYPE': 'SimpleCache'}})

@app.route("/")
def home():
    return render_template("index.html")

@cache.cached(timeout=300)
@app.route("/api/news")
def news():
    headers = {{
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    }}
    base_url = "https://search.naver.com/search.naver?where=news&query=비트코인&start="

    now = datetime.now(timezone('Asia/Seoul'))
    today = now.date()
    
    date_map = {{}}
    for i in range(4):
        date_key = today - timedelta(days=i)
        date_map[date_key] = []

    def classify(date_str, article):
        d = date_str.strip().replace(".", "-").replace(" ", "")
        try:
            if "일전" in d:
                days = int(d.replace("일전", "").strip())
                article_date = today - timedelta(days=days)
            elif "시간전" in d or "분전" in d:
                article_date = today
            elif "-" in d:
                article_date = datetime.strptime(d, "%Y-%m-%d").date()
            else:
                print("❌ 처리 못한 날짜 형식:", d)
                return

            if article_date in date_map and len(date_map[article_date]) < 30:
                date_map[article_date].append(article)
        except Exception as e:
            print(f"[❌ classify 실패] {{d}} → {{e}}")
            return

    count = 0
    for page in range(1, 11):
        url = base_url + str((page - 1) * 10 + 1)
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"⛔ 요청 실패: {{e}}")
            continue

        for item in soup.select("li.bx"):
            a = item.select_one("a.news_tit")
            date_tag = None
            for span in item.select("span.info"):
                text = span.get_text(strip=True)
                if "2025." in text or "2024." in text:
                    date_tag = text
                    break

            if not a or not date_tag:
                continue

            article = {{
                "title": a.get_text(strip=True),
                "url": a["href"],
                "press": "N/A",
                "date": date_tag
            }}
            classify(article["date"], article)
            count += 1

        if count >= 100:
            break

    result = {{dt.strftime("%Y년 %m월 %d일"): date_map.get(dt, []) for dt in sorted(date_map.keys(), reverse=True)}}
    return jsonify(result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
