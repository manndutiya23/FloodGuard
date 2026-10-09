# Ward Exposure Data Verification Report

**Project:** FloodGuard — Mumbai hyperlocal flood intelligence  
**Status:** Source transcription verified for all 24 ward rows  
**Verification date:** 2026-10-09  
**Primary source:** Table XXVI, printed page 112 of the original Mumbai Climate Action Plan *Climate & Air Pollution Risks and Vulnerability Assessment* report.

## Method

The table on printed page 112 was visually inspected in the supplied original PDF. Each ward code, exposed-population count, and percentage was compared with the corresponding row in `data/reference/floodguard_mumbai_ward_flood_exposure.csv`. The extracted PDF text was used as a secondary check; the rendered table was treated as authoritative for visual verification.

## Results

- Ward rows compared: **24 / 24**.
- Ward codes matching: **24 / 24**.
- Exposed-population counts matching: **24 / 24**.
- Percentages matching: **24 / 24**.
- Numeric corrections required: **none**.
- Sum of the 24 exposed-population counts: **4,386,255**, matching the source table total shown as `43,86,255`.
- Source table aggregate percentage: **35.3%**. Do not interpret this as the simple average of ward percentages.

## Row-by-row comparison

| Ward | CSV exposed population | Source exposed population | CSV % | Source % | Result |
|---|---:|---:|---:|---:|---|
| A | 33,152 | 33,152 | 17.9 | 17.9 | MATCH |
| B | 53,911 | 53,911 | 43.4 | 43.4 | MATCH |
| C | 36,010 | 36,010 | 21.7 | 21.7 | MATCH |
| D | 105,583 | 105,583 | 30.4 | 30.4 | MATCH |
| E | 147,930 | 147,930 | 37.5 | 37.5 | MATCH |
| F/N | 355,766 | 355,766 | 66.8 | 66.8 | MATCH |
| F/S | 144,576 | 144,576 | 40.3 | 40.3 | MATCH |
| G/N | 304,429 | 304,429 | 50.3 | 50.3 | MATCH |
| G/S | 153,522 | 153,522 | 41.7 | 41.7 | MATCH |
| H/E | 329,774 | 329,774 | 61.6 | 61.6 | MATCH |
| H/W | 200,342 | 200,342 | 61.2 | 61.2 | MATCH |
| K/E | 187,389 | 187,389 | 22.5 | 22.5 | MATCH |
| K/W | 266,733 | 266,733 | 35.9 | 35.9 | MATCH |
| L | 312,960 | 312,960 | 34.5 | 34.5 | MATCH |
| M/E | 275,491 | 275,491 | 34.1 | 34.1 | MATCH |
| M/W | 182,542 | 182,542 | 45.1 | 45.1 | MATCH |
| N | 108,962 | 108,962 | 17.4 | 17.4 | MATCH |
| P/N | 143,697 | 143,697 | 15.4 | 15.4 | MATCH |
| P/S | 143,846 | 143,846 | 31.0 | 31.0 | MATCH |
| R/C | 145,800 | 145,800 | 25.6 | 25.6 | MATCH |
| R/N | 175,520 | 175,520 | 41.1 | 41.1 | MATCH |
| R/S | 209,665 | 209,665 | 30.0 | 30.0 | MATCH |
| S | 190,113 | 190,113 | 26.4 | 26.4 | MATCH |
| T | 178,542 | 178,542 | 49.5 | 49.5 | MATCH |

## Provenance

- **Report:** Mumbai Climate Action Plan, *Climate & Air Pollution Risks and Vulnerability Assessment* (March 2022).
- **Table:** XXVI — Persons potentially at risk due to floods.
- **Source note printed in report:** WRI India Analysis using data from BMC; Census 2011.
- **Original PDF:** https://portal.mcgm.gov.in/irj/go/km/docs/documents/Environment/Climate/VULNERABILITY%20ASSESSMENT%20REPORT%20-%20MCAP.pdf

## Interpretation and limits

This verification establishes that the repository CSV matches the published table. It does not independently validate the study methodology, spatial inputs, or present-day accuracy. Counts are associated with Census 2011 and a 250 m buffer around flood-risk locations; they must be treated as historical vulnerability/exposure context, not current population, live flood conditions, or a calibrated flood probability.

The population total is an aggregate reconciliation check only and is intentionally not stored as a ward row in the source CSV.

## Audit file

The machine-readable row comparisons are in `data/reference/floodguard_mumbai_ward_exposure_verification_log.csv`.
