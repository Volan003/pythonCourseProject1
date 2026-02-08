import pandas as pd
from pandas import DataFrame
import pytest
import datetime
from unittest.mock import patch

from src.utils import get_time_for_greeting, get_card_with_spend, get_top_transactions, get_path_and_period

@pytest.mark.parametrize(
    "hour, expected",
    [
        (6, "Доброе утро"),
        (9, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (23, "Добрый вечер"),
        (2, "Доброй ночи"),
        (0, "Доброй ночи"),
    ]
)
@patch("src.utils.datetime")
def test_get_time_for_greeting(mock_datetime, hour, expected):
    mock_datetime.now.return_value = datetime.datetime(2026, 1, 30, hour, 0, 0)
    assert get_time_for_greeting() == expected


@pytest.mark.parametrize(
    "df, expected",
    [
        (
            pd.DataFrame([
                {"Номер карты": "1234****5678", "Сумма операции": 50.0,
                 "Кэшбэк": 1.0, "Сумма операции с округлением": 50.0},
                {"Номер карты": "4321****8765", "Сумма операции": 20.0,
                 "Кэшбэк": 0.5, "Сумма операции с округлением": 20.0},
            ]),
            []
        ),

        (
            pd.DataFrame([
                {"Номер карты": "1234****5678", "Сумма операции": -100.0,
                 "Кэшбэк": 2.0, "Сумма операции с округлением": -100.0},
            ]),
            [
                {"last_digits": "12345678", "total_spent": -100.0, "cashback": 2.0}
            ]
        ),

        (
            pd.DataFrame([
                {"Номер карты": "1234****5678", "Сумма операции": -10.0,
                 "Кэшбэк": 0.5, "Сумма операции с округлением": -10.0},
                {"Номер карты": "9999****8888", "Сумма операции": -20.0,
                 "Кэшбэк": 1.0, "Сумма операции с округлением": -20.0},
            ]),
            [
                {"last_digits": "12345678", "total_spent": -10.0, "cashback": 0.5},
                {"last_digits": "99998888", "total_spent": -20.0, "cashback": 1.0},
            ]
        ),
    ],
)
def test_get_card_with_spend_param(df: DataFrame, expected: list[dict]):
    result = get_card_with_spend(df)
    assert result == expected


def _make_df(rows):
    return pd.DataFrame(rows)

@pytest.mark.parametrize(
    "rows, top, expected",
    [
        # кейс 1: две верхние операции
        (
            [
                {"Дата платежа": "2026-01-02", "Сумма операции": 300, "Категория": "B", "Описание": "x2"},
                {"Дата платежа": "2026-01-03", "Сумма операции": 200, "Категория": "A", "Описание": "x3"},
                {"Дата платежа": "2026-01-01", "Сумма операции": 100, "Категория": "A", "Описание": "x1"},
                {"Дата платежа": "2026-01-04", "Сумма операции": 150, "Категория": "C", "Описание": "x4"},
            ],
            2,
            [
                {"date": "2026-01-02", "amount": "300", "category": "B", "description": "x2"},
                {"date": "2026-01-03", "amount": "200", "category": "A", "description": "x3"},
            ],
        ),
        # кейс 2: три верхние операции
        (
            [
                {"Дата платежа": "2026-01-02", "Сумма операции": 300, "Категория": "B", "Описание": "x2"},
                {"Дата платежа": "2026-01-03", "Сумма операции": 200, "Категория": "A", "Описание": "x3"},
                {"Дата платежа": "2026-01-01", "Сумма операции": 100, "Категория": "A", "Описание": "x1"},
                {"Дата платежа": "2026-01-04", "Сумма операции": 150, "Категория": "C", "Описание": "x4"},
            ],
            3,
            [
                {"date": "2026-01-02", "amount": "300", "category": "B", "description": "x2"},
                {"date": "2026-01-03", "amount": "200", "category": "A", "description": "x3"},
                {"date": "2026-01-04", "amount": "150", "category": "C", "description": "x4"},
            ],
        ),
    ],
)
def test_get_top_transactions(rows, top, expected):
    df = _make_df(rows)
    result = get_top_transactions(df, top)
    assert result == expected

def _write_excel_with_sheet(path: Path, df: pd.DataFrame, sheet_name: str = "Отчет по операциям"):
    # Записываем DataFrame в Excel-файл с заданным листом
    df.to_excel(path, sheet_name=sheet_name, index=False)
    return str(path)

@pytest.mark.parametrize(
    "rows, period_date, expected_dates",
    [
        # 1) две записи попадают в период, должны быть отсортированы по Дате операции
        (
            [
                {"Дата операции": "02.01.2020 12:00:00"},
                {"Дата операции": "15.01.2020 10:00:00"},
                {"Дата операции": "31.01.2020 09:00:00"},
                {"Дата операции": "01.02.2020 00:00:00"},
            ],
            ["01.01.2020 00:00:00", "20.01.2020 23:59:59"],
            ["2020-01-02 12:00:00", "2020-01-15 10:00:00"],
        ),
        # 2) нет записей в диапазоне
        (
            [
                {"Дата операции": "01.02.2020 12:00:00"},
            ],
            ["01.01.2020 00:00:00", "31.01.2020 23:59:59"],
            [],  # пустой результат
        ),
    ],
)
def test_get_path_and_period(tmp_path, rows, period_date, expected_dates):
    df = pd.DataFrame(rows)
    # файл в tmp_path
    tmp_file = tmp_path / "data.xlsx"
    path = _write_excel_with_sheet(tmp_file, df)

    result = get_path_and_period(path, period_date)

    if not expected_dates:
        assert result.empty
    else:
        # Дата в результирующем DataFrame приведена к datetime, проверяем порядок
        actual_dates = result["Дата операции"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
        assert actual_dates == expected_dates