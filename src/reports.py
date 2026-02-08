import functools
import logging
from builtins import str
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

import pandas as pd
from pandas import Series

log_file_path = Path(__file__).resolve().parent.parent / 'logs' / 'reports.log'
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('reports')
file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
file_formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def report_decorator(filename=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Проверка, что результат — DataFrame
            if not isinstance(result, pd.DataFrame):
                logger.warning(f"Результат {func.__name__} не является DataFrame. Сохранение в CSV пропущено.")
                return result

            # Генерация имени файла
            if filename is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
                file_name = f"{func.__name__}_{date_str}.csv"
            else:
                file_name = filename

            # Проверка на пустоту
            if result.empty:
                logger.info(f"DataFrame пуст. Файл {file_name} не будет сохранён.")
                return result

            # Сохранение с обработкой ошибок
            try:
                result.to_csv(file_name, index=False, encoding="utf-8-sig")  # utf-8-sig для Excel
                logger.info(f"Отчёт сохранён в {file_name}")
                print(f"Отчёт сохранён в {file_name}")
            except (PermissionError, FileNotFoundError, OSError) as e:
                logger.error(f"Ошибка при сохранении файла {file_name}: {e}")
                raise

            return result

        return wrapper

    return decorator


@report_decorator()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None
) -> Series[Any]:
    """
    Возвращает траты по заданной категории за последние три месяца.
    Если дата не передана — используется текущая дата.
    """
    # Проверка обязательных столбцов
    required_columns = ["Дата операции", "Категория"]
    for col in required_columns:
        if col not in transactions.columns:
            raise ValueError(f"Столбец '{col}' отсутствует в данных.")

    # Обработка даты
    if date is None:
        reference_date = datetime.now()
    else:
        reference_date = pd.to_datetime(date, dayfirst=True)

    three_months_ago = reference_date - timedelta(days=90)

    # Фильтрация
    filtered = transactions[
        (pd.to_datetime(transactions["Дата операции"], dayfirst=True, errors="coerce") >= three_months_ago)
        & (pd.to_datetime(transactions["Дата операции"], dayfirst=True, errors="coerce") <= reference_date)
        & (transactions["Категория"] == category)
    ].copy()

    return filtered
