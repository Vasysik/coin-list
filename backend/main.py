import argparse
import requests
import json
from datetime import datetime, timedelta

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
            print(f"Ошибка при выполнении запроса: {e}")
            break
        
        klines = response.json()
        if not klines:
            break

        all_klines.extend(klines)
        
        # Если количество полученных строк меньше лимита, значит мы получили все данные
        if len(klines) < limit:
            break
        
        # Обновляем start_ts для следующего запроса
        start_ts = klines[-1][6] + 1  # +1 чтобы не получить дубликат последнего времени
    
    return all_klines

def format_klines_data(klines):
    formatted_data = []
    for kline in klines:
        kline_data = {
            'open_time': datetime.fromtimestamp(kline[0] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            'open': kline[1],
            # 'high': kline[2],
            # 'low': kline[3],
            # 'close': kline[4],
            # 'volume': kline[5],
            # 'close_time': datetime.fromtimestamp(kline[6] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
            # 'quote_asset_volume': kline[7],
            # 'number_of_trades': kline[8],
            # 'taker_buy_base_asset_volume': kline[9],
            # 'taker_buy_quote_asset_volume': kline[10]
        }
        formatted_data.append(kline_data)
    return formatted_data

def load_existing_data(filename):
    try:
        with open(filename, 'r') as f:
            existing_data = json.load(f)
        return existing_data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Ошибка при чтении файла {filename}. Файл поврежден или имеет неверный формат.")
        return []

def save_to_json(data, filename):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Данные сохранены в файл {filename}")
    except IOError as e:
        print(f"Ошибка при сохранении данных в файл: {e}")

def main(days):
    symbol = 'BTCUSDT'
    interval = '1m'  # Интервал 1 минута
    
    now = datetime.now()
    start_date = now - timedelta(days=days)
    
    start_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
    end_str = now.strftime('%Y-%m-%d %H:%M:%S')
    filename = 'historical_klines.json'

    klines = get_historical_klines(symbol, interval, start_str, end_str)

    if klines:
        formatted_data = format_klines_data(klines)
        
        # Загружаем существующие данные из файла
        existing_data = load_existing_data(filename)
        
        # Исключаем дубликаты
        new_data = [data for data in formatted_data if data not in existing_data]
        
        # Добавляем новые данные к существующим
        updated_data = existing_data + new_data
        
        # Сохраняем обновленные данные в файл
        save_to_json(updated_data, filename)
    else:
        print("Не удалось получить исторические данные.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Запрос и обновление исторических данных курса валют с Binance API в JSON файле.')
    parser.add_argument('--days', type=int, default=1, help='Количество дней для получения и обновления исторических данных (по умолчанию 1)')
    args = parser.parse_args()

    main(args.days)

# python main.py --days 2