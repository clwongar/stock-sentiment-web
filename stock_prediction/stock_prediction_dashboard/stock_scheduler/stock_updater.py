from apscheduler.schedulers.background import BackgroundScheduler
from stock_prediction_dashboard.views import dailyUpdate #, update_sentiment, update_stock

def start():

    
    scheduler = BackgroundScheduler()

    #scheduler.add_job(dailyUpdate, "interval", minutes=1, id="stock_001", replace_existing=True)


    #stock details
    scheduler.add_job(dailyUpdate, trigger="cron", args=[3],day='*', hour=19, minute=40,id="stock_003", replace_existing=True)
    scheduler.add_job(dailyUpdate, trigger="cron", args=[4],day='*', hour=19, minute=42,id="stock_004", replace_existing=True)

    #market cap
    scheduler.add_job(dailyUpdate, trigger="cron", args=[5],day='*', hour=19, minute=44,id="stock_005", replace_existing=True)
    scheduler.add_job(dailyUpdate, trigger="cron", args=[6],day='*', hour=19, minute=46,id="stock_006", replace_existing=True)


    #sentiment
    scheduler.add_job(dailyUpdate, trigger="cron", args=[1],day='*', hour=19, minute=48,id="stock_001", replace_existing=True)
    scheduler.add_job(dailyUpdate, trigger="cron", args=[2],day='*', hour=19, minute=50,id="stock_002", replace_existing=True)



    scheduler.start()
