from flask import Flask, render_template, jsonify
from pymongo import MongoClient
import pandas as pd
import os

app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri, tls=True, tlsAllowInvalidCertificates=True)
collection = client["sentiment_analysis"]["tweets"]

@app.route('/')
def home():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)
    return render_template("dashboard.html", tweets=df.to_dict(orient="records"))

@app.route('/api/tweets')
def api_tweets():
    data = list(collection.find({}, {"_id": 0}))
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
