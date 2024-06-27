from flask import Flask, render_template
from flask_socketio import SocketIO
import mysql.connector
import json
from datetime import datetime

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

def fetch_data(table_name):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT open_time, open FROM {table_name} ORDER BY open_time"
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        labels = [row['open_time'].strftime('%Y-%m-%d %H:%M:%S') for row in rows]
        open_prices = [float(row['open']) for row in rows]
        return labels, open_prices
    else:
        return [], []

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

@app.route('/')
def index():
    tables = get_tables()
    data = {table: fetch_data(table) for table in tables}
    return render_template('index.html', data=data, tables=tables)

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
