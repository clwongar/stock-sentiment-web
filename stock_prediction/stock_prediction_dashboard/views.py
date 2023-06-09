import json
from django.http import HttpResponse
from django.shortcuts import render
from .models import stockSentiment, stockInfo
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta

#library for models
#from transformers import BertTokenizer, TFBertForSequenceClassification
#from transformers import InputExample, InputFeatures
#import tensorflow as tf
#import pandas as pd

# Create your views here.
def index(request):
    return render(request, "stock_prediction/dashboard.html", {
        "stock_info": stockSentiment.objects.all() 
    })

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
def predict(pred_sentences, model):
    #Predictons
    tf_batch = tokenizer(pred_sentences, max_length=128, padding=True, truncation=True, return_tensors='tf')
    tf_outputs = model(tf_batch)
    tf_predictions = tf.nn.softmax(tf_outputs['logits'], axis=-1)
    labels = ['Negative','Positive']
    label = tf.argmax(tf_predictions, axis=1)
    label = label.numpy()
    predicted_sentiments = label.tolist()
    return predicted_sentiments

#def updatePrediction(request):
#    pred_sentences = ['Market share decreased on the route between Helsinki in Finland and Tallinn in Estonia by 0.1 percentage points to 24.8 % .', '$AAPL $131 rally mode', '$MSFT SQL Server revenue grew double-digit with SQL Server Premium revenue growing over 30% http://stks.co/ir2F', 'Koduextra is operating a retail chain of 11 stores , controlled by Finnish Non-Food Center KY , Rukax OY , and Scan-Tukka OY .', 'EA Launches Origin Online Game Distribution for Mac http://stks.co/aKTU via MacRumors $EA', 'Finnish fibers and plastic products maker Suominen Corporation said its net loss from continuing operations narrowed to 1.8 mln euro ( $ 2.3 mln ) in 2006 from 3.7 mln euro ( $ 4.8 mln ) in 2005 .']
#    model = tf.keras.models.load_model('./model/')
#    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
#    predicted_sentiments = predict(pred_sentences, model)
#    return JsonResponse([{'sentence': pred_sentences, 'sentiment': predicted_sentiments}], safe=False)