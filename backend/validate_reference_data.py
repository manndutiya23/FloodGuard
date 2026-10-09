
"""Validate FloodGuard's historical ward-exposure reference CSV."""

import csv
import math
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CSV_PATH = (
    REPOSITORY_ROOT
    / "data"
    / "reference"
    / "floodguard_mumbai_ward_flood_exposure.csv"
)

REQUIRED_COLUMNS = (
    "ward_code",
    "population_potentially_exposed_within_250m_buffer",
    "percentage_of_ward_population_potentially_exposed_percent",
    "source",
    "source_table",
    "source_page",
    "underlying_population_data_year",
    "data_type",
)


def validate_rows(fieldnames, rows):
    """Return a list of validation errors for CSV headers and records."""
    errors = []
    rows = list(rows)

    if not fieldnames:
        return ["CSV is missing its header row."]

    if len(fieldnames) != len(set(fieldnames)):
        errors.append("CSV contains duplicate column names.")

    missing = [name for name in REQUIRED_COLUMNS if name not in fieldnames]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return errors

    if not rows:
        return ["CSV contains no data rows."]

    seen_codes = set()

    for line_number, row in enumerate(rows, start=2):
        if None in row:
            errors.append(
                f"Row {line_number}: more values than the header defines."
            )

        ward_code = (row.get("ward_code") or "").strip()

        if not ward_code:
            errors.append(f"Row {line_number}: ward_code is blank.")
        else:
            normalized_code = ward_code.casefold()
            if normalized_code in seen_codes:
                errors.append(
                    f"Row {line_number}: duplicate ward_code {ward_code!r}."
                )
            seen_codes.add(normalized_code)

        # Population, source page, and population-data year must be integers.
        integer_fields = (
            "population_potentially_exposed_within_250m_buffer",
            "source_page",
            "underlying_population_data_year",
        )

        for field in integer_fields:
            raw_value = (row.get(field) or "").strip()
            try:
                value = int(raw_value)
            except (TypeError, ValueError):
                errors.append(
                    f"Row {line_number}: {field} must be an integer."
                )
                continue

            if field == "population_potentially_exposed_within_250m_buffer":
                if value < 0:
                    errors.append(
                        f"Row {line_number}: {field} cannot be negative."
                    )
            elif value <= 0:
                errors.append(
                    f"Row {line_number}: {field} must be greater than zero."
                )

        raw_percentage = (
            row.get(
                "percentage_of_ward_population_potentially_exposed_percent"
            )
            or ""
        ).strip()

        try:
            percentage = float(raw_percentage)
            if not math.isfinite(percentage):
                raise ValueError
        except (TypeError, ValueError):
            errors.append(
                f"Row {line_number}: exposure percentage must be a finite number."
            )
        else:
            if not 0 <= percentage <= 100:
                errors.append(
                    f"Row {line_number}: exposure percentage must be between 0 and 100."
                )

        for field in ("source", "source_table", "data_type"):
            if not (row.get(field) or "").strip():
                errors.append(
                    f"Row {line_number}: {field} cannot be blank."
                )

    return errors


def validate_csv(path=DEFAULT_CSV_PATH):
    """Load and validate a reference CSV from disk."""
    with Path(path).open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)
        return validate_rows(reader.fieldnames, reader)


def main():
    try:
        errors = validate_csv()
    except OSError as exc:
        print(f"Could not read reference CSV: {exc}")
        return 1

    if errors:
        print("Reference CSV validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: reference CSV passed all validation checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
