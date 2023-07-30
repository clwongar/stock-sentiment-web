from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("stock/<str:Ticker>", views.stock, name="stock"),
    path("getStockDetails", views.getStockDetails, name="getStockDetails"),
    path("getStockImg", views.getStockImg, name="getStockImg")
]