"""Reusable data quality assertions for pandas DataFrames."""

from typing import List, Optional

import pandas as pd


class DataQualityLibrary:
    """Assertions used by the PyTest DQ test modules."""

    @staticmethod
    def check_dataset_is_not_empty(df: pd.DataFrame) -> None:
        assert not df.empty, "Dataset is empty"

    @staticmethod
    def check_data_completeness(
        df_expected: pd.DataFrame, df_actual: pd.DataFrame
    ) -> None:
        expected_columns = list(df_expected.columns)
        actual_columns = list(df_actual.columns)
        if set(expected_columns) != set(actual_columns):
            missing = sorted(set(expected_columns) - set(actual_columns))
            unexpected = sorted(set(actual_columns) - set(expected_columns))
            raise AssertionError(
                "Dataset columns do not match; "
                f"missing from actual: {missing}; unexpected in actual: {unexpected}"
            )

        actual = df_actual.loc[:, expected_columns]
        if len(df_expected) != len(actual):
            raise AssertionError(
                "Dataset row counts differ: "
                f"expected={len(df_expected)}, actual={len(actual)}"
            )

        try:
            expected_sorted = df_expected.sort_values(
                by=expected_columns, na_position="last", kind="mergesort"
            ).reset_index(drop=True)
            actual_sorted = actual.sort_values(
                by=expected_columns, na_position="last", kind="mergesort"
            ).reset_index(drop=True)
            pd.testing.assert_frame_equal(
                expected_sorted,
                actual_sorted,
                check_dtype=False,
                check_like=False,
            )
        except (AssertionError, TypeError) as error:
            raise AssertionError(
                "Expected and actual datasets differ. "
                f"Expected sample: {df_expected.head(5).to_dict(orient='records')}; "
                f"actual sample: {df_actual.head(5).to_dict(orient='records')}. "
                f"Details: {error}"
            ) from error

    @staticmethod
    def check_count(df_expected: pd.DataFrame, df_actual: pd.DataFrame) -> None:
        expected_count = len(df_expected)
        actual_count = len(df_actual)
        assert expected_count == actual_count, (
            f"Dataset row counts differ: expected={expected_count}, "
            f"actual={actual_count}"
        )

    @staticmethod
    def check_duplicates(
        df: pd.DataFrame, column_names: Optional[List[str]] = None
    ) -> None:
        columns = column_names if column_names is not None else list(df.columns)
        missing_columns = sorted(set(columns) - set(df.columns))
        if missing_columns:
            raise AssertionError(f"Columns not found in dataset: {missing_columns}")
        if not columns:
            raise AssertionError("Cannot check duplicates without columns")

        duplicate_mask = df.duplicated(subset=columns, keep=False)
        duplicates = df.loc[duplicate_mask, columns]
        assert duplicates.empty, (
            f"Found {len(duplicates)} rows with duplicate values for "
            f"columns {columns}. Samples: "
            f"{duplicates.head(5).to_dict(orient='records')}"
        )

    @staticmethod
    def check_not_null_values(
        df: pd.DataFrame, column_names: Optional[List[str]] = None
    ) -> None:
        if column_names is None:
            columns = list(df.columns)
        else:
            columns = column_names

        missing_columns = sorted(set(columns) - set(df.columns))
        if missing_columns:
            raise AssertionError(f"Columns not found in dataset: {missing_columns}")
        if not columns:
            raise AssertionError("No columns were specified for the not-null check")

        null_counts = df.loc[:, columns].isnull().sum()
        null_counts = null_counts[null_counts > 0]
        assert null_counts.empty, (
            "Found null values in columns: "
            f"{null_counts.to_dict()}"
        )

    @staticmethod
    def check_non_negative_values(
        df: pd.DataFrame, column_names: List[str]
    ) -> None:
        missing_columns = sorted(set(column_names) - set(df.columns))
        if missing_columns:
            raise AssertionError(f"Columns not found in dataset: {missing_columns}")
        if not column_names:
            raise AssertionError(
                "No columns were specified for the non-negative check"
            )

        DataQualityLibrary.check_not_null_values(df, column_names)

        negative_values = {
            column: df.loc[df[column] < 0, column].tolist()
            for column in column_names
            if (df[column] < 0).any()
        }
        assert not negative_values, (
            "Found negative values in columns: "
            f"{negative_values}"
        )
