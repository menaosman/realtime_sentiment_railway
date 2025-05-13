from flask import Flask, render_template, request, jsonify, send_file
from pymongo import MongoClient
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from io import BytesIO
from datetime import datetime
import os

app = Flask(__name__)

# MongoDB Configuration
mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
collection = client["sentiment_analysis"]["tweets"]

@app.route('/')
def home():
    return render_template('dashboard.html')  # Make sure your HTML file is named 'dashboard.html' and placed in 'templates/'.

@app.route('/api/fetch', methods=['GET'])
def fetch_from_mongo():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        skip = (page - 1) * limit
        data = list(collection.find({}, {"_id": 0}).skip(skip).limit(limit))
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/wordcloud_image')
def wordcloud_image():
    sentiment = request.args.get('sentiment')
    query = {"Sentiment": sentiment} if sentiment else {}
    texts = [doc.get('Text', '') for doc in collection.find(query, {"Text": 1, "_id": 0})]

    if not texts or not ''.join(texts).strip():
        return '', 204  # No content

    combined_text = ' '.join(texts)
    wc = WordCloud(width=800, height=400, background_color='white').generate(combined_text)
    img_io = BytesIO()
    wc.to_image().save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/api/sentiment_distribution')
def sentiment_distribution():
    try:
        data = list(collection.find({}, {"Sentiment": 1, "_id": 0}))
        sentiments = pd.DataFrame(data)["Sentiment"].value_counts().to_dict()
        return jsonify(sentiments)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/upload', methods=['POST'])
def upload_to_mongo():
    try:
        data = request.get_json()
        if data:
            batch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for record in data:
                record["BatchTimestamp"] = batch_time
            collection.insert_many(data)
            return jsonify({"status": "success", "message": f"Uploaded {len(data)} records with batch timestamp {batch_time}."})
        return jsonify({"status": "error", "message": "No data provided."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/batches', methods=['GET'])
def get_batches():
    try:
        batches = collection.distinct("BatchTimestamp")
        return jsonify(sorted(batches, reverse=True))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/fetch_batch', methods=['POST'])
def fetch_by_batch():
    batch_time = request.json.get("BatchTimestamp")
    data = list(collection.find({"BatchTimestamp": batch_time}, {"_id": 0}))
    return jsonify(data)

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
@app.route('/api/sentiment_over_time')
def sentiment_over_time():
    try:
        data = list(collection.find({}, {"Sentiment": 1, "Timestamp": 1, "_id": 0}))
        df = pd.DataFrame(data)

        if "Timestamp" not in df or df.empty:
            return jsonify({"status": "error", "message": "No timestamp data available."})

        # Ensure Timestamp is in datetime format
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors='coerce')
        df = df.dropna(subset=["Timestamp"])

        # Group by Date and Sentiment
        df["Date"] = df["Timestamp"].dt.date
        sentiment_time = df.groupby(["Date", "Sentiment"]).size().unstack(fill_value=0).reset_index()

        # Convert to JSON-friendly format
        result = {
            "dates": sentiment_time["Date"].astype(str).tolist(),
            "positive": sentiment_time.get("positive", pd.Series()).tolist(),
            "neutral": sentiment_time.get("neutral", pd.Series()).tolist(),
            "negative": sentiment_time.get("negative", pd.Series()).tolist()
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
