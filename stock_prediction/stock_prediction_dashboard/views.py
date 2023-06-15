import json
from django.http import HttpResponse
from django.shortcuts import render
from .models import stockSentiment, stockInfo
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from polygon import RESTClient
import requests
import urllib.request

#library for models
from transformers import BertTokenizer, TFBertForSequenceClassification
from transformers import InputExample, InputFeatures
import tensorflow as tf
import csv
#import pandas as pd

#for extracting data
client = RESTClient(api_key="31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8")

#model
model = tf.keras.models.load_model('./model/')
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

# Create your views here.
def index(request):
    return render(request, "stock_prediction/dashboard.html")

@csrf_exempt
def stock(request, symbol):

    #for making dropdown
    if symbol == "all":
        stock_info = list(stockInfo.objects.values("symbol"))
        return JsonResponse(stock_info, safe=False)

    #get by date (default latest)
    date = stockSentiment.objects.latest('date').date
    if request.method == "PUT":
        data = json.loads(request.body)
        if data.get("date") != "":
            date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()

    #for generating result
    #count number of different sentiment of specified symbol
    stock_name = stockInfo.objects.get(symbol=symbol).company_name
    stock_sentiment = getStockByDate(symbol, date)
    return JsonResponse([{'name': stock_name, 'sentiment': stock_sentiment}], safe=False)

def bar(request, symbol):
    end_date = stockSentiment.objects.latest('date').date
    start_date = end_date - timedelta(days=6)

    date = []

    stock_name = stockInfo.objects.get(symbol=symbol).company_name
    stock_sentiment = []
    for i in range(7):
        date.append(start_date + timedelta(days=i))
        stock_sentiment.append(getStockByDate(symbol, start_date + timedelta(days=i)))
    
    return JsonResponse([{'name': stock_name, 'date': date, 'sentiment': stock_sentiment}], safe=False)

def allStock(request):
    scores = list(stockSentiment.objects.values('symbol').order_by('symbol').annotate(total=Sum('sentiment')))
    counts = list(stockSentiment.objects.values('symbol').order_by('symbol').annotate(total=Count('sentiment')))

    all_scores = []
    for i in range(len(scores)):
        name = scores[i]['symbol']
        score = (scores[i]['total'] - counts[i]['total']) / counts[i]['total']
        all_scores.append({'symbol': name, 'score': score})

    return JsonResponse(all_scores, safe=False)

def getTimeRange(request):
    latest_date  = stockSentiment.objects.latest('date').date.strftime("%Y-%m-%d") 
    earliest_date = stockSentiment.objects.earliest('date').date.strftime("%Y-%m-%d") 
    return JsonResponse([{'max': latest_date, 'min': earliest_date}], safe=False)

def getStockByDate(symbol, date):
    stock_sentiment = list(stockSentiment.objects.filter(symbol=symbol, date=date).values('sentiment').annotate(total=Count('sentiment')))
    return stock_sentiment


#for model prediction
def predict(pred_sentences, tokenizer, model):
    #Predictons
    tf_batch = tokenizer(pred_sentences, max_length=128, padding=True, truncation=True, return_tensors='tf')
    tf_outputs = model(tf_batch)
    tf_predictions = tf.nn.softmax(tf_outputs['logits'], axis=-1)
    labels = ['Negative','Positive']
    label = tf.argmax(tf_predictions, axis=1)
    label = label.numpy()
    predicted_sentiments = label.tolist()
    return predicted_sentiments

def updatePrediction(request):

    #initialize variables
    pred_dataset = []
    curr_date = stockSentiment.objects.latest('date').date.strftime("%Y-%m-%d")#(datetime.now()-timedelta(hours=8)).strftime("%Y-%m-%d")

    #get all symbols for update
    symbol_query = list(stockInfo.objects.values("symbol").all())
    symbol_str = ""
    symbol_list = []
    for s in symbol_query:
        symbol_str += s['symbol'] + ','
        symbol_list.append(s['symbol'])
    symbol_str = symbol_str[:-1]

    #get results
    url = 'https://api.polygon.io/v2/reference/news?tickers=' + symbol_str + '&published_utc.gte=' + curr_date + '&sort=published_utc&sort=asc&limit=1000&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8'
    result = requests.get(url).json()['results']

    #if not in database, need to add them
    for r in result:
        for ticker in r['tickers']:
            if ticker in symbol_list:
                if not stockSentiment.objects.filter(symbol=ticker, date=r['published_utc'][:10], sentence=r['title']).exists():
                    pred_dataset.append([ticker, r['published_utc'][:10], r['title']])

    #no need to update if nothing
    if len(pred_dataset) == 0:
        return JsonResponse({"message": "no new data"}, status=201)

    #model prediction
    predicted_sentiments = predict([row[2] for row in pred_dataset], tokenizer, model)
    for i in range(len(pred_dataset)):
        record = stockSentiment(symbol=pred_dataset[i][0], date=pred_dataset[i][1], sentence=pred_dataset[i][2], sentiment=predicted_sentiments[i])
        record.save()

    return JsonResponse({"symbol_list": symbol_str, 'url': url, 'content': pred_dataset}, status=201)