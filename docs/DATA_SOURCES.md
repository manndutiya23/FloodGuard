# FloodGuard Data Sources and Provenance

**Project:** FloodGuard — Mumbai Hyperlocal Flood Intelligence
**Status:** Checkpoint 0 — Data inventory and verification plan
**Version:** 1.0

## 1. Purpose

This document records the data available to FloodGuard, its provenance, its intended use, and its limitations.

Every dataset used by the application must have a documented source, geographic coverage, relevant time period, and known limitations.

Data sources listed as candidates in this document are not considered integrated or verified until the team has confirmed their availability and suitability.

## 2. Current reference dataset: Mumbai ward-level flood exposure

### Dataset file

`data/reference/floodguard_mumbai_ward_flood_exposure.csv`

Supporting documentation:

`data/reference/floodguard_mumbai_ward_flood_exposure_README.md`

### Source

The dataset was transcribed from the ward-level exposure table in the Mumbai Climate Action Plan's *Climate & Air Pollution Risks and Vulnerability Assessment* report.

The source table is identified as appearing on printed page 112 of the report.

The original report is available among the project's reference materials. The transcribed values should be checked against the source table before being used as verified public-facing figures.

### Available fields

| Field                                                       | Description                                                                |
| ----------------------------------------------------------- | -------------------------------------------------------------------------- |
| `ward_code`                                                 | Ward identifier in the source dataset                                      |
| `population_potentially_exposed_within_250m_buffer`         | Number of people potentially exposed within the assessed flood-risk buffer |
| `percentage_of_ward_population_potentially_exposed_percent` | Percentage of the ward population potentially exposed                      |
| `source`                                                    | Source report                                                              |
| `source_table`                                              | Source table reference                                                     |
| `source_page`                                               | Source page reference                                                      |
| `underlying_population_data_year`                           | Year of the underlying population data                                     |
| `data_type`                                                 | Classification of the dataset                                              |

The implementation must preserve these source field names unless a documented transformation is agreed upon.

### Intended use

The dataset provides a historical ward-level exposure baseline.

FloodGuard can use it to:

- Display the number of people potentially exposed.
- Display the corresponding percentage of the ward population.
- Compare the historical exposure measures between wards.
- Provide context alongside separately calculated current risk assessments.

Both the count and percentage should be displayed where the values are available.

### Important limitations

This dataset does **not** independently tell us:

- How many people are experiencing flooding right now.
- Whether a particular street is currently flooded.
- The probability that a ward will flood during a particular rainfall event.
- The current population of each ward.
- Whether current drainage conditions or flood defences have changed the exposure.
- The exact location of every potentially exposed person.

The 250-metre buffer refers to the assessment's mapped exposure methodology. It must not be interpreted as a live flood boundary or a guarantee that every person counted will be affected.

The underlying population information is historical and associated with Census 2011. These figures must not be presented as current population counts.

### Verification status

The file has been prepared from a source report and has accompanying documentation. Before the values are treated as verified:

1. Compare all ward codes and measurements against the source table.
2. Confirm the meaning and units of both exposure fields.
3. Confirm the source-page reference and underlying population year.
4. Check for missing values, duplicate ward codes, and transcription errors.
5. Record any discrepancies and corrections.

Until this verification is complete, the data should be described as transcribed historical reference data.

## 3. Original source report

### Source

*Climate & Air Pollution Risks and Vulnerability Assessment*, associated with the Mumbai Climate Action Plan.

### Intended use

The original report provides the context and methodology behind the ward-level exposure figures. It should be consulted whenever the team needs to interpret a source field or explain the dataset's limitations.

### Handling requirements

- Preserve the report's title and source attribution.
- Cite the relevant page when describing a specific finding.
- Do not imply that the report provides live flood forecasts unless a specific source passage supports that claim.
- Check redistribution and licensing conditions before committing the complete report to the public GitHub repository.
- Keep the report in the team's permitted reference storage if it cannot be redistributed publicly.

## 4. Environmental data needed for current risk assessment

The historical dataset alone is insufficient to establish current flood risk. FloodGuard must investigate additional data sources.

