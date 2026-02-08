from datetime import datetime
from typing import Any

import pandas as pd
from pandas import DataFrame
import json
import os
import requests
from dotenv import load_dotenv
import logging
from pathlib import Path
log_file_path = Path(__file__).resolve().parent.parent / 'logs' / 'utils.log'
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('utils')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_KEY_MARKETSTACK = os.getenv("API_KEY_MARKETSTACK")
API_KEY_FCSAPI = os.getenv("API_KEY_FCSAPI")
API_KEY_ALPHAVANTAGE = os.getenv("API_ALPHAVANTAGE")
URL = "https://api.apilayer.com/exchangerates_data/convert"
URL_MARKETSTACK = "https://api.marketstack.com/v2/eod"
URL_fcsapi = "https://api-v4.fcsapi.com/stock/indices_latest"
URL_alphavantage = "https://www.alphavantage.co/query"


def get_time_for_greeting():
    """Принимает время пользователя и выводит приветствие"""
    user_hour = datetime.now().hour
    logger.info("Приветствуем пользователя")
    if 6 <= user_hour < 12:
        return "Доброе утро"
    elif 12 <= user_hour < 18:
        return "Добрый день"
    elif 18 <= user_hour <= 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    dt = datetime.strptime(date_time, date_format)
    start_of_month = dt.replace(day=1)

    return [
        start_of_month.strftime("%d.%m.%Y %H:%M:%S"),
        dt.strftime("%d.%m.%Y %H:%M:%S")
    ]


def get_path_and_period(path_to_file: str, period_date: list) -> DataFrame:
    """Возврат массива данных по заданным датам"""
    df = pd.read_excel(path_to_file, sheet_name="Отчет по операциям")
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    start_date = datetime.strptime(period_date[0], "%d.%m.%Y %H:%M:%S")
    end_date = datetime.strptime(period_date[1], "%d.%m.%Y %H:%M:%S")
    filtered_df = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= end_date)
    ]
    sorted_df = filtered_df.sort_values(by="Дата операции", ascending=True)
    return sorted_df


def get_card_with_spend(sorted_df: DataFrame) -> list[dict]:
    """Вывод списка словарей согласно ТЗ - список карт с расходами"""
    logger.info("Выводим список карт с расходами")
    card_spend_transactions = []
    card_sorted = sorted_df[
        [
            "Номер карты",
            "Сумма операции",
            "Кэшбэк",
            "Сумма операции с округлением"
        ]
    ]
    for index, row in card_sorted.iterrows():
        if row["Сумма операции"] < 0:
            last_digits = str(row["Номер карты"]).replace("*", "")
            total_spent = row["Сумма операции с округлением"]
            cashback = row["Кэшбэк"]
            row_dict = {
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback": cashback
            }
            card_spend_transactions.append(row_dict)
    return card_spend_transactions


def get_top_transactions(sorted_df: DataFrame, get_top):
    """Выборка топ 5 операций по сумме платежа"""
    logger.info("Получаем топ 5 операций")
    top_pay_transactions = []
    sorted_pay_df = sorted_df.sort_values(by="Сумма операции", ascending=False)
    top_transactions = sorted_pay_df.head(get_top)
    top_transactions_sorted = top_transactions[
        [
            "Дата платежа",
            "Сумма операции",
            "Категория",
            "Описание"
        ]
    ]

    for index, row in top_transactions_sorted.iterrows():
        transaction = {
            "date": f"{row['Дата платежа']}",
            "amount": f"{row['Сумма операции']}",
            "category": f"{row['Категория']}",
            "description": f"{row['Описание']}"
        }
        top_pay_transactions.append(transaction)
    return top_pay_transactions


def get_currency(path_to_json: str) -> bool | list[Any] | list[dict[str, str]]:
    """Получение курсов валют"""
    logger.info("Получаем курсы валют")
    currency_rates = []
    try:
        with open(path_to_json, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as ex:
        logger.info(f"Ошибка чтения файла {ex}")
        return False
    currencies = data["user_currencies"]

    for currency in currencies:
        params = {
            "amount": 1,
            "from": f"{currency}",
            "to": "RUB"
        }
        headers = {
            "apikey": API_KEY
        }
        try:
            response = requests.request("GET", URL, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()
                currency_code_response = result["query"]["from"]
                currency_amount = round(result["result"], 2)
                currency_rates.append({
                    "currency": f"{currency_code_response}",
                    "rate": f"{currency_amount}"
                })
        except requests.RequestException as ex:
            logger.error(f"Произошла ошибка: {ex}")
            return []
        except Exception as ex:
            logger.error(f"Произошла ошибка: {ex}")
            return []
    return currency_rates


def get_stock(path_to_json: str) -> list[dict]:
    """Выводим стоимость акций из S&P500"""
    logger.info("Выводим стоимость акций из S&P500")
    stock_rates = []
    with open(path_to_json, 'r', encoding='utf-8') as file:
        data = json.load(file)
        stocks = data['user_stocks']

    for stock in stocks:
        logger.info(f"Запрос цены для акции: {stock}")
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": stock,
            "apikey": API_KEY_ALPHAVANTAGE
        }
        try:
            response = requests.get(URL_alphavantage, params=params)
            status_code = response.status_code
            if status_code != 200:
                print(f"HTTP {status_code} для {stock}")
                continue

            result = response.json()
            quote = result.get("Global Quote")
            if not quote:
                print(f"Нет данных Global Quote для {stock}: {result}")
                continue

            stock_code_response = quote.get("01. symbol", stock)
            stock_rate = quote.get("05. price")
            stock_rates.append({
                "stock": f"{stock_code_response}",
                "price": f"{stock_rate}"
            })
        except requests.RequestException as ex:
            logger.error(f"Произошла ошибка: {ex}")
            return []
        except Exception as ex:
            logger.error(f"Произошла ошибка: {ex}")
            return []

    return stock_rates
