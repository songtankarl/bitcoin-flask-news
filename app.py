from flask import Flask, jsonify, render_template
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get('NEWSAPI_KEY') or 'f509959c999b4d7e98cc62d75c0b3102'
NEWS_ENDPOINT = 'https://newsapi.org/v2/everything'

def fetch_bitcoin_news():
    params = {
        'q': '비트코인',
        'language': 'ko',
        'sortBy': 'publishedAt',
        'pageSize': 100,
        'apiKey': API_KEY
    }
    response = requests.get(NEWS_ENDPOINT, params=params)
    data = response.json()

    seen_sources = set()
    filtered_articles = []

    for article in data.get("articles", []):
        source = article["source"]["name"]
        if source not in seen_sources:
            seen_sources.add(source)
            filtered_articles.append({
                'title': article["title"],
                'url': article["url"],
                'source': source
            })

    return filtered_articles

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news')
def get_news():
    return jsonify(fetch_bitcoin_news())

if __name__ == '__main__':
    app.run(debug=True)
