
from validate_reference_data import (
    DEFAULT_CSV_PATH,
    REQUIRED_COLUMNS,
    validate_csv,
    validate_rows,
)


def make_valid_row(ward_code="A"):
    return {
        "ward_code": ward_code,
        "population_potentially_exposed_within_250m_buffer": "1000",
        "percentage_of_ward_population_potentially_exposed_percent": "25.5",
        "source": "Example source",
        "source_table": "Example table",
        "source_page": "112",
        "underlying_population_data_year": "2011",
        "data_type": "historical vulnerability baseline",
    }


def test_repository_reference_csv_passes_validation():
    assert validate_csv(DEFAULT_CSV_PATH) == []


def test_duplicate_ward_codes_are_rejected():
    rows = [make_valid_row("A"), make_valid_row("A")]

    errors = validate_rows(REQUIRED_COLUMNS, rows)

    assert any("duplicate ward_code" in error for error in errors)


def test_percentage_above_100_is_rejected():
    row = make_valid_row()
    row[
        "percentage_of_ward_population_potentially_exposed_percent"
    ] = "101.5"

    errors = validate_rows(REQUIRED_COLUMNS, [row])

    assert any("between 0 and 100" in error for error in errors)


def test_negative_population_is_rejected():
    row = make_valid_row()
    row["population_potentially_exposed_within_250m_buffer"] = "-5"

    errors = validate_rows(REQUIRED_COLUMNS, [row])

    assert any("cannot be negative" in error for error in errors)


def test_missing_required_column_is_rejected():
    columns = [
        column
        for column in REQUIRED_COLUMNS
        if column != "source"
    ]

    errors = validate_rows(columns, [make_valid_row()])

    assert any("Missing required columns" in error for error in errors)
