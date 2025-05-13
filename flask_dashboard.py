from flask import Flask, render_template, request, jsonify, send_file
from pymongo import MongoClient
import pandas as pd
from wordcloud import WordCloud
from io import BytesIO
from datetime import datetime
import os

app = Flask(__name__)

# MongoDB Configuration
mongo_uri = os.getenv("MONGO_URI")  # Add your default URI or keep it from environment
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
collection = client["sentiment_analysis"]["tweets"]

@app.route('/')
def home():
    return render_template('dashboard.html')  # Ensure this HTML exists in templates/

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
        return '', 204

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

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
