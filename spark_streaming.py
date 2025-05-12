from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import StructType, StringType
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pymongo import MongoClient

# MongoDB setup
mongo_uri = "mongodb+srv://biomedicalinformatics100:MyNewSecurePass%2123@cluster0.jilvfuv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(mongo_uri)
collection = mongo_client["sentiment_analysis"]["tweets"]

# Spark setup
spark = SparkSession.builder.appName("KafkaSparkMongo").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

schema = StructType().add("Text", StringType()).add("Timestamp", StringType())

def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)['compound']
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

sentiment_udf = udf(analyze_sentiment, StringType())

df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "tweets")
    .load()
)

parsed_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .withColumn("Sentiment", sentiment_udf(col("Text")))

def foreach_batch_function(batch_df, batch_id):
    records = batch_df.toPandas().to_dict(orient="records")
    if records:
        collection.insert_many(records)

query = parsed_df.writeStream.foreachBatch(foreach_batch_function).start()
query.awaitTermination()
