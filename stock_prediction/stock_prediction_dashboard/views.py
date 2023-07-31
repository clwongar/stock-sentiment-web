import json
from django.http import HttpResponse
from django.shortcuts import render
from .models import *
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta, timezone
import requests
import time
import urllib.request


#library for models
import numpy as np
import tensorflow as tf
from transformers import TFBertModel, BertTokenizer, TFBertForSequenceClassification
from tensorflow.keras.layers import Input, LSTM, Dense, Concatenate, Attention, TimeDistributed, Reshape, Flatten
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from keras.models import Model
from keras.layers import LSTM, Dense, Input
from keras.preprocessing.sequence import TimeseriesGenerator
import csv

#stocks used #[0 5 3 1 6 8 4 9 2 7]
top10 = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA", "META", "TSM", "AVGO", "ORCL"]
top10_dict = {"AAPL": 0, "MSFT": 5, "GOOG": 3, "AMZN": 1, "NVDA": 6, "TSLA": 8, "META": 4, "TSM": 9, "AVGO": 2, "ORCL": 7}

#deploy model
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
lstm_model = tf.keras.models.load_model('./lstm_model/')
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')


# Create your views here.
def index(request):
    return render(request, "stock_prediction/dashboard.html")

#for auto updating
def update_sentiment(index):
    print("start " + str(index))

    today = (datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d") 
    last_update = lastUpdate.objects.last().date.strftime("%Y-%m-%d")

    Tickers = top10[:5]

    if index == 2:
        Tickers = top10[5:]

    for ticker in Tickers:
        url = 'https://api.polygon.io/v2/reference/news?ticker=' + ticker + '&published_utc.gte=' + last_update + '&published_utc.lte=' + today + '&sort=published_utc&sort=asc&limit=1000&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8'
        result = requests.get(url).json()['results']
        pred_dataset = []

        #if not in database, need to add them
        for r in result:
            if not stockSentiment.objects.filter(Ticker=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
                pred_dataset.append([ticker, r['published_utc'][:10], r['title']])

        if len(pred_dataset) != 0:
            predicted_sentiments = predict([row[2] for row in pred_dataset], sentiment_model)
            for i in range(len(pred_dataset)):
                record = stockSentiment(Ticker=pred_dataset[i][0], date=pred_dataset[i][1], sentence=pred_dataset[i][2], sentiment=predicted_sentiments[i])
                record.save()

        print(str(index) + " " + ticker + " done.")

    print("end " + str(index))

def update_predict_price_change():

    today = (datetime.now()).strftime("%Y-%m-%d")
    start_day = (datetime.now()-timedelta(days=149)).strftime("%Y-%m-%d")
    prediction_set = []

    for ticker in top10:
        stock_data = list(stockPrice.objects.filter(Ticker=ticker, date__range=[start_day, today]))
        prediction_set_ticker = []
        for item in stock_data:
            avg_sent = item.avg_sentiment
            unix = item.date.strftime("%Y-%m-%d")
            unix = datetime.strptime(unix,"%Y-%m-%d")
            unix = unix.replace(tzinfo=timezone.utc).timestamp() / 1000000000
            price_change = item.stock_change
            prediction_set_ticker.append([avg_sent, unix, price_change])
        prediction_set.append(prediction_set_ticker)

    pred_set_np = np.array(prediction_set)
    predictions = lstm_model.predict(pred_set_np)

    for i in range(len(top10)):
        s = stockInfo.objects.get(Ticker=top10[i])
        s.PredictPrice = predictions[i][0]
        s.save()

    print(pred_set_np.shape)
    print(predictions)
    

def update_stock_price(index):
    print("start " + str(index))
    start_date = lastUpdate.objects.last().date
    Tickers = top10[:5]
    if index == 4:
        Tickers = top10[5:]
    today = datetime.now().date()
    d = timedelta(days=30)
    a = (today - d).strftime("%Y-%m-%d")
    start_date_str = start_date.strftime("%Y-%m-%d")
    #print("start time: " + start_date.strftime("%Y-%m-%d"))
    for ticker in Tickers:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{a}/{today.strftime('%Y-%m-%d')}?adjusted=true&sort=desc&limit=120&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"
        result_json = requests.get(url).json()

        if result_json['resultsCount'] != 0:

            #update stock price for prediction

            #get average sentiment data
            sentiment_sum = list(stockSentiment.objects.filter(Ticker=ticker, date__range=[start_date_str, today]).values('date').order_by('date').annotate(total_sentiment=Sum('sentiment')))
            sentiment_count = list(stockSentiment.objects.filter(Ticker=ticker, date__range=[start_date_str, today]).values('date').order_by('date').annotate(total_count=Count('sentiment')))
            #average sentiment of the day {date: avg_sentiment}
            sent_avg = {}
            for i in range(len(sentiment_sum)):
                date = sentiment_sum[i]['date'].strftime("%Y-%m-%d")
                #since in the database it is [0: negative, 1: neutral, 2: positive]
                #need to -1 for all values and then do the average
                avg = (sentiment_sum[i]['total_sentiment'] - sentiment_count[i]['total_count']) / sentiment_count[i]['total_count']
                sent_avg[date] = avg

            #stock price
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            current_date = datetime.strptime(current_date_str,"%Y-%m-%d")
            
            #insert all new data
            for i in range(len(result_json['results'])-1):
                change = (result_json['results'][i]['c'] - result_json['results'][i+1]['c']) * 100 / result_json['results'][i+1]['c']
                date_str = datetime.utcfromtimestamp(result_json['results'][i]['t']/1000).strftime("%Y-%m-%d")
                date = datetime.strptime(date_str,"%Y-%m-%d")
                while date <= current_date:
                    if current_date.strftime("%Y-%m-%d") == start_date.strftime("%Y-%m-%d"):
                        break
                    avg_sentiment=0
                    if current_date.strftime("%Y-%m-%d") in sent_avg.keys():
                        avg_sentiment = sent_avg[current_date.strftime("%Y-%m-%d")]
                    sp = stockPrice(Ticker=ticker, date=current_date.strftime("%Y-%m-%d"), stock_price=result_json['results'][i]['c'], stock_change=change, avg_sentiment=avg_sentiment)
                    sp.save()
                    current_date = current_date-timedelta(days=1)

                #do update if it is latest date and exit loop
                if current_date.strftime("%Y-%m-%d") == start_date.strftime("%Y-%m-%d"):
                    #print("do last update: " + start_date.strftime("%Y-%m-%d"))
                    avg_sentiment = 0
                    if start_date_str in sent_avg.keys():
                        avg_sentiment = sent_avg[start_date_str]
                    sp = stockPrice.objects.get(Ticker=ticker, date=start_date_str)
                    sp.avg_sentiment = avg_sentiment
                    #update only when there is value
                    if date_str == start_date:
                        sp.stock_price = result_json['results'][i]['c']
                        sp.stock_change = change
                    sp.save()
                    break

            #update last update date

            result_curr = result_json['results'][0]   
            result_prev = result_json['results'][1]            
            s = stockInfo.objects.get(Ticker=ticker)
            s.PrevPrevPrice = result_prev['c']
            s.LatestPrice = result_curr['c']
            s.Volume = result_curr['v']
            s.save()
        print(str(index) + " " + ticker + " done.")
    print("end " + str(index))


def update_market_cap(index):

    print("start " + str(index))

    Tickers = top10[:5]

    if index == 6:
        Tickers = top10[5:]

    for ticker in Tickers:

        url = f"https://api.polygon.io/v3/reference/tickers/{ticker}?apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"

        result_json = requests.get(url).json()

        result_curr = result_json['results']['market_cap']         
        s = stockInfo.objects.get(Ticker=ticker)
        s.MarketCap = result_curr
        s.save()

        print(str(index) + " " + ticker + " done.")

    print("end " + str(index))

#1, 2 -> sentiment, 3, 4 -> stock details
def dailyUpdate(index):

    if index == 1 or index == 2:
        update_sentiment(index)
    if index == 3 or index == 4:
        update_stock_price(index)
    if index == 5 or index == 6:
        update_market_cap(index)
    if index == 7:
        update_predict_price_change()

    if (index == 6):
        last_update = lastUpdate.objects.last()
        last_update.date = datetime.utcnow().strftime("%Y-%m-%d")
        last_update.save()



#Overview Page
def getStockImg(request):
    return_json = []
    stocks = list(stockInfo.objects.all())
    for stock in stocks:
        return_json.append({"id": stock.id, "Ticker": stock.Ticker, "ImageURL": stock.ImageURL})
    return JsonResponse(return_json, safe=False)

def getStockDetails(request):
    #updateStock()
    stock_info = stockInfo.objects.all()
    return JsonResponse([stock.serialize() for stock in stock_info], safe=False)


#Prediction_page
def stock(request, Ticker):
    today = (datetime.now()).strftime("%Y-%m-%d")
    start_day = (datetime.now()-timedelta(days=6)).strftime("%Y-%m-%d")
    #today = (datetime.utcnow()).strftime("%Y-%m-%d")
    #start_day = (datetime.utcnow()-timedelta(days=6)).strftime("%Y-%m-%d")

    if Ticker == "all":
        stock_sentiment = []
        for ticker in top10:
            for i in range(7):
                date = (datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d")
                temp_stock_sentiment = list(stockSentiment.objects.filter(Ticker=ticker, date=date).values("Ticker", "sentiment"))
                if temp_stock_sentiment == []:
                    print(ticker + ": " + date + " has no data.")
                else:
                    for item in temp_stock_sentiment:
                        stock_sentiment.append(item)
                    break
        #print(stock_sentiment)
        return JsonResponse(stock_sentiment, safe=False)
    
    stock_sentiment = list(stockSentiment.objects.filter(date__range=[start_day,today], Ticker=Ticker).values("date", "sentiment"))
    for item in stock_sentiment:
        item['date'] = item['date'].strftime("%Y-%m-%d")
    return JsonResponse(stock_sentiment, safe=False)