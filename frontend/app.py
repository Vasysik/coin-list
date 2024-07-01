from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from influxdb_client import InfluxDBClient
import json
from datetime import datetime, timedelta
from dateutil import parser, tz

app = Flask(__name__)
socketio = SocketIO(app)

def load_db_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    return config

def load_coin_list():
    with open('coin_list.json', 'r') as file:
        coin_list = json.load(file)
    return coin_list

def create_influxdb_client():
    config = load_db_config()
    client = InfluxDBClient(url=config['url'], token=config['token'], org=config['org'])
    return client

def fetch_data(symbol, start_date, end_date, interval):
    config = load_db_config()
    client = create_influxdb_client()
    query_api = client.query_api()
    query = f'''
    from(bucket: "{config['bucket']}")
    |> range(start: {start_date.isoformat()}, stop: {end_date.isoformat()})
    |> filter(fn: (r) => r["_measurement"] == "klines" and r["symbol"] == "{symbol}")
    |> filter(fn: (r) => r["_field"] == "open")
    |> aggregateWindow(every: {interval}, fn: mean, createEmpty: false)
    |> yield(name: "mean")
    '''
    tables = query_api.query(query)
    labels = []
    open_prices = []
    for table in tables:
        for record in table.records:
            labels.append(record.get_time().strftime('%Y-%m-%d %H:%M:%S'))
            open_prices.append(record.get_value())
    return labels, open_prices

@app.route('/data/<symbol>/<start_date>/<end_date>/<interval>')
def data_in_range(symbol, start_date, end_date, interval):
    start_date = parser.parse(start_date).astimezone(tz.UTC)
    end_date = parser.parse(end_date).astimezone(tz.UTC)
    
    intervals = {
        "1h": "1m",
        "1d": "5m",
        "1w": "1h",
        "1m": "6h",
        "1y": "1d"
    }
    labels, open_prices = fetch_data(symbol, start_date, end_date, intervals.get(interval, "5m"))
    return jsonify(labels=labels, open_prices=open_prices)

@app.route('/')
def index():
    symbols = load_coin_list()
    return render_template('index.html', tables=symbols)

if __name__ == "__main__":
    socketio.run(app, debug=True)
