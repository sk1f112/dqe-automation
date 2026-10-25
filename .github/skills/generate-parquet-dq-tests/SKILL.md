---
name: generate-parquet-dq-tests
description: >-
  Explicitly generate one mapping-based PyTest DQ module for a Parquet dataset.
  Refuse framework, Jenkins, or conftest changes; do not derive expected SQL from ETL code.
disable-model-invocation: true
---

# Generate Parquet DQ tests

Use this skill as **Step 2** of the PyTest DQ assignment. Read first:

- `PyTest DQ Framework/docs/test-automation-strategy.md` — especially §5 Skill contract and §6 Test design standard.
- `PyTest DQ Framework/docs/dq-framework-design.md` — fixture names, connector behavior, and supported DQ library APIs.
- `docs/parquet-aggregated-data-mapping.md` — the only source for dataset output definitions and expected-result logic.

Read the mapping at generation time. Do not copy dataset SQL or expected results into this reusable skill.

## When this skill applies

Apply this skill only when the user explicitly asks to generate a PyTest DQ module for one Parquet dataset, and the framework components and mapping are available. Generate **exactly one** module per invocation at:

`PyTest DQ Framework/tests/dq checks/parquet_files/test_<dataset_name>.py`

Do not use this skill to implement or alter framework code, Jenkins, `conftest.py`, pytest configuration, dependencies, the mapping, or other project files. Refuse those requests and direct the user to the framework implementation task. Do not generate multiple dataset modules in one invocation.

## Inputs you must have

Before writing the module, obtain or read:

1. The exact dataset name, matching its folder under `/parquet_data/` and its mapping section.
2. That dataset's mapping definition: output columns and source columns/tables, transformations, grouping dimensions/grain, partition information, and any explicitly stated filters.
3. The author name and requirement/ticket ID for the module header.

The mapping is `docs/parquet-aggregated-data-mapping.md` at the repository root. If it is missing, does not define the requested dataset, or lacks information needed to produce a correct query or grain check, stop without creating a module and report exactly what is missing or ambiguous. Ask for an authoritative clarification; do not infer undocumented join keys, transformations, date bucketing, or business rules.

Never use `data_dev/`, pipeline/ETL implementation, parquet-loader SQL, parquet contents/previews, or an existing generated dataset test as a source for the expected query or result. The query must be independently derived from the mapping.

## Hard rules

1. Create one file only, named `test_<dataset_name>.py`, under `PyTest DQ Framework/tests/dq checks/parquet_files/`. Do not edit any other file.
2. Treat PostgreSQL as the expected/source side and Parquet as the actual/target side. Use fixtures `source_data(db_connection)` and `target_data(parquet_reader)` in that direction.
3. Derive expected SQL solely from the requested dataset's mapping. Do not copy SQL or expected results from `data_dev/`, the ETL implementation, parquet-loader SQL, dataset previews, or other tests.
4. Do not introduce `UNION`, extra `WHERE` clauses, `CASE`, sign changes, or other business logic unless explicitly required by the mapping.
5. Make the query return every mapped output column, aliased to the exact mapping/Parquet column name, at the mapped grain. Never create dataset-specific SQL in this skill.
6. Do not guess join keys. If the mapping and authoritative requirements do not establish the needed join path, stop and report the missing join keys.
7. Set `target_path` to `/parquet_data/<dataset_name>` and call `parquet_reader.process(target_path, include_subfolders=True)`.
8. Project the target DataFrame to exactly the mapped output columns before comparison. Partition columns added by the Parquet reader are storage metadata, not mapped outputs; exclude them unless the mapping explicitly defines them as output columns.
9. When a mapped output/grain column is a calendar date, normalize that column to the same date representation in both source and target fixtures before completeness comparison. Use `pd.to_datetime(df[column]).dt.date`; do not change the SQL grouping semantics to work around a representation mismatch.
10. Include all five checks: non-empty smoke, completeness, count, uniqueness, and not-null. Call only the documented `data_quality_library` methods; do not implement DataFrame checks in the test module.
11. Check uniqueness using the complete mapped grain as the `column_names` argument to `check_duplicates`. The TAS §6.2 example calls it without columns, which only requests the library's default whole-row check; the documented API supports an optional column list. Use that API to satisfy the TAS's mapped-grain uniqueness requirement.
12. Pass every mapped output column to `check_not_null_values`, including measure columns marked not-null by the mapping.
13. If the mapping specifies a non-negative constraint, add a test calling the existing `data_quality_library.check_non_negative_values(target_data, column_names=[...])` for the constrained mapped measure. This method permits zero and rejects negative and null values. In particular, use it for `sum_treatment_cost` when that constraint is present in the mapping.
14. Decorate every test with `pytest.mark.parquet_data` and `pytest.mark.<dataset_name>`. Add `pytest.mark.smoke` only to `test_check_dataset_is_not_empty`.
15. Do not change the framework/library code unless the user explicitly requests a separate framework change. Do not rewrite the expected query to make a failing comparison pass.
16. If a mapped constraint cannot be expressed using a documented library method, or its meaning is ambiguous, do not silently omit it or invent behavior. Stop and report the exact unresolved constraint for clarification.

