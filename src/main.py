import pandas as pd

from src.reports import spending_by_category
from src.services import analyze_cashback
from src.views import main_info

if __name__ == "__main__":
    data_request = "2019-04-10 15:30:00"
    result_view = main_info(data_request)
    print(result_view)

    result_services = analyze_cashback("../data/operations.xlsx", 2018, 3)
    print(result_services)

    df = pd.read_excel("../data/operations.xlsx", sheet_name="Отчет по операциям")
    result_report = spending_by_category(df, "Ж/д билеты", "2019-04-10")
