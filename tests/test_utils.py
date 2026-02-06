import pandas as pd
from pandas import DataFrame
import pytest
import datetime
from unittest.mock import patch

from src.utils import get_time_for_greeting, get_card_with_spend


@patch("src.utils.datetime")
def test_get_time_for_greeting(mock_datetime):
    mock_datetime.now.return_value = datetime.datetime(2026, 1, 30, 18, 59, 59)
    assert get_time_for_greeting() == "Добрый вечер"


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
