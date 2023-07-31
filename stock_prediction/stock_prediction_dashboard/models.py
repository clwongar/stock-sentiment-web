from django.db import models
from datetime import date

# Create your models here.
class lastUpdate(models.Model):
    date = models.DateField(default=date.today)

class stockInfo(models.Model):
    Ticker = models.CharField(max_length=45)
    Name = models.CharField(max_length=64)
    ImageURL = models.CharField(max_length=200, default="null")
    MarketCap = models.FloatField(default=0)
    LatestPrice = models.FloatField(default=0)
    PrevPrice = models.FloatField(default=0)
    Volume = models.FloatField(default=0)
    PredictPrice = models.FloatField(default=0)

    def serialize(self):
        return {
            "id": self.id,
            "ImageURL": self.ImageURL,
            "MarketCap": self.MarketCap,
            "Ticker": self.Ticker,
            "Name": self.Name, 
            "LatestPrice": self.LatestPrice,
            "PrevPrice": self.PrevPrice,
            #"PercentageChange": (self.LatestPrice - self.PrevPrice) / self.PrevPrice,
            "Volume": self.Volume
        }

class stockSentiment(models.Model):
    Ticker = models.CharField(max_length=10)
    date = models.DateField()
    sentence = models.CharField(max_length=2048)
    sentiment = models.IntegerField()

    def serialize(self):
        return {
            "id": self.id,
            "Ticker": self.Ticker,
            "date": self.date.strftime("%b %d %Y"),
            "sentence": self.sentence,
            "sentiment": self.sentiment
        }
    
class stockPrice(models.Model):
    Ticker = models.CharField(max_length=10)
    date = models.DateField(default=date.today)
    stock_price = models.FloatField(default=0)
    stock_change = models.FloatField(default=0)
    avg_sentiment = models.FloatField(default=0)

