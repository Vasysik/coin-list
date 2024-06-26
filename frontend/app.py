from flask import Flask, render_template
from flask_socketio import SocketIO
import mysql.connector
import json
from datetime import datetime
import threading
import time

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

def fetch_data():
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT open_time, open FROM klines ORDER BY open_time")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        labels = [row['open_time'].strftime('%Y-%m-%d %H:%M:%S') for row in rows]
        open_prices = [float(row['open']) for row in rows]
        return labels, open_prices
    else:
        return [], []

@app.route('/')
def index():
    labels, open_prices = fetch_data()
    return render_template('index.html', labels=labels, open_prices=open_prices)

def background_thread():
    while True:
        socketio.sleep(10)
        labels, open_prices = fetch_data()
        socketio.emit('update_data', {'labels': labels, 'open_prices': open_prices})

@socketio.on('connect')
def handle_connect():
    labels, open_prices = fetch_data()
    socketio.emit('update_data', {'labels': labels, 'open_prices': open_prices})

if __name__ == "__main__":
    socketio.start_background_task(target=background_thread)
    socketio.run(app, debug=True)
