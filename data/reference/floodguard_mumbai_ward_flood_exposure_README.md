# FloodGuard — Mumbai Ward Flood Exposure Baseline

## Source
Municipal Corporation of Greater Mumbai, *Climate & Air Pollution Risks and Vulnerability Assessment* (Mumbai Climate Action Plan vulnerability assessment report).

Source PDF:
https://portal.mcgm.gov.in/irj/go/km/docs/documents/Environment/Climate/VULNERABILITY%20ASSESSMENT%20REPORT%20-%20MCAP.pdf

## Table used
Printed page 112, table headed “Persons potentially at risk due to floods (Source: WRI India Analysis using data from BMC; Census 2011)”. The report's ward-wise summary on printed page 66 reports a BMC average of 35.3%.

## Columns
- `ward_code`: BMC administrative ward code as shown in the report.
- `population_potentially_exposed_within_250m_buffer`: number of people potentially exposed within a 250 m buffer of flood risk locations.
- `percentage_of_ward_population_potentially_exposed_percent`: reported percentage for that ward.
- `source`, `source_table`, `source_page`: provenance.
- `underlying_population_data_year`: Census 2011, as stated in the report's source note.
- `data_type`: explicit reminder that this is a historical vulnerability baseline, not a real-time flood forecast.

## Important caveats
1. Values were transcribed from a user-provided screenshot of printed page 112. Verify them against the original PDF before using them for a high-stakes or public-facing claim.
2. Do not describe this table as current population data or street-level flood probability.
3. The total row is omitted from the CSV because it is an aggregate, not an individual ward. The report shows total population potentially exposed as 4,386,255 and total percentage as 35.3%.
4. The ward percentages can support contextual vulnerability display or a clearly labelled heuristic. They do not alone establish whether a road will flood at a particular time.

## Recommended repository location
`data/reference/floodguard_mumbai_ward_flood_exposure.csv`
