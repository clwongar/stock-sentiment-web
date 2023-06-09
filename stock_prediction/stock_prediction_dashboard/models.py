from django.db import models

# Create your models here.
class stockInfo(models.Model):
    symbol = models.CharField(max_length=10)
    company_name = models.CharField(max_length=64)

class stockSentiment(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    sentence = models.CharField(max_length=2048)
    sentiment = models.IntegerField()

    def serialize(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "date": self.date.strftime("%b %d %Y"),
            "sentence": self.sentence,
            "sentiment": self.sentiment
        }

