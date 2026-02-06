import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch
import logging
from src.reports import spending_by_category


@pytest.fixture
def sample_transactions():
    """Фикстура с тестовыми транзакциями."""
    return pd.DataFrame({
        "Дата операции": [
            "01.01.2026",
            "15.02.2026",
            "10.03.2026",
            "20.04.2026"
        ],
        "Категория": [
            "Продукты",
            "Развлечения",
            "Продукты",
            "Транспорт"
        ],
        "Сумма": [100, 200, 150, 50]
    })


def test_spending_by_category_filter_by_category(sample_transactions):
    """Тест: фильтрация по категории."""
    result = spending_by_category(sample_transactions, "Продукты")

    assert len(result) == 1
    assert (result["Категория"] == "Продукты").all()
    assert list(result["Сумма"]) == [100]


def test_spending_by_category_no_matching_category(sample_transactions):
    """Тест: категория не найдена."""
    result = spending_by_category(sample_transactions, "Одежда")

    assert result.empty


def test_spending_by_category_default_date():
    """Тест: использование текущей даты по умолчанию."""
    # Мокируем datetime.now() для предсказуемости
    mock_date = datetime(2026, 4, 20)
    with patch("src.utils.datetime", wraps=datetime) as mocked_datetime:
        mocked_datetime.now.return_value = mock_date

        # Создаём транзакции с датами в пределах 3 месяцев от 20.04.2026
        transactions = pd.DataFrame({
            "Дата операции": ["01.02.2026", "15.03.2026"],
            "Категория": ["Продукты", "Продукты"],
            "Сумма": [100, 150]
        })

        result = spending_by_category(transactions, "Продукты")

        assert len(result) == 1


def test_spending_by_category_invalid_column():
    """Тест: отсутствие обязательного столбца."""
    transactions = pd.DataFrame({
        "Дата": ["01.01.2026"],  # Нет столбца "Дата операции"
        "Категория": ["Продукты"]
    })

    with pytest.raises(ValueError, match="Столбец 'Дата операции' отсутствует в данных."):
        spending_by_category(transactions, "Продукты")


def test_spending_by_category_empty_input():
    """Тест: пустой DataFrame на входе."""
    empty_df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма"])
    result = spending_by_category(empty_df, "Продукты")

    assert result.empty


def test_spending_by_category_malformed_date():
    """Тест: некорректная дата в данных."""
    transactions = pd.DataFrame({
        "Дата операции": ["некорректная_дата", "15.02.2026"],
        "Категория": ["Продукты", "Продукты"],
        "Сумма": [100, 150]
    })

    result = spending_by_category(transactions, "Продукты", "01.03.2026")

    # Транзакция с некорректной датой будет отфильтрована (pd.to_datetime → NaT)
    assert len(result) == 1
    assert result.iloc[0]["Дата операции"] == "15.02.2026"


def test_spending_by_category_logging(sample_transactions, caplog):
    """Тест: проверка логирования."""
    with caplog.at_level(logging.INFO):
        spending_by_category(sample_transactions, "Продукты")

    assert "Отчёт сохранён в spending_by_category_" in caplog.text
