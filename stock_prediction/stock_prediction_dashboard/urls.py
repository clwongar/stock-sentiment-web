from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("predict", views.updatePrediction, name="predict"),
    path("overall", views.allStock, name="overall"),
    path("stock/<str:Ticker>", views.stock, name="stock"),
    path("stock/bar/<str:Ticker>", views.bar, name="bar"),
    path("date", views.getTimeRange, name="date"),
    path("getStockDetails", views.getStockDetails, name="getStockDetails"),
    path("getStockImg", views.getStockImg, name="getStockImg")
]