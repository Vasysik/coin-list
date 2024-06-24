from flask import Flask, render_template
import mysql.connector
import json
from datetime import datetime

app = Flask(__name__)

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

@app.route('/')
def index():
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT open_time, open FROM klines ORDER BY open_time")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()

        labels = [row['open_time'].strftime('%Y-%m-%d %H:%M:%S') for row in rows]
        open_prices = [float(row['open']) for row in rows]

        return render_template('index.html', labels=labels, open_prices=open_prices)
    else:
        return "Failed to connect to the database."

if __name__ == "__main__":
    app.run(debug=True)
