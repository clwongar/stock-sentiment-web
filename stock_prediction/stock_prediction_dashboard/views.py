import json
from django.http import HttpResponse
from django.shortcuts import render
from .models import *
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import requests
import time
import urllib.request


#library for models
#from transformers import BertTokenizer, TFBertForSequenceClassification
#from transformers import InputExample, InputFeatures
import numpy as np
import tensorflow as tf
from transformers import TFBertModel, BertTokenizer
from tensorflow.keras.layers import Input, LSTM, Dense, Concatenate, Attention, TimeDistributed, Reshape
from tensorflow.keras.models import Model
import csv

#stocks used #[0 5 3 1 6 8 4 9 2 7]
top10 = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA", "META", "TSM", "AVGO", "ORCL"]
top10_dict = {"AAPL": 0, "MSFT": 5, "GOOG": 3, "AMZN": 1, "NVDA": 6, "TSLA": 8, "META": 4, "TSM": 9, "AVGO": 2, "ORCL": 7}


#deploy model
# Instantiate the tokenizer
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
# Instantiate the BERT model
bert_model = TFBertModel.from_pretrained("bert-base-uncased")
# Define input layers
news_text_input = Input(shape=(150,), dtype="int32", name="news_text_input")
stock_price_input = Input(shape=(1,), dtype="float32", name="stock_price_input")
date_input = Input(shape=(1,), dtype="float32", name="date_input")  # Updated input shape for Unix time
# BERT layer for text processing
bert_output = bert_model(news_text_input)[1]
# Concatenate BERT output with stock price and date
merged_inputs = Concatenate(axis=1)([bert_output, stock_price_input, date_input])
# Add a time dimension for LSTM
reshaped_inputs = Reshape((1, 770))(merged_inputs)  # Updated input dimensions to match Unix time input
# LSTM layer
lstm_output = LSTM(64)(reshaped_inputs)
# Attention layer
attention = Attention()([lstm_output, lstm_output])
# Output layer for price difference prediction
price_diff_output = Dense(1, activation="linear", name="price_diff_output")(attention)
# Create the model
model = Model(inputs=[news_text_input, stock_price_input, date_input], outputs=price_diff_output)

LEARNING_RATE = 3e-5
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE), loss="mean_squared_error")
model.load_weights("./model/model_weights")

#for testing
#test_text = ["3 Stocks I'm Holding Forever", "1 Unstoppable Stock That Could Join Apple, Microsoft, Nvidia, Amazon, and Alphabet in the $1 Trillion Club", "Jamie Dimon says U.S. consumers are in ‘good shape.’ This evidence proves him wrong."]
#test_label =  ["AAPL", "TSLA", "AMZN"]
#test_price = [186.01, 281.38, 134.68]
#test_date = [datetime(2023, 7, 15), datetime(2023, 7, 16), datetime(2023, 7, 16)]
#test_text_tokenize = []
#test_label_encode = []
#test_unix = []

#for text in test_text:
#    test_text_tokenize.append(tokenizer.encode(text, max_length=150, truncation=True, padding="max_length"))

#for label in test_label:
#    test_label_encode.append(top10_dict[label])

#for d in test_date:
#    test_unix.append(time.mktime(d.timetuple()))

#test_text_tokenize = np.stack(test_text_tokenize)
#test_label_encode = np.stack(test_label_encode).reshape(-1, 1)
#test_unix = np.stack(test_unix).reshape(-1, 1)
#test_price = np.stack(test_price).reshape(-1, 1)

#predictions = model.predict({"news_text_input": test_text_tokenize, "stock_price_input": test_price, "date_input": test_unix})
#print(predictions)


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
        ticker_encode = top10_dict[ticker]
        pred_text_ori = []
        pred_date_ori = []
        pred_text = [] 
        pred_date = []
        pred_ticker = []
        pred_price = []
        #if not in database, need to add them
        for r in result:
            if not stockSentiment.objects.filter(Ticker=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
                pred_text_ori.append(r['title'])
                pred_date_ori.append(r['published_utc'][:10])
                pred_text.append(tokenizer.encode(r['title'], max_length=150, truncation=True, padding="max_length"))
                pred_date.append(time.mktime((datetime.strptime(r['published_utc'][:10], '%Y-%m-%d')).timetuple()))
                pred_ticker.append(ticker_encode)
                pred_price.append(stockPrice.objects.get(Ticker=ticker, date=r['published_utc'][:10]).stock_price)
        if len(pred_text) != 0:
            pred_text = np.stack(pred_text)
            pred_date = np.stack(pred_date).reshape(-1, 1)
            pred_ticker = np.stack(pred_ticker).reshape(-1, 1)
            predictions = model.predict({"news_text_input": pred_text, "stock_price_input": pred_ticker, "date_input": pred_date})
            for i in range(len(predictions)):
                temp_pred = np.sign(predictions[i][0])+1
                #print(temp_pred)
                record = stockSentiment(Ticker=ticker, date=pred_date_ori[i], sentence=pred_text_ori[i], sentiment=temp_pred)
                record.save()
        print(str(index) + " " + ticker + " done.")
    print("end " + str(index))

    

def update_stock_price(index):
    print("start " + str(index))
    start_date = lastUpdate.objects.last().date
    Tickers = top10[:5]
    if index == 4:
        Tickers = top10[5:]
    today = datetime.utcnow().date()
    d = timedelta(days=14)
    a = (today - d).strftime("%Y-%m-%d")
    days_to_update = (today - start_date).days
    start_date = start_date.strftime("%Y-%m-%d")
    for ticker in Tickers:
        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{a}/{today.strftime('%Y-%m-%d')}?adjusted=true&sort=desc&limit=120&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"
        result_json = requests.get(url).json()
        if result_json['resultsCount'] != 0:
            #update stock price for prediction
            for i in range(days_to_update):
                sp = stockPrice(Ticker=ticker, date=(today-timedelta(days=i)), stock_price=result_json['results'][i]['c'])
                sp.save()
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

    if (index == 2):
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
    today = (datetime.utcnow()).strftime("%Y-%m-%d")
    start_day = (datetime.utcnow()-timedelta(days=6)).strftime("%Y-%m-%d")

    if Ticker == "all":
        stock_sentiment = list(stockSentiment.objects.filter(date=today).values("Ticker", "sentiment"))
        return JsonResponse(stock_sentiment, safe=False)
    
    stock_sentiment = list(stockSentiment.objects.filter(date__range=[start_day,today], Ticker=Ticker).values("date", "sentiment"))
    for item in stock_sentiment:
        item['date'] = item['date'].strftime("%Y-%m-%d")
    return JsonResponse(stock_sentiment, safe=False)