import json
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import logging

logger = logging.getLogger(__name__)

def load_db_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    return config

def create_influxdb_client():
    config = load_db_config()
    client = InfluxDBClient(url=config['url'], token=config['token'], org=config['org'])
    return client

def save_klines_to_influxdb(klines, symbol):
    client = create_influxdb_client()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    config  = load_db_config()
    bucket = config['bucket']

    points = []
    for kline in klines:
        point = Point("klines").tag("symbol", symbol).field("open", float(kline['open'])).time(kline['open_time'])
        points.append(point)
    
    try:
        write_api.write(bucket=bucket, record=points)
    except Exception as e:
        logger.error(f"Error inserting data into InfluxDB: {e}")
    finally:
        write_api.close()
        client.close()
