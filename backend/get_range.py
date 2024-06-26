import argparse
import requests
from datetime import datetime, timedelta
import json
import logging
from db import save_klines_to_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            logger.error(f"Error executing request: {e}")
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

def get_all_symbols():
    url = 'https://api.binance.com/api/v3/ticker/price'
    try:
        response = requests.get(url)
        response.raise_for_status()
        symbols = [item['symbol'] for item in response.json() if item['symbol'].endswith('USDT')]
        return symbols
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching symbols: {e}")
        return []

def main(minutes, coins):
    interval = '1m'
    
    now = datetime.now()
    start_date = now - timedelta(minutes=minutes)
    
    start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_str = now.strftime('%Y-%m-%d %H:%M:%S')

    for symbol in coins:
        logger.info(f"Fetching data for {symbol}")
        klines = get_historical_klines(symbol, interval, start_str, end_str)

        if klines:
            formatted_data = format_klines_data(klines)
            save_klines_to_db(formatted_data, symbol)
            logger.info(f"Successfully saved data for {symbol}")
        else:
            logger.warning(f"Failed to retrieve historical data for {symbol}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query and update historical exchange rate data from the Binance API in a MySQL database.')
    parser.add_argument('--minutes', type=int, default=60, help='Number of minutes to retrieve and update historical data (default 60)')
    parser.add_argument('--coin', type=str, default='BTCUSDT', help='Coin symbol(s) to retrieve data for (e.g., BTCUSDT, "BTCUSDT,ETHUSDT", list.json, or all)')
    args = parser.parse_args()

    if args.coin.startswith('[') and args.coin.endswith(']'):
        coins = args.coin.strip('[]').split(',')
    elif args.coin == 'all':
        coins = get_all_symbols()
    elif args.coin.endswith('.json'):
        with open(args.coin, 'r') as file:
            coins = json.load(file)
    else:
        coins = [args.coin]

    main(args.minutes, coins)
