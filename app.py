from flask import Flask, jsonify, render_template
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.environ.get('NEWSAPI_KEY') or 'f509959c999b4d7e98cc62d75c0b3102'
NEWS_ENDPOINT = 'https://newsapi.org/v2/everything'

def fetch_bitcoin_news():
    now = datetime.utcnow() + timedelta(hours=9)
    from_time = (now - timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0)

    from_str = from_time.strftime('%Y-%m-%dT%H:%M:%S')
    to_str = now.strftime('%Y-%m-%dT%H:%M:%S')

    all_articles = []

    for page in range(1, 6):
        params = {
            'q': '비트코인 OR bitcoin',
            'from': from_str,
            'to': to_str,
            'sortBy': 'publishedAt',
            'pageSize': 100,
            'page': page,
            'apiKey': API_KEY,
            'domains': 'zdnet.co.kr,ohmynews.com,blockmedia.co.kr'
        }
        response = requests.get(NEWS_ENDPOINT, params=params)
        data = response.json()

        for article in data.get("articles", []):
            all_articles.append({
                'title': article["title"],
                'url': article["url"],
                'source': article["source"]["name"],
                'publishedAt': article["publishedAt"]
            })

        if len(data.get("articles", [])) < 100:
            break

    all_articles.sort(key=lambda x: x["publishedAt"], reverse=True)

    return all_articles

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(fetch_bitcoin_news())

if __name__ == '__main__':
    app.run(debug=True)
