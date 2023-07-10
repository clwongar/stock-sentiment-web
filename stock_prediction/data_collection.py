from datetime import datetime, timedelta

#library for models
from stock_prediction_dashboard.models import stockSentiment
from transformers import BertTokenizer, TFBertForSequenceClassification
from transformers import InputExample, InputFeatures
import tensorflow as tf

#restful api
from polygon import RESTClient

#model
model = tf.keras.models.load_model('./model/')
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

#api
client = RESTClient(api_key="31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8")

#for model prediction
def predict(pred_sentences, tokenizer, model):
    #Predictons
    tf_batch = tokenizer(pred_sentences, max_length=128, padding=True, truncation=True, return_tensors='tf')
    tf_outputs = model(tf_batch)
    tf_predictions = tf.nn.softmax(tf_outputs['logits'], axis=-1)
    label = ['Negative','Positive']
    label = tf.argmax(tf_predictions, axis=1)
    label = label.numpy()
    predicted_sentiments = label.tolist()
    return predicted_sentiments

def updatePrediction(symbol, date):
    predict_dataset = []
    for n in client.list_ticker_news(symbol, published_utc_gte=date, order="asc",limit=1000):
        if not stockSentiment.objects.filter(Ticker=symbol, date=n.published_utc[:10], sentence=n.title).exists():
            predict_dataset.append([symbol, n.published_utc[:10], n.title])
    predicted_sentiments = predict([row[2] for row in predict_dataset], tokenizer, model)
    for i in range(len(predict_dataset)):
        record = stockSentiment(Ticker=predict_dataset[i][0], date=predict_dataset[i][1], sentence=predict_dataset[i][2], sentiment=predicted_sentiments[i])
        record.save()

#update from Apr 1 to today
#["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA", "META", "TSM", "AVGO", "ORCL"]
'''
def updatePrediction(symbol):
    pred_dataset = []
    curr_date = datetime.now().strftime("%Y-%m-%d")
    for n in client.list_ticker_news(symbol, published_utc_gte="2023-04-01", published_utc_lte="2023-04-30", order="asc",limit=1000):
        pred_dataset.append([symbol, n.published_utc[:10], n.title])
    for n in client.list_ticker_news(symbol, published_utc_gte="2023-05-01", published_utc_lte="2023-05-31", order="asc",limit=1000):
        pred_dataset.append([symbol, n.published_utc[:10], n.title])
    for n in client.list_ticker_news(symbol, published_utc_gte="2023-06-01", published_utc_lte=curr_date, order="asc",limit=1000):
        pred_dataset.append([symbol, n.published_utc[:10], n.title])
    predicted_sentiments = predict([row[2] for row in pred_dataset], tokenizer, model)
    for i in range(len(pred_dataset)):
        record = stockSentiment(Ticker=pred_dataset[i][0], date=pred_dataset[i][1], sentence=pred_dataset[i][2], sentiment=predicted_sentiments[i])
        record.save()
'''