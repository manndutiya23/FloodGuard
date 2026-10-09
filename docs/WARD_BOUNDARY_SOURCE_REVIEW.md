FloodGuard Ward-Boundary Source Review
Status: Structural validation passed; source/licence, boundary-vintage, and visual review remain pending
Review prepared: 2026-10-10
Candidate: Mumbai (BMC) Wards — 24 administrative wards, catalogue listing from Bharatlas / OpenCity / Oorvani Foundation
Catalogue: https://bharatlas.com/view/wards_mumbai
Direct GeoJSON download URL used: https://pub-0429b8e3b5a946e69ea007df844a6f1c.r2.dev/admin/wards-mumbai/wards_mumbai.geojson
Licence listed by catalogue: ODbL-1.0
Expected project join key: ward_code from data/reference/floodguard_mumbai_ward_flood_exposure.csv
Expected repository path: data/reference/mumbai_ward_boundaries.geojson
Decision so far: The downloaded candidate passes FloodGuard's structural validator and its validator unit tests. It is not yet accepted as the project boundary source: attribution/licence review, source metadata and boundary vintage, and visual checks remain outstanding.

1. Preliminary inspection and validation result
The downloaded file was inspected locally. Results:
- GeoJSON root type: FeatureCollection.
- Feature count: 24.
- Geometry types present: Polygon and MultiPolygon.
- The first feature contains Name, NAME2, OBJECTID, Shape__Area, and Shape__Length properties.
- The first observed Name and NAME2 values both represent G/S, with leading/trailing whitespace and line breaks. The validator normalizes whitespace before comparing ward codes.
Validator result
Command run from backend:
.\.venv\Scripts\python.exe validate_ward_boundaries.py
Output:
PASS: GeoJSON contains one structurally valid polygon feature for every reference ward code.
Reminder: confirm source attribution/licence and visually inspect the boundaries before integration.
The validator reports one structurally valid polygon feature for every ward code in the reference CSV. It checks FeatureCollection structure, feature count, ward-code matching and duplicates/missing/extra values, Polygon/MultiPolygon coordinate structure, coordinate ranges, and closed linear rings. This is structural validation; it does not prove topological correctness, absence of gaps or overlaps, administrative authority, current boundary vintage, or geographic accuracy.
Test results
Validator unit tests were run from backend:
.\.venv\Scripts\python.exe -m pytest tests\test_ward_boundaries.py -q
Result: 9 passed in 0.03s.
The full backend test suite was also run from backend:
.\.venv\Scripts\python.exe -m pytest -q
Result: 77 passed, 1 warning in 0.38s. The warning is a StarletteDeprecationWarning about httpx use in starlette.testclient; it did not cause the suite to fail.
2. Source and licence review
The Bharatlas catalogue labels the layer “Mumbai Ward Map: 24 wards (BMC),” describes it as 24 BMC administrative wards, lists OpenCity as the source, and identifies the licence as ODbL-1.0. See the Bharatlas catalogue entry. The catalogue also identifies OpenCity / Oorvani Foundation as the source in its wider description.
This catalogue metadata is the basis of the current source description; it does not yet independently establish the original boundary publisher's methodology or the boundary vintage of the downloaded file.
Before committing the boundary file or using a transformed/joined database publicly:
1. Preserve the catalogue page URL and the direct download URL above. Record the actual local download/retrieval date if known; it was not separately captured in the validation command output.
2. Inspect the downloaded file metadata and any original OpenCity dataset page/readme for the original publisher, source date, and boundary vintage.
3. Review ODbL-1.0 obligations, including attribution and share-alike conditions that may apply to a publicly used adapted database. Do not assume that code and dataset obligations are identical.
4. Add visible map attribution in the UI if the data is integrated.
5. Keep the original boundary file unchanged. If a transformed/joined derivative is produced, save it under a separate name and document the transformation and applicable licence.
Licence references:
- Catalogue: https://bharatlas.com/view/wards_mumbai
- ODbL overview: https://opendatacommons.org/licenses/odbl/summary/
- ODbL legal text: https://opendatacommons.org/licenses/odbl/1-0/
3. Files and validation procedure
Expected boundary file path after review:
- data/reference/mumbai_ward_boundaries.geojson
Reference ward codes:
- data/reference/floodguard_mumbai_ward_flood_exposure.csv
Run the validator from the repository root:
python backend\validate_ward_boundaries.py
Run its unit tests from backend:
.\.venv\Scripts\python.exe -m pytest tests\test_ward_boundaries.py -q
The validation output confirms the structure/code match described above. It does not replace visual inspection or provenance and licence review.
4. Acceptance checklist
- [x] Record catalogue page URL and direct GeoJSON download URL.
- [ ] Record/confirm the actual download date from file history or retrieval notes.
- [ ] Verify original publisher and dataset-specific source metadata, including boundary vintage.
- [ ] Review licence terms for use, redistribution, derivative database, and attribution.
- [x] Run backend/validate_ward_boundaries.py on the actual downloaded file; result passed as recorded in Section 1.
- [x] Confirm all 24 reference CSV ward codes match exactly one feature according to the validator; no missing, duplicate, or extra codes were reported.
- [x] Confirm supported Polygon/MultiPolygon structure, coordinate ranges, and closed rings pass the validator's structural checks.
- [ ] Open the file in QGIS or another GIS viewer and inspect coverage, obvious gaps/overlaps, placement, and boundary vintage.
- [ ] Compare a few recognizable locations/ward boundaries with an authoritative reference; record the reference and caveats.
- [ ] Ask Laksh to confirm that it fits the frontend mapping layer and agree the property name used for ward joins.
- [ ] Confirm visible attribution and document any transformed/joined database licence obligations before integration.
5. Limitations and recommendation
Recommendation: continue with this candidate, but do not mark it fully accepted or integrate it into a public-facing ward choropleth until the remaining source, licence, vintage, and visual checks have been completed.
The following are now confirmed from local checks: the file is a 24-feature FeatureCollection; its geometries are Polygon/MultiPolygon; the project validator found exactly one structurally valid polygon feature per reference ward code; the validator tests passed (9/9); and the full backend test suite passed (77 passed, 1 warning).
Still unverified: original boundary vintage and authoritative accuracy, visual topology/placement, all licence/attribution implications, and Laksh's mapping integration review.
Do not infer current population, current flood conditions, or flood probability from these boundaries. Administrative ward boundaries are a geographic join/display layer only. FloodGuard's current weather point is still a single representative Mumbai location, not ward-specific weather.
After all acceptance checks pass, update docs/DATA_SOURCES.md to reflect the source's accepted status and review result. Keep the original GeoJSON unchanged and include it in the repository only after the team is satisfied with the licence and attribution obligations.