from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from pytz import timezone
import re  # 추가

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
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
    }
    base_url = "https://m.search.naver.com/search.naver?where=m_news&query=비트코인&start="

    now = datetime.now(timezone('Asia/Seoul'))
    today = now.date()
    
    # 최근 4일의 날짜별로 딕셔너리 초기화
    date_map = {}
    for i in range(4):
        date_key = today - timedelta(days=i)
        date_map[date_key] = []

    def classify_relative_date(date_str):
        """
        '방금 전', 'n분 전', 'n시간 전', 'n일 전', 'YYYY.MM.DD' 등 다양한 형태의 
        날짜 문자열을 파싱해서 date(YYYY, MM, DD)를 반환하는 함수.
        파싱 실패 시 None 반환
        """
        # 기본 전처리
        date_str = date_str.strip()
        # '·' 기호 제거 (네이버 모바일 환경에서 가끔 섞여 나오므로)
        date_str = date_str.replace("·", "")
        
        # 1) 'n시간 전', 'n분 전', 'n일 전' 형태 처리
        #    예: "5시간 전", "10분 전", "2일 전" 등
        m_relative = re.match(r'(\d+)(분|시간|일)\s*전', date_str)
        if m_relative:
            amount = int(m_relative.group(1))
            unit = m_relative.group(2)

            if unit == '분':
                return (now - timedelta(minutes=amount)).date()
            elif unit == '시간':
                return (now - timedelta(hours=amount)).date()
            elif unit == '일':
                return (now - timedelta(days=amount)).date()

        # 2) 'YYYY.MM.DD' 혹은 'YYYY.MM.DD.' 형태
        #    가끔 뒤에 시간이 붙어서 "YYYY.MM.DD. HH:MM" 로 나오기도 함
        #    예: "2025.04.12", "2025.04.12.", "2025.04.12. 15:30"
        m_date = re.match(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})', date_str)
        if m_date:
            y = int(m_date.group(1))
            m = int(m_date.group(2))
            d = int(m_date.group(3))

            # 혹시 뒤에 시간이 붙어 있다면, 추가로 HH:MM 형식을 파싱할 수도 있음
            # 여기서는 일단 date까지만 파싱
            try:
                return date(y, m, d)
            except ValueError:
                # 예외 발생 시 None
                return None

        # 3) 그 외 "어제", "이틀 전", "방금 전" 같은 경우를 추가로 처리하고 싶다면:
        if "어제" in date_str:
            # "어제 14:20"처럼 구체적인 시간이 있을 수도 있으니 여기서 더 파싱해도 됨
            return (now - timedelta(days=1)).date()

        if "이틀 전" in date_str:
            return (now - timedelta(days=2)).date()

        if "방금 전" in date_str:
            return now.date()

        # 여기까지 왔는데도 파싱이 안 되면 None 리턴
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
            # "언론사 · n시간 전" 처럼 뒤쪽에 날짜/시간 정보가 나오는 경우가 많으므로
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

    result = {
        dt.strftime("%Y년 %m월 %d일"): date_map.get(dt, []) 
        for dt in sorted(date_map.keys(), reverse=True)
    }
    return jsonify(result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
