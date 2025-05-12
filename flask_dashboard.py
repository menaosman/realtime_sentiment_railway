from flask import Flask, render_template, request, jsonify, send_file
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from io import BytesIO
from datetime import datetime
import base64
import os

app = Flask(__name__)

# MongoDB Configuration
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
collection = client["sentiment_analysis"]["tweets"]

@app.route('/')
def home():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    if not df.empty and "Sentiment" in df.columns:
        df["Sentiment (Emoji)"] = df["Sentiment"].map({
            "positive": "😊 Positive",
            "neutral": "😐 Neutral",
            "negative": "😠 Negative"
        })
    return render_template("dashboard.html", tweets=df.to_dict("records"))

@app.route('/api/upload_csv', methods=['POST'])
def upload_csv():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded."})
        file = request.files['file']
        df = pd.read_csv(file)
        df["BatchTimestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        collection.insert_many(df.to_dict("records"))
        return jsonify({"status": "success", "message": f"Uploaded {len(df)} records."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/download')
def download_csv():
    try:
        data = list(collection.find({}, {"_id": 0}))
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(output, mimetype="text/csv", as_attachment=True, download_name="sentiment_results.csv")
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

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
    try:
        batch = request.json.get("BatchTimestamp")
        cursor = collection.find({"BatchTimestamp": batch}, {"_id": 0})
        return jsonify(list(cursor))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

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

# ✅ NEW: WordCloud Generation API
@app.route('/api/wordcloud', methods=['GET'])
def generate_wordcloud():
    try:
        texts = [doc.get('Text', '') for doc in collection.find({}, {"Text": 1, "_id": 0})]
        if not texts:
            return jsonify({"status": "error", "message": "No text data found for WordCloud."})

        combined_text = ' '.join(texts)
        wc = WordCloud(width=800, height=400, background_color='white').generate(combined_text)
        
        img_io = BytesIO()
        wc.to_image().save(img_io, 'PNG')
        img_io.seek(0)
        base64_img = base64.b64encode(img_io.read()).decode('utf-8')

        return jsonify({"status": "success", "wordcloud": base64_img})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
