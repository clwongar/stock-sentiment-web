# stock-sentiment-web
 
 ### Set up environment
 ```
 conda install -c anaconda django
 conda create msc python=3.8
 conda activate msc
 conda install -c anaconda django
 pip install tensorflow
 pip install transformers
 pip install moment
 ```

Need to copy Model and Frontend folder in ./stock-sentiment-web/stock_prediction

### Open Django (port 8000)
 ```
cd YOURPATH\stock-sentiment-web\stock_prediction
py manage.py runserver
 ```

### Open Frontend (changed utils/global.js server_baseURL to 'http://127.0.0.1:8000/stock_prediction')
 ```
cd YOURPATH\stock-sentiment-web\stock_prediction\Frontend
npm run dev
 ```

Go to http://localhost:3000 and can see the webpage