The following are candidate categories to investigate. They are not confirmed integrations.

### 4.1 Rainfall observations

**Purpose:** Understand rainfall that has already occurred.

Information to investigate:

- Rainfall amount.
- Measurement interval.
- Observation timestamp.
- Geographic coverage.
- Station or grid location.
- Missing measurements and update frequency.

Rainfall observations must be labelled with their actual observation period. Recent rainfall is not equivalent to forecast rainfall.

### 4.2 Rainfall forecasts

**Purpose:** Assess potential future rainfall conditions.

Information to investigate:

- Forecast rainfall amount.
- Forecast issue time.
- Forecast valid period.
- Geographic resolution.
- Update frequency.
- Availability and access restrictions.

Forecast data must be displayed as forecasts, with the relevant valid period. It must not be labelled as observed rainfall.

### 4.3 Historical flood and waterlogging records

**Purpose:** Provide historical context and, where sufficiently detailed, support evaluation of risk logic.

Information to investigate:

- Incident location.
- Incident date and time.
- Source and verification status.
- Incident type.
- Geographic accuracy.
- Coverage and missing records.
- Terms governing reuse.

Historical incident records must not be presented as current incidents.

### 4.4 Geographic and terrain data

**Purpose:** Improve geographic context and investigate whether elevation or terrain contributes useful information.

Information to investigate:

- Geographic coverage.
- Spatial resolution.
- Coordinate reference system.
- Source date.
- Licensing.
- Suitability for the intended analysis.

Elevation alone does not establish flood probability. Any derived geographic indicator must be explained and evaluated.

### 4.5 Administrative ward boundaries

**Purpose:** Display ward-level results accurately on the map.

The team must find a suitable ward-boundary dataset with clear provenance and permitted usage.

Before integration, verify:

- Ward naming and codes.
- Geographic coverage.
- Coordinate reference system.
- Boundary vintage.
- Licensing and attribution requirements.
- Compatibility with the reference CSV.

Ward codes must not be joined to geographic polygons based on assumptions alone. Any unmatched records must be investigated.

## 5. Candidate source discovery

The team may investigate the following organisations and portals for relevant data:

- India Meteorological Department (IMD) for rainfall and weather information.
- Municipal Corporation of Greater Mumbai (BMC) for municipal information and potentially available ward or flood-related records.
- Relevant government open-data portals.
- Suitable geographic-data providers for ward boundaries and terrain information.

These are starting points for research, not confirmation that a specific dataset or API is freely accessible, sufficiently current, or suitable for this project.

For each candidate source, record:

1. Exact dataset or API name.
2. Official URL.
3. Provider and attribution.
4. Access method and any required credentials.
5. Geographic and temporal coverage.
6. Update frequency.
7. Licensing and usage restrictions.
8. Known data-quality limitations.
9. Date checked by the team.
10. Decision: accepted, rejected, or pending verification.

Do not build a critical workflow around a source until access and suitability have been tested.

## 6. Citizen-submitted reports

Citizen reports are application-generated records rather than an authoritative external environmental dataset.

Each report should preserve:

- Report identifier.
- Submitted coordinates, where available.
- Incident category.
- Description.
- Submission timestamp.
- Workflow status.
- Verification status.
- Whether the report is simulated.

### Trust and quality rules

- A submitted report is unverified until appropriate verification occurs.
- Multiple reports may describe the same incident.
- Incorrect coordinates or inaccurate descriptions may occur.
- A report's existence does not prove that an area is flooded.
- Simulated reports must be visibly identified.
- Personal information should not be collected unless it is necessary for the feature.

Citizen reports may contribute to the risk assessment only through documented logic that accounts for their status, recency, location, and limitations.

## 7. Data freshness and missing information

Each environmental source must have a documented update policy appropriate to that source.

The application should distinguish:

- **Available:** The required input is present.
- **Unavailable:** The input could not be retrieved or is absent.
- **Stale:** The input is older than the source-specific freshness threshold.
- **Simulated:** The input was generated for testing or demonstration.

These are proposed logical states. The implementation must define exact field names and freshness thresholds in the API contract or relevant technical documentation.

