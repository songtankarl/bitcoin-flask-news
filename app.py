from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

def fetch_naver_news():
    articles = []
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://search.naver.com/search.naver?where=news&query=비트코인&start="

    now = datetime.now()
    three_days_ago = now - timedelta(days=3)

    for page in range(1, 11):  # 10페이지 x 10개 = 최대 100개 기사
        start = (page - 1) * 10 + 1
        url = base_url + str(start)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        for item in soup.select("div.news_area"):
            a_tag = item.select_one("a.news_tit")
            press_tag = item.select_one("a.info.press")
            date_tag = item.select_one("span.info")

            if not a_tag or not press_tag or not date_tag:
                continue

            title = a_tag.get_text(strip=True)
            link = a_tag["href"]
            press = press_tag.get_text(strip=True).replace("언론사 선정", "").strip()
            date_str = date_tag.get_text(strip=True)

            # 날짜 필터링
            if "전" in date_str:  # ex) 2시간 전, 1일 전
                if "일" in date_str:
                    days = int(date_str.replace("일 전", "").strip())
                    if days > 3:
                        continue
                # "시간 전", "분 전"은 최신 기사이므로 허용
            else:
                try:
                    published_date = datetime.strptime(date_str, "%Y.%m.%d.")
                    if published_date < three_days_ago:
                        continue
                except:
                    continue  # 날짜 포맷 이상 시 스킵

            articles.append({
                "title": title,
                "url": link,
                "press": press,
                "date": date_str
            })

            if len(articles) >= 100:
                return articles

    return articles

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(fetch_naver_news())

if __name__ == '__main__':
    app.run(debug=True)
