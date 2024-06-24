import mysql.connector
from mysql.connector import Error
import json

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
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    return None

def create_table_if_not_exists(connection):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS klines (
        open_time DATETIME PRIMARY KEY,
        open DECIMAL(18, 8)
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_query)
        connection.commit()
    except Error as e:
        print(f"Error creating table: {e}")

def save_klines_to_db(klines):
    connection = create_connection()
    if connection:
        create_table_if_not_exists(connection)
        insert_query = """
        INSERT INTO klines (open_time, open)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
        open=VALUES(open)
        """
        klines_data = [(k['open_time'], k['open']) for k in klines]
        
        try:
            cursor = connection.cursor()
            cursor.executemany(insert_query, klines_data)
            connection.commit()
        except Error as e:
            print(f"Error inserting data into MySQL: {e}")
        finally:
            cursor.close()
            connection.close()
    else:
        print("Failed to connect to the database.")