A source-specific freshness threshold must not be invented without considering the source's normal update frequency and intended use.

Missing or stale rainfall data must not be silently treated as zero rainfall. Missing data must not automatically produce a low-risk result.

Historical exposure may remain visible even when current environmental signals are unavailable, provided it is labelled correctly.

## 8. Data preparation and validation

Before any dataset enters the risk engine:

1. Preserve the original source file where permitted.
2. Record provenance and retrieval or preparation date.
3. Validate required columns and data types.
4. Check for missing and duplicate records.
5. Validate units and plausible value ranges.
6. Check ward-code consistency with geographic boundaries.
7. Record any transformations.
8. Create reproducible tests for important transformations.
9. Keep sample or simulated data separate from verified source data.

Do not silently replace missing values, modify source measurements, or remove records without documenting the reason.

## 9. Data storage and repository policy

### Git repository

Suitable small, redistributable reference datasets and their documentation may be stored in `data/reference/`.

Synthetic test fixtures belong in `data/sample/`.

Large, restricted, sensitive, or frequently refreshed files should not automatically be committed to Git. Their storage method must be decided based on size, licensing, sensitivity, and reproducibility requirements.

### Amazon S3

S3 may be used for supported reference datasets, ingestion artifacts, or historical snapshots when those files need object storage.

If the same dataset exists in Git and S3, document which copy is authoritative and how versions are identified.

### Application records

Citizen incident reports and their workflow metadata may be stored in the selected application database. They should not be mixed into the historical reference CSV.

### Secrets

Never commit API keys, AWS credentials, access tokens, or populated `.env` files.

## 10. Relationship to the risk engine

The risk engine may combine suitable historical exposure information with current environmental inputs and incident reports.

However:

- Historical exposure is contextual information, not a direct flood-probability label.
- Forecasts and observations must remain distinct.
- Citizen reports must retain their verification and recency information.
- Each input must have documented units and provenance.
- The risk calculation must explain how inputs contribute to its output.
- Missing critical information must be handled explicitly.
- Simulated inputs must produce visibly labelled simulated results.

The initial risk method is intended to be an explainable heuristic. It must not be described as a validated predictive model unless appropriate training or calibration data, evaluation, and supporting evidence exist.

## 11. Source register

Maintain a record for each source using this structure:

| Field               | Description                                          |
| ------------------- | ---------------------------------------------------- |
| Dataset name        | Human-readable name                                  |
| Provider            | Publishing organisation                              |
| Official URL        | Dataset or API page                                  |
| Geographic coverage | Area covered                                         |
| Temporal coverage   | Dates represented                                    |
| Update frequency    | How often data changes                               |
| Access requirements | Public, registration, API key, or other restrictions |
| Licence             | Confirmed usage terms                                |
| Verification status | Pending, accepted, or rejected                       |
| Last checked        | Date the team checked the source                     |
| Limitations         | Known issues and caveats                             |

A candidate source must remain marked as pending until its availability, licence, and suitability have been checked.

## 12. Acceptance criteria

A data source is ready for integration when:

- Its provenance is documented.
- The team can access the required data.
- Its licensing and usage conditions are understood.
- Its geographic and temporal coverage suit the feature.
- Its fields, units, and timestamps are understood.
- Its missing-data behaviour is documented.
- A reproducible test or sample has been prepared.
- The team has recorded its acceptance decision.

Until these criteria are met, the application must not depend on the source as though it were guaranteed to be available.

## 13. Outstanding tasks

- [ ] Verify the transcribed ward exposure values against the original report.
- [ ] Confirm the source CSV's exact provenance fields and metadata.
- [ ] Find and verify a suitable Mumbai ward-boundary dataset.
- [ ] Investigate accessible rainfall observations and forecast sources.
- [ ] Investigate suitable historical flood or waterlogging records.
- [ ] Document the licence and access requirements for every accepted source.
- [ ] Define source-specific freshness thresholds.
- [ ] Prepare clean sample fixtures for independent risk-engine testing.
- [ ] Confirm which data can be safely included in the public repository.

**Final principle:** FloodGuard must communicate what its data actually supports, not what the team wishes the data could prove.
