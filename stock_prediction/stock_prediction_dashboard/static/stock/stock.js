var pieChart;
var barChart;

document.addEventListener('DOMContentLoaded', function() {
  update_prediction();
});

function load_page(){
  load_date();
  load_stock_name();
  load_overall_table();
  load_overview();
}

function load_overview(){
  fetch('/stock_prediction/getStockDetails')
  .then(response => response.json())
  .then(stockinfo => {
    stockinfo.forEach((stock) => {   
          var table = document.getElementById("overviewTable");
          var tr = document.createElement("tr");
          create_th('img', stock.ImageURL, tr);
          create_th('str', stock.Ticker, tr);
          create_th('str', stock.Name, tr);
          create_th('float', stock.LatestPrice, tr);
          create_th('percent', stock.PercentageChange, tr);
          create_th('float', stock.Volume, tr);
          create_th('float', stock.MarketCap, tr);
          //create_th('str', stock.Name, tr);
          table.appendChild(tr);

      });
  });
}

function create_th(type, input, tr){
  var th = document.createElement("th");

  if(type == 'img'){
    //th.innerHTML = "<img src='" + input + "'>";
  }
  else if (type == 'float'){
    th.innerText = input.toFixed(2);
  }
  else if(type == 'percent'){
    th.innerText = (input * 100).toFixed(2) + '%';
  }
  else{
    th.innerText = input;
  }

  tr.appendChild(th);

}

function update_prediction(){
  fetch('/stock_prediction/predict')
  .then(response => response.json())
  .then(result => {
      console.log(result);
  })
  .then(() => load_page());  
}

function load_date(){
    var datepicker = document.querySelector('#datepicker');
    var stock_dropdown = document.querySelector('#stock_list');
    datepicker.addEventListener('change', () => load_stock(stock_dropdown.options[stock_dropdown.selectedIndex].value));
    fetch('/stock_prediction/date')
    .then(response => response.json())
    .then(date_list => {
        datepicker.setAttribute("value", date_list[0].max);
        datepicker.setAttribute("max", date_list[0].max);
        datepicker.setAttribute("min", date_list[0].min);
    });
}

function load_stock_name(){

    var stock_dropdown = document.querySelector('#stock_list');

    fetch('/stock_prediction/stock/all')
    .then(response => response.json())
    .then(stock_list => {
        stock_list.forEach((stock) => {
            var option = document.createElement("option");
            option.value = stock.Ticker;
            option.text = stock.Ticker;
            stock_dropdown.appendChild(option);      
        });
        load_stock(stock_list[0].Ticker);
    });

    
    stock_dropdown.addEventListener('change', () => load_stock(stock_dropdown.options[stock_dropdown.selectedIndex].value));
    
    
}

function load_pie_chart(stock_name){
    
    var datepicker = document.querySelector('#datepicker');
    var date = datepicker.value;

    fetch(`/stock_prediction/stock/${stock_name}`, {
        method: 'PUT',
        body: JSON.stringify({
            date: date
        })
      })
    .then(response => response.json())
    .then(stock_info => {
        var stock_name = stock_info[0].name;
        let labels = []
        let data = []

        stock_info[0].sentiment.forEach((info) => {
            labels.push(sentiment_index(info.sentiment));
            data.push(info.total);
        });

        if (pieChart != null)
            pieChart.destroy();
        var ctx = document.getElementById('pie_chart');

        pieChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
              labels: labels,
              datasets: [{
                label: 'Total',
                data: data,
                backgroundColor: [
                  'rgb(255, 99, 132)',
                  'rgb(54, 162, 235)',
                  'rgb(255, 205, 86)'
                ],
                hoverOffset: 4
              }]
            },
            options: {
              scales: {
                y: {
                  beginAtZero: true
                }
              },
              plugins: {
                title: {
                    display: true,
                    text: 'Predicted Sentiment of ' + stock_name
                }
            }
            }
          });


    });
      

}

function load_bar_chart(stock_name){
    fetch(`/stock_prediction/stock/bar/${stock_name}`)
    .then(response => response.json())
    .then(stock_info => {
        var stock_name = stock_info[0].name;
        let dates = stock_info[0].date;
        let data = [];
        
        for (var i = 0; i < 3; i++){
            let arr2 = new Array(7).fill(0);
            data.push(arr2);
        }

        index = 0
        stock_info[0].sentiment.forEach((info) => {        
            info.forEach((sent) => {
              data[sent.sentiment][index] = sent.total;
              
            });
            index+=1;
        });

        console.log(data);

        if (barChart != null)
            barChart.destroy();
        var ctx = document.getElementById('bar_chart');

        barChart = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: dates,
              datasets: [
                {
                  label: 'Negative',
                  data: data[0],
                  backgroundColor: 'rgb(255, 99, 132)',
                },
                {
                  label: 'Neutral',
                  data: data[1],
                  backgroundColor: 'rgb(54, 162, 235)',
                },
                {
                  label: 'Positive',
                  data: data[2],
                  backgroundColor: 'rgb(255, 205, 86)',
                },
              ]
            },
            options: {
              scales: {
                x: {
                    stacked: true
                },
                y: {
                    stacked: true
                }
              },
              plugins: {
                title: {
                    display: true,
                    text: 'Predicted Sentiment of ' + stock_name + ' (weekly)'
                }
            }
            }
          });


    });
}

function load_overall_table(){
  fetch('/stock_prediction/overall')
  .then(response => response.json())
  .then(scores => {
      scores.forEach((score) => {        
          var sign = '+';
          if (score.score < 0) sign = '-';
          var table = document.getElementById("overallTable");
          var tr = document.createElement("tr");
          var th_ticker = document.createElement("th");
          var th_score = document.createElement("th");
          th_ticker.innerText = score.Ticker;
          th_score.innerText = sign + score.score.toFixed(2);;
          tr.appendChild(th_ticker);
          tr.appendChild(th_score);
          table.appendChild(tr);
      });
  });
}

function load_stock(stock_name){
    load_pie_chart(stock_name);
    load_bar_chart(stock_name);
}

function sentiment_index(index){
    if (index == 0) return "negative";
    else if (index == 1) return "neutral";
    else return "positive";
}