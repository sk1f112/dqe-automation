import pandas as pd
import pytest


def test_file_not_empty(csv_data):
    assert not csv_data.empty, "CSV file is empty"


@pytest.mark.validate_csv
def test_validate_schema(
    csv_data, actual_schema, expected_schema, schema_is_valid
):
    assert schema_is_valid, (
        f"Schema mismatch. Expected: {expected_schema}; "
        f"Actual: {actual_schema}"
    )

    assert pd.api.types.is_integer_dtype(csv_data["id"]), (
        "Column 'id' must contain integers"
    )
    assert pd.api.types.is_string_dtype(csv_data["name"]), (
        "Column 'name' must contain strings"
    )
    assert pd.api.types.is_integer_dtype(csv_data["age"]), (
        "Column 'age' must contain integers"
    )
    assert pd.api.types.is_string_dtype(csv_data["email"]), (
        "Column 'email' must contain strings"
    )
    assert pd.api.types.is_bool_dtype(csv_data["is_active"]), (
        "Column 'is_active' must contain boolean values"
    )


@pytest.mark.validate_csv
@pytest.mark.skip(reason="Skipped as required by the assignment")
def test_age_column_valid(csv_data):
    assert csv_data["age"].between(0, 100).all(), (
        "Age values must be between 0 and 100 inclusive"
    )


@pytest.mark.validate_csv
def test_email_column_valid(csv_data):
    email_pattern = (
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
        r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+"
    )

    valid_emails = csv_data["email"].str.fullmatch(
        email_pattern, na=False
    )

    assert valid_emails.all(), (
        f"Invalid emails found:\n"
        f"{csv_data.loc[~valid_emails, 'email']}"
    )


@pytest.mark.validate_csv
@pytest.mark.xfail(
    reason="Expected failure mark required by the assignment"
)
def test_duplicates(csv_data):
    duplicates = csv_data[csv_data.duplicated(keep=False)]

    assert duplicates.empty, (
        f"Found duplicate rows in CSV:\n{duplicates}"
    )


@pytest.mark.parametrize(
    "id, is_active",
    [
        (1, False),
        (2, True),
    ],
)
def test_is_active_by_id(csv_data, id, is_active):
    row = csv_data.loc[csv_data["id"] == id, "is_active"]

    assert len(row) == 1, (
        f"Expected exactly one row for id={id}, found {len(row)}"
    )
    assert row.iloc[0] == is_active, (
        f"Expected is_active={is_active} for id={id}, "
        f"got {row.iloc[0]}"
    )


def test_id_2_is_active(csv_data):
    row = csv_data.loc[csv_data["id"] == 2, "is_active"]

    assert len(row) == 1, (
        f"Expected exactly one row for id=2, found {len(row)}"
    )
    assert row.iloc[0] == True, (
        f"Expected is_active=True for id=2, got {row.iloc[0]}"
    )