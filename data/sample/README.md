# Demo sample data

`demo_reports.json` holds **12 simulated citizen reports** for demos. They are not real observations or flood records.

- Every report is stored with `is_simulated: true` and a `report_id` starting with `demo-`, so the UI shows a "Simulated" badge and the reports can be removed without touching real data.
- `reported_at` is computed when seeding as now minus `minutes_ago`, so the demo always shows recent activity.
- Ward codes were matched by point-in-polygon against `data/reference/mumbai_ward_boundaries.geojson`; `backend/tests/test_demo_reports.py` re-checks this. `demo-010` is deliberately unmatched (`ward_code: null`) to show that state.
- The mix covers: new, reviewed and resolved reports; verified and unverified; both categories; and a likely-duplicate pair (`demo-001`/`demo-002`, within 200 m and 30 minutes).

## Using it

**Mock mode (no AWS):** the frontend's mock data uses this file automatically (`VITE_USE_MOCKS=true`).

**Live DynamoDB table:** run from the repository root with AWS credentials for the account and `REPORTS_TABLE_NAME` set:

```powershell
python backend/seed_demo_reports.py                   # dry run: lists what would be written
python backend/seed_demo_reports.py --apply           # write (or refresh timestamps of) the demo reports
python backend/seed_demo_reports.py --remove --apply  # delete only the demo-* reports
```

Re-run `--apply` shortly before presenting so the reports look recent. Run `--remove --apply` after the demo.

Coordinate with the infrastructure owner (Mann) before writing to the shared table.
