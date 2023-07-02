from django.contrib import admin

from .models import stockSentiment, stockInfo, updateInfo
# Register your models here.
admin.site.register(stockSentiment)
admin.site.register(stockInfo)
admin.site.register(updateInfo)
