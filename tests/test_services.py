import pytest
import pandas as pd
import json
from src.services import analyze_cashback  # Уточните путь при необходимости


@pytest.fixture
def sample_dataframe():
    """Фикстура с тестовыми данными."""
    return pd.DataFrame({
        "Дата операции": [
            "05.01.2026 10:00:00",
            "15.01.2026 12:00:00",
            "20.02.2026 14:00:00",  # Другой месяц
            "10.01.2026 09:00:00"
        ],
        "Категория": [
            "Продукты",
            "Развлечения",
            "Продукты",
            "Продукты"
        ],
        "Сумма платежа": [-1000, -2000, -1500, -500],  # Отрицательные — расходы
        "Кэшбэк": [10, 20, 15, 5]
    })


def test_analyze_cashback_normal_case(sample_dataframe, tmp_path):
    """Тест: базовый сценарий — корректные данные."""
    # Сохраняем тестовый Excel-файл
    file_path = tmp_path / "test_transactions.xlsx"
    sample_dataframe.to_excel(file_path, index=False)

    result = analyze_cashback(str(file_path), 2026, 1)
    expected = {
        "Продукты": 15,  # (-1000 + -500) = -1500 → abs(-1500) // 100 = 15
        "Развлечения": 20  # -2000 → 20
    }

    assert json.loads(result) == expected


def test_analyze_cashback_no_cashback_transactions(sample_dataframe, tmp_path):
    """Тест: нет транзакций с кэшбэком."""
    df_no_cashback = sample_dataframe.copy()
    df_no_cashback["Кэшбэк"] = 0

    file_path = tmp_path / "no_cashback.xlsx"
    df_no_cashback.to_excel(file_path, index=False)

    result = analyze_cashback(str(file_path), 2026, 1)
    assert json.loads(result) == {}


def test_analyze_cashback_no_negative_payments(sample_dataframe, tmp_path):
    """Тест: нет отрицательных сумм платежа (нет расходов)."""
    df_positive = sample_dataframe.copy()
    df_positive["Сумма платежа"] = 100  # Положительные суммы

    file_path = tmp_path / "positive_payments.xlsx"
    df_positive.to_excel(file_path, index=False)

    result = analyze_cashback(str(file_path), 2026, 1)
    assert json.loads(result) == {}


def test_analyze_cashback_empty_file(tmp_path):
    """Тест: пустой Excel-файл."""
    empty_df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма платежа", "Кэшбэк"])
    file_path = tmp_path / "empty.xlsx"
    empty_df.to_excel(file_path, index=False)

    result = analyze_cashback(str(file_path), 2026, 1)
    assert json.loads(result) == {}
