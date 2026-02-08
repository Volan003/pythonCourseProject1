import logging
import json
import pandas as pd
from pathlib import Path


log_file_path = Path(__file__).resolve().parent.parent / 'logs' / 'services.log'
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('services')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def analyze_cashback(path_to_file: str, year: int, month: int) -> str:
    """Выбор выгодных категорий кэшбэка"""
    logger.info("Выбираем выгодные категорий кэшбэка")
    df = pd.read_excel(path_to_file)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    filtered_data = df[
        (df["Дата операции"].dt.year == year)
        & (df["Дата операции"].dt.month == month)
    ]

    filtered_data = filtered_data[filtered_data["Кэшбэк"] > 0]
    filtered_data = filtered_data[filtered_data["Сумма платежа"] < 0]

    expenses_by_category = filtered_data.groupby("Категория")["Сумма платежа"].sum()
    cashback_by_category = abs(expenses_by_category) // 100
    result = cashback_by_category.to_dict()
    return json.dumps(result, ensure_ascii=False, indent=4)
