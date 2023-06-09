from django.contrib import admin

from .models import stockSentiment, stockInfo
# Register your models here.
admin.site.register(stockSentiment)
admin.site.register(stockInfo)
