"""
Description: Data Quality checks for patient_sum_treatment_cost_per_facility_type dataset.
Requirement(s): TICKET-1234
Author(s): Vladyslav
"""

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def source_data(db_connection):
    source_query = """
    SELECT
        facilities.facility_type AS facility_type,
        CONCAT(patients.first_name, ' ', patients.last_name) AS full_name,
        CAST(SUM(visits.treatment_cost) AS DOUBLE PRECISION) AS sum_treatment_cost
    FROM visits
    JOIN facilities
        ON visits.facility_id = facilities.id
    JOIN patients
        ON visits.patient_id = patients.id
    GROUP BY
        facilities.facility_type,
        CONCAT(patients.first_name, ' ', patients.last_name)
    """
    source = db_connection.get_data_sql(source_query)
    source["sum_treatment_cost"] = pd.to_numeric(
        source["sum_treatment_cost"], errors="coerce"
    )
    return source


@pytest.fixture(scope="module")
def target_data(parquet_reader):
    target_path = "/parquet_data/patient_sum_treatment_cost_per_facility_type"
    target = parquet_reader.process(target_path, include_subfolders=True)
    target = target[["facility_type", "full_name", "sum_treatment_cost"]].copy()
    target["sum_treatment_cost"] = pd.to_numeric(
        target["sum_treatment_cost"], errors="coerce"
    )
    return target


@pytest.mark.parquet_data
@pytest.mark.smoke
@pytest.mark.patient_sum_treatment_cost_per_facility_type
def test_check_dataset_is_not_empty(target_data, data_quality_library):
    data_quality_library.check_dataset_is_not_empty(target_data)


@pytest.mark.parquet_data
@pytest.mark.patient_sum_treatment_cost_per_facility_type
def test_check_data_completeness(source_data, target_data, data_quality_library):
    data_quality_library.check_data_completeness(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.patient_sum_treatment_cost_per_facility_type
def test_check_count(source_data, target_data, data_quality_library):
    data_quality_library.check_count(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.patient_sum_treatment_cost_per_facility_type
def test_check_uniqueness(target_data, data_quality_library):
    data_quality_library.check_duplicates(
        target_data, column_names=["facility_type", "full_name"]
    )


@pytest.mark.parquet_data
@pytest.mark.patient_sum_treatment_cost_per_facility_type
def test_check_not_null_values(target_data, data_quality_library):
    data_quality_library.check_not_null_values(
        target_data,
        ["facility_type", "full_name", "sum_treatment_cost"],
    )


@pytest.mark.parquet_data
@pytest.mark.patient_sum_treatment_cost_per_facility_type
def test_check_non_negative_values(target_data, data_quality_library):
    data_quality_library.check_non_negative_values(
        target_data,
        ["sum_treatment_cost"],
    )
