from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from pytz import timezone
import re

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
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        )
    }
    base_url = "https://m.search.naver.com/search.naver?where=m_news&query=비트코인&start="

    # 현재(한국 시간) 날짜 구하기
    now = datetime.now(timezone('Asia/Seoul'))
    today = now.date()

    # 최근 4일 치를 저장할 딕셔너리
    date_map = {}
    for i in range(4):
        date_key = today - timedelta(days=i)
        date_map[date_key] = []

    def classify_relative_date(date_str: str):
        """
        'n시간 전', 'n분 전', 'n일 전', 'YYYY.MM.DD.', 'YYYY.MM.DD' 형태 등을
        제대로 파싱하여 date 객체(년-월-일)로 반환. 파싱 실패 시 None.
        """

        date_str = date_str.strip()
        # 혹시 "2025.04.15." 처럼 끝에 점이 붙어있으면 제거
        # (단, 'n시간 전' 같은 표현까지 잘라내면 안 되므로 주의)
        if re.match(r"\d{4}\.\d{1,2}\.\d{1,2}\.$", date_str):
            date_str = date_str.rstrip(".")

        # 1) 상대 날짜: "n시간 전", "n분 전", "n일 전"
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

        # 2) 절대 날짜: "YYYY.MM.DD" or "YYYY.MM.DD."
        #    예) "2025.04.14" 또는 "2025.04.14."
        m_date = re.match(r'^(\d{4})\.(\d{1,2})\.(\d{1,2})$', date_str)
        if m_date:
            y = int(m_date.group(1))
            m = int(m_date.group(2))
            d = int(m_date.group(3))
            try:
                return date(y, m, d)
            except ValueError:
                return None

        # 3) 기타 케이스: "어제", "이틀 전", "방금 전" 등이 필요한 경우 추가
        if "어제" in date_str:
            return (now - timedelta(days=1)).date()
        if "이틀 전" in date_str:
            return (now - timedelta(days=2)).date()
        if "방금 전" in date_str:
            return now.date()

        return None

    count = 0
    # 네이버 모바일 뉴스 검색결과는 start=1,11,21,31,41 등으로 페이지네이션
    for page in range(1, 6):
        # (page-1)*10+1 → 1, 11, 21, 31, 41
        url = base_url + str((page - 1) * 10 + 1)
        try:
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"⛔ 요청 실패: {e}")
            continue

        # 모바일 네이버 뉴스 결과는 보통 div.news_wrap.api_ani_send 안에 기사 정보가 들어 있음
        news_items = soup.select("div.news_wrap.api_ani_send")
        for item in news_items:
            # 기사 제목 a 태그
            a = item.select_one("a.news_tit")
            if not a:
                continue

            # 기사 정보 (언론사, 날짜 등) 
            info_group = item.select_one("div.news_info > div.info_group")
            if not info_group:
                continue

            # 예: 
            # <span class="info press">언론사</span>
            # <span class="info">2시간 전</span>
            info_spans = info_group.select("span.info")
            press_str = ""
            raw_date = ""
            if len(info_spans) >= 2:
                # 첫 번째 span.info가 언론사, 두 번째 span.info가 날짜인 케이스
                press_str = info_spans[0].get_text(strip=True)
                raw_date = info_spans[1].get_text(strip=True)
            elif len(info_spans) == 1:
                # 경우에 따라 하나만 있을 수도 있음 (ex. 'n시간 전'만 노출)
                raw_text = info_spans[0].get_text(strip=True)
                # 언론사에 '뉴스'나 특정 키워드가 들어있을 수도 있으므로, 
                # 날짜인지 판별 시도
                # 간단히 '전' 포함 여부나 yyyy.mm.dd 정규식으로 판별
                if "전" in raw_text or re.match(r'^\d{4}\.\d{1,2}\.\d{1,2}', raw_text):
                    raw_date = raw_text
                else:
                    press_str = raw_text

            # 날짜 파싱
            article_date = classify_relative_date(raw_date)
            if article_date and article_date in date_map:
                article = {
                    "title": a.get_text(strip=True),
                    "url": a["href"],
                    "press": press_str,
                    "date": raw_date
                }
                date_map[article_date].append(article)
                count += 1

            if count >= 100:
                break

        if count >= 100:
            break

    # 날짜 내림차순 정렬
    result = {
        dt.strftime("%Y년 %m월 %d일"): date_map.get(dt, [])
        for dt in sorted(date_map.keys(), reverse=True)
    }

    return jsonify(result)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
