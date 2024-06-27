from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import mysql.connector
import json
from datetime import datetime, timedelta

app = Flask(__name__)
socketio = SocketIO(app)

def load_db_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    return config

def create_connection():
    config = load_db_config()
    try:
        connection = mysql.connector.connect(
            host=config['host'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
    return None

def fetch_data(table_name, start_date, end_date, interval):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT open_time, open FROM {table_name} WHERE open_time BETWEEN %s AND %s ORDER BY open_time"
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        if interval:
            rows = aggregate_data(rows, interval)

        labels = [row['open_time'].strftime('%Y-%m-%d %H:%M:%S') for row in rows]
        open_prices = [float(row['open']) for row in rows]
        return labels, open_prices
    else:
        return [], []

def aggregate_data(rows, interval):
    aggregated_data = []
    current_period_start = None
    current_period_data = []

    def round_time(dt, delta):
        return dt - (dt - datetime.min) % delta

    for row in rows:
        open_time = row['open_time']
        open_price = float(row['open'])

        if current_period_start is None:
            current_period_start = round_time(open_time, interval)

        if open_time >= current_period_start + interval:
            average_open = sum([data['open'] for data in current_period_data]) / len(current_period_data)
            aggregated_data.append({
                'open_time': current_period_start,
                'open': average_open
            })
            current_period_start = round_time(open_time, interval)
            current_period_data = []

        current_period_data.append(row)

    if current_period_data:
        average_open = sum([data['open'] for data in current_period_data]) / len(current_period_data)
        aggregated_data.append({
            'open_time': current_period_start,
            'open': average_open
        })

    return aggregated_data

@app.route('/data/<table_name>/<start_date>/<end_date>/<interval>')
def data_in_range(table_name, start_date, end_date, interval):
    intervals = {
        "1h": None,
        "1d": timedelta(minutes=5),
        "1w": timedelta(hours=1),
        "1m": timedelta(hours=6),
        "1y": timedelta(days=1)
    }
    labels, open_prices = fetch_data(table_name, start_date, end_date, intervals.get(interval))
    return jsonify(labels=labels, open_prices=open_prices)

@app.route('/')
def index():
    tables = get_tables()
    return render_template('index.html', tables=tables)

def get_tables():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return tables
    return []

def background_thread():
    while True:
        socketio.sleep(10)
        tables = get_tables()
        data = {table: fetch_data(table) for table in tables}
        socketio.emit('update_data', data)

@socketio.on('connect')
def handle_connect():
    tables = get_tables()
    data = {table: fetch_data(table) for table in tables}
    socketio.emit('update_data', data)

if __name__ == "__main__":
    socketio.start_background_task(target=background_thread)
    socketio.run(app, debug=True)