## Workflow

1. Confirm the request is for one dataset module and that the framework already exists. Refuse framework, Jenkins, `conftest.py`, configuration, or multi-dataset work.
2. Read the dataset's mapping section. Record its target columns, source tables/columns, transformations, mapped grain, partition details, and any explicit filters.
3. Determine whether the mapping establishes every required join key and how each output dimension/measure is derived. If not, stop before editing and report the unresolved detail.
4. Build one expected Postgres query from those mapping facts. Select and alias each output to its exact target name; group by the mapped dimensions; implement only the mapped transformations and filters.
5. Create one module using the template below, filling in dataset-specific placeholders from the mapping and supplied header metadata. Set the duplicate-check columns to the full mapped grain, the not-null list to every mapped output column, and the target projection to exactly those mapped output columns.
6. Normalize mapped calendar-date columns to the same Python date representation on both source and target DataFrames before comparison. If the dataset has no mapped calendar-date columns, use an empty date-column list and do not add date conversion.
7. Add a non-negative test using the existing library method for each mapped non-negative constraint. If another constraint is unsupported or ambiguous, stop rather than implementing or omitting it.
8. Review the module against the checklist below. Confirm the test markers, fixture direction, target path, query independence, target projection, date normalization where applicable, grain uniqueness, all not-null columns, all supported mapped constraints, and the one-file limit.
9. Report the created file and any unresolved issues. Do not run pytest unless the user asks. If asked to run it, report actual results and do not modify expected SQL merely to force a pass.

## Template

This follows the complete module structure in TAS §6.2. The uniqueness call supplies the mapped grain using the documented optional `column_names` argument; the TAS example's no-argument call is insufficient to establish grain uniqueness.

```python
"""
Description: Data Quality checks for <dataset_name> dataset.
Requirement(s): <requirement_or_ticket_id>
Author(s): <author_name>
"""

import pandas as pd
import pytest


def _normalize_date_columns(df, column_names):
    for column_name in column_names:
        df[column_name] = pd.to_datetime(df[column_name]).dt.date
    return df


@pytest.fixture(scope='module')
def source_data(db_connection):
    source_query = """
    -- expected query derived from mapping (grain + measures + joins)
    """
    source = db_connection.get_data_sql(source_query)
    # Use the mapped calendar-date columns, or [] when there are none.
    return _normalize_date_columns(source, ['<mapped_date_column>'])


@pytest.fixture(scope='module')
def target_data(parquet_reader):
    target_path = '/parquet_data/<dataset_name>'
    target = parquet_reader.process(target_path, include_subfolders=True)
    # Include mapped outputs only; exclude storage-only partition columns.
    target = target[['<mapped_output_column_1>', '<mapped_output_column_2>', '<mapped_output_column_3>']].copy()
    # Use the same mapped calendar-date columns as source_data, or [] when there are none.
    return _normalize_date_columns(target, ['<mapped_date_column>'])


@pytest.mark.parquet_data
@pytest.mark.smoke
@pytest.mark.<dataset_name>
def test_check_dataset_is_not_empty(target_data, data_quality_library):
    data_quality_library.check_dataset_is_not_empty(target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_data_completeness(source_data, target_data, data_quality_library):
    data_quality_library.check_data_completeness(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_count(source_data, target_data, data_quality_library):
    data_quality_library.check_count(source_data, target_data)


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_uniqueness(target_data, data_quality_library):
    data_quality_library.check_duplicates(
        target_data, column_names=['<mapped_grain_column_1>', '<mapped_grain_column_2>']
    )


@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_not_null_values(target_data, data_quality_library):
    data_quality_library.check_not_null_values(
        target_data,
        ['<mapped_output_column_1>', '<mapped_output_column_2>', '<mapped_output_column_3>'],
    )


# Include this test when the mapping specifies a non-negative constraint.
@pytest.mark.parquet_data
@pytest.mark.<dataset_name>
def test_check_non_negative_values(target_data, data_quality_library):
    data_quality_library.check_non_negative_values(
        target_data, column_names=['<mapped_non_negative_column>']
    )
```

