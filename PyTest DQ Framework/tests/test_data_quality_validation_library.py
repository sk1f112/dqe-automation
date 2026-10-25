import pandas as pd
import pytest

from src.data_quality.data_quality_validation_library import DataQualityLibrary


@pytest.mark.parametrize(
    "values",
    [
        [1.25, 2.5],
        [0, 1.25, 0.0],
    ],
    ids=["positive-values", "zero-is-allowed"],
)
def test_check_non_negative_values_accepts_non_negative_values(values):
    df = pd.DataFrame({"sum_treatment_cost": values})

    DataQualityLibrary.check_non_negative_values(df, ["sum_treatment_cost"])


def test_check_non_negative_values_reports_negative_values():
    df = pd.DataFrame({"sum_treatment_cost": [12.5, -1.25, 0]})

    with pytest.raises(
        AssertionError,
        match=r"Found negative values in columns: .*'sum_treatment_cost': \[-1.25\]",
    ):
        DataQualityLibrary.check_non_negative_values(df, ["sum_treatment_cost"])


def test_check_non_negative_values_rejects_null_values():
    df = pd.DataFrame({"sum_treatment_cost": [12.5, None]})

    with pytest.raises(
        AssertionError,
        match=r"Found null values in columns: \{'sum_treatment_cost': 1\}",
    ):
        DataQualityLibrary.check_non_negative_values(df, ["sum_treatment_cost"])
