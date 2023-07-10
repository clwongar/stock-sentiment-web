import json
from django.http import HttpResponse
from django.shortcuts import render
from .models import *
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import requests
import urllib.request


#library for models
from transformers import BertTokenizer, TFBertForSequenceClassification
from transformers import InputExample, InputFeatures
import tensorflow as tf
import csv

#stocks used
top10 = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA", "META", "TSM", "AVGO", "ORCL"]

#model
model = tf.keras.models.load_model('./model/')
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# Create your views here.
def index(request):
    return render(request, "stock_prediction/dashboard.html")

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

#for auto updating
def update_sentiment(index):

    print("start " + str(index))

    yesterday = (datetime.now() - timedelta(hours=32)).strftime("%Y-%m-%d") 

    Tickers = top10[:5]

    if index == 2:
        Tickers = top10[5:]

    for ticker in Tickers:
        url = 'https://api.polygon.io/v2/reference/news?ticker=' + ticker + '&published_utc.gte=' + yesterday + '&sort=published_utc&sort=asc&limit=1000&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8'
        result = requests.get(url).json()['results']
        pred_dataset = []

        #if not in database, need to add them
        for r in result:
            if not stockSentiment.objects.filter(Ticker=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
                pred_dataset.append([ticker, r['published_utc'][:10], r['title']])

        #model prediction only with values
        if len(pred_dataset) != 0:
            predicted_sentiments = predict([row[2] for row in pred_dataset], tokenizer, model)
            for i in range(len(pred_dataset)):
                record = stockSentiment(Ticker=pred_dataset[i][0], date=pred_dataset[i][1], sentence=pred_dataset[i][2], sentiment=predicted_sentiments[i])
                record.save()

        print(str(index) + " " + ticker + " done.")

    print("end " + str(index))

    

def update_stock_price(index):

    print("start " + str(index))

    Tickers = top10[:5]

    if index == 4:
        Tickers = top10[5:]

    today = datetime.utcnow()
    d = timedelta(days=5)
    a = (today - d).strftime("%Y-%m-%d")

    for ticker in Tickers:

        url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{a}/{today.strftime('%Y-%m-%d')}?adjusted=true&sort=desc&limit=120&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"

        result_json = requests.get(url).json()

        if result_json['resultsCount'] != 0:

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



####not used
@csrf_exempt
def stock(request, Ticker):

    #for making dropdown
    if Ticker == "all":
        stock_info = list(stockInfo.objects.values("Ticker"))
        return JsonResponse(stock_info, safe=False)

    #get by date (default latest)
    date = stockSentiment.objects.latest('date').date
    if request.method == "PUT":
        data = json.loads(request.body)
        if data.get("date") != "":
            date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()

    #for generating result
    #count number of different sentiment of specified Ticker
    stock_name = stockInfo.objects.get(Ticker=Ticker).Name
    stock_sentiment = getStockByDate(Ticker, date)
    return JsonResponse([{'name': stock_name, 'sentiment': stock_sentiment}], safe=False)

def bar(request, Ticker):
    end_date = stockSentiment.objects.latest('date').date
    start_date = end_date - timedelta(days=6)

    date = []

    stock_name = stockInfo.objects.get(Ticker=Ticker).Name
    stock_sentiment = []
    for i in range(7):
        date.append(start_date + timedelta(days=i))
        stock_sentiment.append(getStockByDate(Ticker, start_date + timedelta(days=i)))
    
    return JsonResponse([{'name': stock_name, 'date': date, 'sentiment': stock_sentiment}], safe=False)

def allStock(request):
    scores = list(stockSentiment.objects.values('Ticker').order_by('Ticker').annotate(total=Sum('sentiment')))
    counts = list(stockSentiment.objects.values('Ticker').order_by('Ticker').annotate(total=Count('sentiment')))

    all_scores = []
    for i in range(len(scores)):
        name = scores[i]['Ticker']
        score = (scores[i]['total'] - counts[i]['total']) / counts[i]['total']
        all_scores.append({'Ticker': name, 'score': score})

    return JsonResponse(all_scores, safe=False)

def getTimeRange(request):
    latest_date  = stockSentiment.objects.latest('date').date.strftime("%Y-%m-%d") 
    earliest_date = stockSentiment.objects.earliest('date').date.strftime("%Y-%m-%d") 
    return JsonResponse([{'max': latest_date, 'min': earliest_date}], safe=False)

def getStockByDate(Ticker, date):
    stock_sentiment = list(stockSentiment.objects.filter(Ticker=Ticker, date=date).values('sentiment').annotate(total=Count('sentiment')))
    return stock_sentiment



def updatePrediction(request):

    #initialize variables
    pred_dataset = []
    curr_date = stockSentiment.objects.latest('date').date.strftime("%Y-%m-%d")#(datetime.now()-timedelta(hours=8)).strftime("%Y-%m-%d")

    #get all Tickers for update
    Ticker_query = list(stockInfo.objects.values("Ticker").all())
    Ticker_str = ""
    Ticker_list = []
    for s in Ticker_query:
        Ticker_str += s['Ticker'] + ','
        Ticker_list.append(s['Ticker'])
    Ticker_str = Ticker_str[:-1]

    #get results
    url = 'https://api.polygon.io/v2/reference/news?tickers=' + Ticker_str + '&published_utc.gte=' + curr_date + '&sort=published_utc&sort=asc&limit=1000&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8'
    result = requests.get(url).json()['results']

    #if not in database, need to add them
    for r in result:
        for ticker in r['tickers']:
            if ticker in Ticker_list:
                if not stockSentiment.objects.filter(Ticker=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
                    pred_dataset.append([ticker, r['published_utc'][:10], r['title']])

    #no need to update if nothing
    if len(pred_dataset) == 0:
        return JsonResponse({"message": "no new data", 'url': url}, status=201)

    #model prediction
    predicted_sentiments = predict([row[2] for row in pred_dataset], tokenizer, model)
    for i in range(len(pred_dataset)):
        record = stockSentiment(Ticker=pred_dataset[i][0], date=pred_dataset[i][1], sentence=pred_dataset[i][2], sentiment=predicted_sentiments[i])
        record.save()

    return JsonResponse({"Ticker_list": Ticker_str, 'url': url, 'content': pred_dataset}, status=201)