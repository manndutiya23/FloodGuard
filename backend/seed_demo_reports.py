"""Seed or remove SIMULATED demo reports in the FloodGuard reports table.

Run from the repository root:
    python backend/seed_demo_reports.py              # dry run: prints what would be written
    python backend/seed_demo_reports.py --apply      # writes demo reports to DynamoDB
    python backend/seed_demo_reports.py --remove --apply   # deletes only demo-* reports

Requires REPORTS_TABLE_NAME (and AWS credentials/region) only with --apply.

Every seeded item has is_simulated=True and a report_id starting with "demo-".
The --remove option deletes only those IDs, so real citizen reports are never
touched. Re-running --apply refreshes the demo items with new relative timestamps.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_PATH = REPOSITORY_ROOT / "data" / "sample" / "demo_reports.json"
DEMO_ID_PREFIX = "demo-"
CATEGORIES = {"waterlogging", "flooded_passage"}
STATUSES = {"new", "reviewed", "resolved"}
VERIFICATION_STATUSES = {"unverified", "verified"}
DESCRIPTION_MAX_LENGTH = 280
# Rough Mumbai bounding box; catches swapped or mistyped coordinates.
MUMBAI_LAT_RANGE = (18.85, 19.35)
MUMBAI_LNG_RANGE = (72.75, 73.05)


def load_fixture(path: str | Path = DEFAULT_FIXTURE_PATH) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as file:
        payload = json.load(file)
    reports = payload.get("reports")
    if not isinstance(reports, list):
        raise ValueError("Fixture must contain a 'reports' list.")
    return reports


def validate_fixture(reports: list[dict[str, Any]]) -> list[str]:
    """Return a list of problems; an empty list means the fixture is safe to seed."""
    errors: list[str] = []
    seen: set[str] = set()
    for index, report in enumerate(reports):
        context = f"reports[{index}]"
        report_id = report.get("report_id")
        if not isinstance(report_id, str) or not report_id.startswith(DEMO_ID_PREFIX):
            errors.append(f"{context}: report_id must start with '{DEMO_ID_PREFIX}'.")
        elif report_id in seen:
            errors.append(f"{context}: duplicate report_id {report_id!r}.")
        else:
            seen.add(report_id)
        minutes_ago = report.get("minutes_ago")
        if not isinstance(minutes_ago, int) or minutes_ago < 0:
            errors.append(f"{context}: minutes_ago must be a non-negative integer.")
        lat, lng = report.get("latitude"), report.get("longitude")
        if not isinstance(lat, (int, float)) or not MUMBAI_LAT_RANGE[0] <= lat <= MUMBAI_LAT_RANGE[1]:
            errors.append(f"{context}: latitude {lat!r} is outside Mumbai.")
        if not isinstance(lng, (int, float)) or not MUMBAI_LNG_RANGE[0] <= lng <= MUMBAI_LNG_RANGE[1]:
            errors.append(f"{context}: longitude {lng!r} is outside Mumbai.")
        if report.get("category") not in CATEGORIES:
            errors.append(f"{context}: invalid category {report.get('category')!r}.")
        if report.get("status") not in STATUSES:
            errors.append(f"{context}: invalid status {report.get('status')!r}.")
        if report.get("verification_status") not in VERIFICATION_STATUSES:
            errors.append(f"{context}: invalid verification_status {report.get('verification_status')!r}.")
        description = report.get("description")
        if description is not None and (not isinstance(description, str) or len(description) > DESCRIPTION_MAX_LENGTH):
            errors.append(f"{context}: description must be a string of at most {DESCRIPTION_MAX_LENGTH} characters.")
        ward_code = report.get("ward_code")
        if ward_code is not None and not isinstance(ward_code, str):
            errors.append(f"{context}: ward_code must be a string or null.")
    return errors


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_items(reports: list[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
    """Convert fixture entries into DynamoDB items matching the API's report shape."""
    now = now or datetime.now(timezone.utc)
    items = []
    for report in reports:
        items.append({
            "report_id": report["report_id"],
            "ward_code": report.get("ward_code"),
            "latitude": Decimal(str(report["latitude"])),
            "longitude": Decimal(str(report["longitude"])),
            "category": report["category"],
            "description": report.get("description"),
            "status": report["status"],
            "verification_status": report["verification_status"],
            "reported_at": _iso_utc(now - timedelta(minutes=report["minutes_ago"])),
            "is_simulated": True,
        })
    return items


def _reports_table():
    table_name = os.getenv("REPORTS_TABLE_NAME")
    if not table_name:
        raise SystemExit("REPORTS_TABLE_NAME is not set; refusing to guess the target table.")
    import boto3

    return boto3.resource("dynamodb").Table(table_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE_PATH), help="Path to demo report fixture JSON")
    parser.add_argument("--apply", action="store_true", help="Actually write to DynamoDB (default is a dry run)")
    parser.add_argument("--remove", action="store_true", help="Delete the fixture's demo-* reports instead of seeding")
    args = parser.parse_args()

    reports = load_fixture(args.fixture)
    errors = validate_fixture(reports)
    if errors:
        print("FAIL: demo fixture is invalid:")
        for error in errors:
            print(f"- {error}")
        return 1

    items = build_items(reports)
    action = "delete" if args.remove else "write"
    if not args.apply:
        print(f"DRY RUN: would {action} {len(items)} simulated demo reports:")
        for item in items:
            print(f"- {item['report_id']}  {item['ward_code'] or 'unmatched':<9} {item['status']:<9} {item['reported_at']}")
        print("Re-run with --apply to make the change.")
        return 0

    table = _reports_table()
    with table.batch_writer() as batch:
        for item in items:
            if args.remove:
                batch.delete_item(Key={"report_id": item["report_id"]})
            else:
                batch.put_item(Item=item)
    print(f"Done: {action} {len(items)} simulated demo reports in table {table.name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
