from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

def fetch_naver_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://search.naver.com/search.naver?where=news&query=비트코인&start="

    today = datetime.now().date()
    one_day_ago = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    categories = {
        "today": [],
        "one_day_ago": [],
        "two_days_ago": []
    }

    def classify_article(date_str, article):
        date_str = date_str.strip()
        if "분 전" in date_str or "시간 전" in date_str or "오늘" in date_str or "전" in date_str:
            categories["today"].append(article)
        else:
            try:
                published_date = datetime.strptime(date_str, "%Y.%m.%d.").date()
                if published_date == today:
                    categories["today"].append(article)
                elif published_date == one_day_ago:
                    categories["one_day_ago"].append(article)
                elif published_date == two_days_ago:
                    categories["two_days_ago"].append(article)
            except:
                pass

    count = 0
    for page in range(1, 11):  # 최대 100개 기사
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

            article = {
                "title": title,
                "url": link,
                "press": press,
                "date": date_str
            }

            classify_article(date_str, article)

            count += 1
            if count >= 100:
                return categories

    return categories

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(fetch_naver_news())

if __name__ == '__main__':
    app.run(debug=True)
