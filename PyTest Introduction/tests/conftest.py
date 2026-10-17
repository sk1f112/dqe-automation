from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture(scope="session")
def path_to_file():
    return (
        Path(__file__).resolve().parents[1]
        / "src"
        / "data"
        / "data.csv"
    )


@pytest.fixture(scope="session")
def csv_data(path_to_file):
    return pd.read_csv(path_to_file)


@pytest.fixture(scope="session")
def expected_schema():
    return ["id", "name", "age", "email", "is_active"]


@pytest.fixture(scope="session")
def actual_schema(csv_data):
    return list(csv_data.columns)


@pytest.fixture(scope="session")
def schema_is_valid(actual_schema, expected_schema):
    return actual_schema == expected_schema


def pytest_collection_modifyitems(items):
    for item in items:
        if not list(item.iter_markers()):
            item.add_marker(pytest.mark.unmarked)