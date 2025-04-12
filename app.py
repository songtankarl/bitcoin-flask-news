from flask import Flask, jsonify, render_template
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.environ.get('NEWSAPI_KEY') or 'f509959c999b4d7e98cc62d75c0b3102'
NEWS_ENDPOINT = 'https://newsapi.org/v2/everything'

def fetch_bitcoin_news():
    from_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')

    all_articles = []
    seen_sources = set()

    for page in range(1, 6):  # 1~5페이지 반복
        params = {
            'q': '비트코인',
            'language': 'ko',
            'from': from_date,
            'sortBy': 'publishedAt',
            'pageSize': 100,
            'page': page,
            'apiKey': API_KEY
        }
        response = requests.get(NEWS_ENDPOINT, params=params)
        data = response.json()

        for article in data.get("articles", []):
            source = article["source"]["name"]
            if source not in seen_sources:
                seen_sources.add(source)
                all_articles.append({
                    'title': article["title"],
                    'url': article["url"],
                    'source': source
                })

        if len(data.get("articles", [])) < 100:
            break

    return all_articles

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(fetch_bitcoin_news())

if __name__ == '__main__':
    app.run(debug=True)