Replace all placeholders with concrete Python values before saving. If there are no mapped calendar-date columns, replace each `['<mapped_date_column>']` with `[]`; otherwise list the mapped date columns in both fixtures. The target projection must list every mapped output column and no storage-only partition columns unless the mapping explicitly includes them. The non-negative test is required only when the mapping states that constraint; use the mapped constrained column(s). The comment inside `source_query` is explanatory only: replace it with the complete mapping-derived SQL; do not leave a placeholder query in a generated module. Use the appropriate number of mapped grain and output columns.

## SQL derivation (generic)

Use the mapping—not pipeline code—to translate the data definition into a Postgres query:

1. Identify the source tables and source columns for each mapped output.
2. Determine the joins required to access those columns. Use only join keys established by the mapping or authoritative project requirements; otherwise stop and request clarification.
3. Treat mapped dimensions as the grouping grain and include them in the `GROUP BY`.
4. Express each mapped measure using its stated aggregate or transformation, including required rounding or concatenation/name formatting.
5. Return all mapped target columns and alias each expression to the exact target column name.
6. Add only filters that the mapping explicitly specifies. Do not add implementation-specific filters or transformations.
7. Respect partition information when it defines the mapped output semantics. A storage partition description alone does not authorize changing the row grain or deriving a new date expression. If the mapping leaves the output date grain or partition-to-value relationship unclear, stop and report it.
8. Check that the query has the same mapped grain that will be passed to the duplicate check. Do not use `DISTINCT` or other logic to hide duplicates.
9. For target comparisons, select only mapped output columns from the loaded Parquet DataFrame. Exclude reader-added partition columns and other storage metadata unless they are explicitly mapped output columns.
10. When a mapped output is a calendar date, normalize it to Python `date` values in both source and target fixtures before comparison. Apply the conversion only to mapped date columns; do not alter the expected SQL grain or coerce unrelated columns.
11. For each mapped non-negative constraint, call the existing `check_non_negative_values` method with the constrained output column(s). It allows zero and rejects negatives and nulls. If a mapped constraint has no documented method or its semantics are unclear, stop and request clarification rather than inventing a check or silently omitting it.
12. Do not use `data_dev/`, ETL implementation, Parquet-loader SQL, or Parquet contents to derive or adjust the expected query.

## After generation

- Do not run pytest unless the user asks.
- Do not edit framework files, Jenkins, `conftest.py`, configuration, requirements, or the mapping while generating the module.
- Do not use `data_dev/` or parquet output to alter the expected SQL.
- If execution was requested, report the command/result accurately. Treat mismatches as findings to investigate against the mapping; do not change expected SQL just to make tests green.
- If the mapping does not support a defensible query or grain check, do not generate a partial or guessed module; report the ambiguity instead.

---

## Skill review (self-check before Step 3)

Reject this skill and correct it before applying it if any item below is true:

- [ ] The skill contains concrete expected SQL or dataset-specific expected results for `facility_name_min_time_spent_per_visit_date`, `facility_type_avg_time_spent_per_visit_date`, or `patient_sum_treatment_cost_per_facility_type`.
- [ ] The skill tells the agent to use `data_dev/`, ETL implementation, parquet-loader SQL, parquet previews, or existing generated tests to derive expected SQL/results.
- [ ] The skill omits completeness, count, uniqueness, or not-null checks.
- [ ] The skill swaps PostgreSQL and Parquet fixtures, or permits trivial/always-pass checks (empty assertions or comparing target data to itself).
- [ ] The skill does not require exactly one module at the prescribed path per invocation.
- [ ] The skill does not require every mapped output column in the not-null check or the complete mapped grain in the uniqueness check.
- [ ] The skill permits guessed join keys, date semantics, filters, transformations, or other unsupported business logic.
- [ ] The skill permits mapping-stated quality constraints to be silently skipped or tested through undocumented methods.
- [ ] The template uses fixture names, connector interfaces, DQ methods, target path, or markers that are not documented by the framework/TAS.
- [ ] The template puts `smoke` on any test other than the non-empty check, or omits `parquet_data` / dataset markers.
- [ ] The skill allows framework, Jenkins, `conftest.py`, mapping, or unrelated-file changes.
- [ ] Any section still contains a `TODO` or an unfilled instructional placeholder outside the reusable module template.

All checklist items must be false before the skill is considered ready. On each invocation, independently verify the mapping and stop to report any ambiguity before creating a module.
