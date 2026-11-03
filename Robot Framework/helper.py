
import pandas as pd
from pandas.testing import assert_frame_equal
from selenium.webdriver.common.by import By


def read_html_table(table_element):
    """
    Extracts table data from a Selenium WebElement
    and returns it as a Pandas DataFrame.
    """
    columns = table_element.find_elements(By.CLASS_NAME, "y-column")

    headers = []
    column_values = []

    for column in columns:
        header = column.find_element(By.ID, "header").text.strip()
        headers.append(header)

        cells = column.find_elements(By.CLASS_NAME, "cell-text")

        values = [
            cell.text.strip()
            for cell in cells
            if cell.text.strip() != header
        ]

        column_values.append(values)

    table_data = list(zip(*column_values))

    return pd.DataFrame(table_data, columns=headers)


def read_parquet_data(parquet_folder, filter_date=None):
    """Read Parquet data and optionally filter by visit date."""
    import pandas as pd

    df = pd.read_parquet(parquet_folder)

    # Keep only columns represented in the HTML report.
    df = df[
        ["facility_name", "visit_date", "min_time_spent"]
    ].copy()

    if filter_date:
        target_date = pd.to_datetime(filter_date).date()
        df = df[
            pd.to_datetime(df["visit_date"]).dt.date == target_date
        ]

    # Rename Parquet columns to match HTML headers.
    df = df.rename(columns={
        "facility_name": "Facility Type",
        "visit_date": "Visit Date",
        "min_time_spent": "Average Time Spent",
    })

    return df.reset_index(drop=True)


def compare_dataframes(html_df, parquet_df):
    """Compare HTML and Parquet DataFrames exactly."""
    import pandas as pd
    from pandas.testing import assert_frame_equal

    html_df = html_df.copy().reset_index(drop=True)
    parquet_df = parquet_df.copy().reset_index(drop=True)

    if list(html_df.columns) != list(parquet_df.columns):
        return [
            "Column mismatch:",
            f"HTML: {list(html_df.columns)}",
            f"Parquet: {list(parquet_df.columns)}",
        ]

    # Normalize date and numeric values before comparison.
    html_df["Visit Date"] = pd.to_datetime(
        html_df["Visit Date"]
    ).dt.strftime("%Y-%m-%d")

    parquet_df["Visit Date"] = pd.to_datetime(
        parquet_df["Visit Date"]
    ).dt.strftime("%Y-%m-%d")

    html_df["Average Time Spent"] = pd.to_numeric(
        html_df["Average Time Spent"]
    )

    parquet_df["Average Time Spent"] = pd.to_numeric(
        parquet_df["Average Time Spent"]
    )

    try:
        assert_frame_equal(
            html_df,
            parquet_df,
            check_dtype=False,
            check_exact=True,
        )
    except AssertionError as error:
        return [str(error)]

    return []