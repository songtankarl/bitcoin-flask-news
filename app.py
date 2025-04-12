from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

app = Flask(__name__)

def fetch_naver_news():
    headers = {"User-Agent": "Mozilla/5.0"}
    base_url = "https://search.naver.com/search.naver?where=news&query=비트코인&start="

    today = datetime.now().date()
    date_map = {
        today: [],
        today - timedelta(days=1): [],
        today - timedelta(days=2): []
    }

    def classify_article(date_str, article):
        d = date_str.strip()
        article_date = None

        try:
            if "일 전" in d:
                days_ago = int(d.replace("일 전", "").strip())
                article_date = today - timedelta(days=days_ago)
            elif "시간 전" in d or "분 전" in d:
                article_date = today
            else:
                try:
                    article_date = datetime.strptime(d, "%Y.%m.%d.").date()
                except ValueError:
                    try:
                        article_date = datetime.strptime(d, "%Y.%m.%d").date()
                    except:
                        return
        except:
            return

        if article_date in date_map and len(date_map[article_date]) < 30:
            date_map[article_date].append(article)

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
                break
        if count >= 100:
            break

    result = {}
    for dt, articles in date_map.items():
        key = dt.strftime("%Y년 %m월 %d일")
        result[key] = articles
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(fetch_naver_news())

if __name__ == '__main__':
    app.run(debug=True)
