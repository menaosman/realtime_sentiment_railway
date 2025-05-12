from flask import Flask, render_template, request, jsonify, send_file
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from io import BytesIO
from datetime import datetime
import os

app = Flask(__name__)
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
collection = client["sentiment_analysis"]["tweets"]

@app.route('/')
def home():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    df["Sentiment (Emoji)"] = df["Sentiment"].map({
        "positive": "😊 Positive",
        "neutral": "😐 Neutral",
        "negative": "😠 Negative"
    })
    return render_template("dashboard.html", tweets=df.to_dict("records"))

@app.route('/api/download')
def download_csv():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name="sentiment_results.csv")

@app.route('/api/push_mongo', methods=["POST"])
def push_to_mongo():
    try:
        collection.delete_many({})
        df = pd.DataFrame(request.json)
        df["BatchTimestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        collection.insert_many(df.to_dict("records"))
        return jsonify({"status": "success", "count": len(df)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/fetch_batches')
def fetch_batches():
    try:
        batches = collection.distinct("BatchTimestamp")
        return jsonify(sorted(batches, reverse=True))
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/fetch_by_batch', methods=["POST"])
def fetch_by_batch():
    batch = request.json.get("BatchTimestamp")
    cursor = collection.find({"BatchTimestamp": batch}, {"_id": 0})
    return jsonify(list(cursor))
@app.route('/api/upload', methods=['POST'])
def upload_to_mongo():
    try:
        data = request.get_json()
        collection.delete_many({})  # Clear existing data before upload
        if data:
            collection.insert_many(data)
            return jsonify({"status": "success", "message": f"Uploaded {len(data)} records."})
        return jsonify({"status": "error", "message": "No data to upload."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/fetch', methods=['GET'])
def fetch_from_mongo():
    try:
        data = list(collection.find({}, {"_id": 0}))
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
