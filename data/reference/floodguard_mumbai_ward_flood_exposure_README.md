# FloodGuard — Mumbai Ward Flood Exposure Baseline

## Verification status

**Status: source figures verified against the supplied original report PDF.** All 24 ward codes, exposed-population counts, and ward percentages in the CSV were manually compared with Table XXVI on printed page 112 of the original report on **2026-10-09**. All 24 rows matched; no numeric corrections were required.

The comparison used a rendered view of the original PDF table as the primary source check, with text extraction as a secondary aid. Population counts in the PDF use Indian digit grouping (for example, `3,55,766`); the CSV stores the same integer without separators (`355766`).

See `data/reference/floodguard_mumbai_ward_exposure_verification_log.csv` for the row-by-row comparison and `docs/WARD_DATA_VERIFICATION.md` for a human-readable verification summary.

## Source

Municipal Corporation of Greater Mumbai, *Climate & Air Pollution Risks and Vulnerability Assessment* (Mumbai Climate Action Plan vulnerability assessment report, March 2022).

Original PDF: https://portal.mcgm.gov.in/irj/go/km/docs/documents/Environment/Climate/VULNERABILITY%20ASSESSMENT%20REPORT%20-%20MCAP.pdf

## Table used

Printed page 112, Table XXVI: “Persons potentially at risk due to floods” with source note “WRI India Analysis using data from BMC; Census 2011.” The table reports exposed population within a 250 m buffer and the percentage of ward population potentially exposed.

## Columns

- `ward_code`: BMC administrative ward code as shown in the report.
- `population_potentially_exposed_within_250m_buffer`: people potentially exposed within the assessment's 250 m flood-risk buffer.
- `percentage_of_ward_population_potentially_exposed_percent`: percentage printed for that ward.
- `source`, `source_table`, `source_page`: provenance fields.
- `underlying_population_data_year`: Census 2011, as described in the source note.
- `data_type`: historical vulnerability baseline; not a live flood prediction.

## Verification results

- Ward rows checked: 24 of 24.
- Ward codes: 24 matches.
- Exposed-population counts: 24 matches.
- Ward exposure percentages: 24 matches.
- Sum of the 24 ward exposed-population counts: 4,386,255, matching the source table's total row (printed as `43,86,255`).
- Corrections to source values: none required.
- The source table's aggregate percentage is 35.3%. This is the source's total-row figure; it should not be calculated as the simple arithmetic mean of the 24 ward percentages.

## Important caveats

1. “Verified” here means the transcription matches the supplied original report table; it does not validate the report's underlying methodology or independently verify the original analysis.
2. The counts use underlying Census 2011 population data. They are not current population counts.
3. A 250 m buffer around flood-risk locations is a historical exposure methodology, not a live flood boundary, proof of current waterlogging, or a calibrated probability that a ward will flood.
4. The total row is intentionally omitted from the ward CSV because it is an aggregate, not an individual ward. The aggregate is retained in this README and verification report for reconciliation only.
5. A successful CSV validator checks structure and value ranges; it cannot establish source accuracy without the comparison described above.

## Recommended repository location

- `data/reference/floodguard_mumbai_ward_flood_exposure.csv`
- `data/reference/floodguard_mumbai_ward_flood_exposure_README.md`
- `data/reference/floodguard_mumbai_ward_exposure_verification_log.csv`
- `docs/WARD_DATA_VERIFICATION.md`
