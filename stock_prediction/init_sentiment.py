from stock_prediction_dashboard.models import *
import numpy as np
import tensorflow as tf
from transformers import TFBertModel, BertTokenizer, TFBertForSequenceClassification
from tensorflow.keras.layers import Input, LSTM, Dense, Concatenate, Attention, TimeDistributed, Reshape, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from keras.models import Model
from keras.layers import LSTM, Dense, Input
from keras.preprocessing.sequence import TimeseriesGenerator
import requests
top10 = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA", "META", "TSM", "AVGO", "ORCL"]
top10_dict = {"AAPL": 0, "MSFT": 5, "GOOG": 3, "AMZN": 1, "NVDA": 6, "TSLA": 8, "META": 4, "TSM": 9, "AVGO": 2, "ORCL": 7}
def predict(pred_sentences, model, batch_size=32):
    # Initialize an empty list to store the predictions
    predicted_sentiments = []
    # Iterate over the sentences in batches
    for i in range(0, len(pred_sentences), batch_size):
        # Slice the input list to get the current batch
        batch_sentences = pred_sentences[i:i+batch_size]
        # Make predictions on the batch
        tf_batch = tokenizer(batch_sentences, max_length=150, padding=True, truncation=True, return_tensors='tf')
        tf_outputs = model(tf_batch)
        tf_predictions = tf.nn.softmax(tf_outputs['logits'], axis=-1)
        label = tf.argmax(tf_predictions, axis=1)
        label = label.numpy().tolist()
        # Map the numeric labels to their string counterparts and add them to the predictions list
        #sentiment_map = {0:'negative', 1:'neutral', 2:'positive'}
        #batch_predicted_sentiments = [sentiment_map[i] for i in label.tolist()]
        predicted_sentiments.extend(label)
    # Return the list of all predictions
    return predicted_sentiments

sentiment_model = TFBertForSequenceClassification.from_pretrained('./sentiment_model/')
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
def update_ticker(ticker):
    url1 = "https://api.polygon.io/v2/reference/news?ticker=" + ticker + "&published_utc.gte=2023-05-31&published_utc.lte=2023-07-31&sort=published_utc&sort=asc&limit=1000&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"
    url2 = "https://api.polygon.io/v2/reference/news?ticker=" + ticker + "&published_utc.gte=2023-03-31&published_utc.lte=2023-05-30&sort=published_utc&sort=asc&limit=1000&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"
    url3 = "https://api.polygon.io/v2/reference/news?ticker=" + ticker + "&published_utc.gte=2023-02-01&published_utc.lte=2023-03-30&sort=published_utc&sort=asc&limit=1000&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"
    result1 = requests.get(url1).json()['results']
    result2 = requests.get(url2).json()['results']
    result3 = requests.get(url3).json()['results']
    pred_dataset = []
    for r in result1:
        if not stockSentiment.objects.filter(Ticker=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
            pred_dataset.append([ticker, r['published_utc'][:10], r['title']])
    for r in result2:
        if not stockSentiment.objects.filter(Ticker=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
            pred_dataset.append([ticker, r['published_utc'][:10], r['title']])
    for r in result3:
        if not stockSentiment.objects.filter(Ticker=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
            pred_dataset.append([ticker, r['published_utc'][:10], r['title']])
    if len(pred_dataset) != 0:
        predicted_sentiments = predict([row[2] for row in pred_dataset], sentiment_model)
        for i in range(len(pred_dataset)):
            record = stockSentiment(Ticker=pred_dataset[i][0], date=pred_dataset[i][1], sentence=pred_dataset[i][2], sentiment=predicted_sentiments[i])
            record.save()