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
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://search.naver.com/search.naver?where=news&query=비트코인&start="

    now = datetime.now(timezone('Asia/Seoul'))
    today = now.date()
    
    date_map = {}
    for i in range(4):
    date_key = today - timedelta(days=i)
        date_map[date_key] = []

    def classify(date_str, article):
        d = date_str.strip()
        try:
            article_date = None

            if "일 전" in d:
                days = int(d.replace("일 전", "").strip())
                article_date = (now - timedelta(days=days)).date()
            elif "어제" in d:
                article_date = (now - timedelta(days=1)).date()
            elif "그제" in d:
                article_date = (now - timedelta(days=2)).date()
            elif any(x in d for x in ["초 전", "분 전", "시간 전", "방금 전", "오늘"]):
                article_date = now.date()
            else:
                if d.endswith("."):
                    d = d[:-1]
                article_date = datetime.strptime(d, "%Y.%m.%d").date()

            if article_date in date_map and len(date_map[article_date]) < 30:
                date_map[article_date].append(article)

        except Exception as e:
            print(f"[❌ classify 실패] {d} → {e}")
            return

    count = 0
    for page in range(1, 11):
        url = base_url + str((page - 1) * 10 + 1)
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"⛔ 요청 실패: {e}")
            continue

        for item in soup.select("div.news_area"):
            a = item.select_one("a.news_tit")
            p = item.select_one("a.info.press")
            d = item.select_one("span.info")

                # 디버깅 로그 추가
            print("🎯 기사 요소 탐색 결과:")
            print("title:", a.get_text(strip=True) if a else "없음")
            print("press:", p.get_text(strip=True) if p else "없음")
            print("date :", d.get_text(strip=True) if d else "없음")
            print("---")

            if not a or not p or not d:
                continue
        
            if not a or not p or not d:
                continue
            article = {
                "title": a.get_text(strip=True),
                "url": a["href"],
                "press": p.get_text(strip=True).replace("언론사 선정", "").strip(),
                "date": d.get_text(strip=True)
            }
            classify(article["date"], article)
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
