import argparse
import requests
from datetime import datetime, timedelta
from db import save_klines_to_db

def get_historical_klines(symbol, interval, start_str, end_str=None, limit=1000):
    url = 'https://api.binance.com/api/v3/klines'
    start_ts = int(datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S').timestamp() * 1000)
    end_ts = int(datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S').timestamp() * 1000) if end_str else None

    all_klines = []

    while True:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ts,
            'limit': limit
        }
        
        if end_ts:
            params['endTime'] = end_ts
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error executing request: {e}")
            break
        
        klines = response.json()
        if not klines:
            break

        all_klines.extend(klines)

        if len(klines) < limit:
            break

        start_ts = klines[-1][6] + 1
    
    return all_klines

def format_klines_data(klines):
    formatted_data = []
    for kline in klines:
        kline_data = {
            'open_time': datetime.fromtimestamp(kline[0] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            'open': kline[1]
        }
        formatted_data.append(kline_data)
    return formatted_data

def main(minutes):
    symbol = 'BTCUSDT'
    interval = '1m'
    
    now = datetime.now()
    start_date = now - timedelta(minutes=minutes)
    
    start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_str = now.strftime('%Y-%m-%d %H:%M:%S')

    klines = get_historical_klines(symbol, interval, start_str, end_str)

    if klines:
        formatted_data = format_klines_data(klines)
        save_klines_to_db(formatted_data)
    else:
        print("Failed to retrieve historical data.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query and update historical exchange rate data from the Binance API in a MySQL database.')
    parser.add_argument('--minutes', type=int, default=60, help='Number of minutes to retrieve and update historical data (default 60)')
    args = parser.parse_args()

    main(args.minutes)
