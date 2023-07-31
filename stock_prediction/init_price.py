from stock_prediction_dashboard.models import *
from django.db.models import Sum, Count
from datetime import datetime, timedelta
import numpy as np
import requests
top10 = ["AAPL", "MSFT", "GOOG", "AMZN", "NVDA", "TSLA", "META", "TSM", "AVGO", "ORCL"]
top10_dict = {"AAPL": 0, "MSFT": 5, "GOOG": 3, "AMZN": 1, "NVDA": 6, "TSLA": 8, "META": 4, "TSM": 9, "AVGO": 2, "ORCL": 7}
def update_stock(ticker):
    #get stock price data
    url = "https://api.polygon.io/v2/aggs/ticker/"+ticker+"/range/1/day/2023-01-31/2023-07-30?adjusted=true&sort=desc&apiKey=31wqRQcmAzs0jxj7y3x9W1ROaZ3V2IN8"
    result_json = requests.get(url).json()['results']
    #get average sentiment data
    sentiment_sum = list(stockSentiment.objects.filter(Ticker=ticker).values('date').order_by('date').annotate(total_sentiment=Sum('sentiment')))
    sentiment_count = list(stockSentiment.objects.filter(Ticker=ticker).values('date').order_by('date').annotate(total_count=Count('sentiment')))
    sent_avg = {}
    for i in range(len(sentiment_sum)):
        date = sentiment_sum[i]['date'].strftime("%Y-%m-%d")
        avg = (sentiment_sum[i]['total_sentiment'] - sentiment_count[i]['total_count']) / sentiment_count[i]['total_count']
        sent_avg[date] = avg
    #store stock data, if no stock price data of the day(because of holiday, record old one)
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(current_date_str,"%Y-%m-%d")
    for i in range(len(result_json)-1):
        change = (result_json[i]['c'] - result_json[i+1]['c']) * 100 / result_json[i+1]['c']
        date_str = datetime.utcfromtimestamp(result_json[i]['t']/1000).strftime("%Y-%m-%d")
        date = datetime.strptime(date_str,"%Y-%m-%d")
        while date <= current_date:
            avg_sentiment=0
            if current_date.strftime("%Y-%m-%d") in sent_avg.keys():
                avg_sentiment = sent_avg[current_date.strftime("%Y-%m-%d")]
            s = stockPrice(Ticker=ticker, date=current_date.strftime("%Y-%m-%d"), stock_price=result_json[i]['c'], stock_change=change, avg_sentiment=avg_sentiment)
            s.save()
            current_date = current_date-timedelta(days=1)

#update_stock("AAPL")