from apscheduler.schedulers.background import BackgroundScheduler
from stock_prediction_dashboard.views import dailyUpdate #, update_sentiment, update_stock

def start():

    
    scheduler = BackgroundScheduler()

    #scheduler.add_job(dailyUpdate, "interval", minutes=1, id="stock_001", replace_existing=True)

    #market cap
    scheduler.add_job(dailyUpdate, trigger="cron", args=[5],day='*', hour=6, minute=0,id="stock_005", replace_existing=True)
    scheduler.add_job(dailyUpdate, trigger="cron", args=[6],day='*', hour=6, minute=2,id="stock_006", replace_existing=True)


    #sentiment
    scheduler.add_job(dailyUpdate, trigger="cron", args=[1],day='*', hour=6, minute=4,id="stock_001", replace_existing=True)
    scheduler.add_job(dailyUpdate, trigger="cron", args=[2],day='*', hour=6, minute=6,id="stock_002", replace_existing=True)

    #stock details
    scheduler.add_job(dailyUpdate, trigger="cron", args=[3],day='*', hour=6, minute=8,id="stock_003", replace_existing=True)
    scheduler.add_job(dailyUpdate, trigger="cron", args=[4],day='*', hour=6, minute=10,id="stock_004", replace_existing=True)


    scheduler.start()
