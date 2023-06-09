from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    #path("tmp", views.updatePrediction, name="tmp"),
    path("stock/<str:symbol>", views.stock, name="stock"),
    path("stock/bar/<str:symbol>", views.bar, name="bar"),
    path("date", views.getTimeRange, name="date")
]