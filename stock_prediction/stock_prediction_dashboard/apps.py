from django.apps import AppConfig


class StockPredictionDashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock_prediction_dashboard'

    def ready(self):
        print("starting")
        from .stock_scheduler import stock_updater
        stock_updater.start()
        print("started")
