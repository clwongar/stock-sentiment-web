from django.contrib import admin

from .models import *
# Register your models here.
admin.site.register(stockSentiment)
admin.site.register(stockInfo)
admin.site.register(stockPrice)
admin.site.register(lastUpdate)
