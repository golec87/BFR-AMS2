"""Regenerate the public website snapshot from the league workbook.

Usage: python scripts/import_excel.py "/path/to/BFR Fall 2026 League.xlsx"
Requires: pip install artifact-tool
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from artifact_tool import Blob, SpreadsheetFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "BFR Fall 2026 League.xlsx"
if not SOURCE.exists():
    raise SystemExit(f"Workbook not found: {SOURCE}")
book = SpreadsheetFile.import_xlsx(Blob.load(str(SOURCE)))
def rows(name, area):
    return book.worksheets.get_item(name).get_range(area).values
def excel_date(value):
    if isinstance(value, (int, float)):
        return (datetime(1899, 12, 30) + timedelta(days=value)).date().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)[:10]
drivers = [r[1].strip() for r in rows("Drivers", "A4:B40") if isinstance(r[1], str) and isinstance(r[0], (int, float))]
rounds = []
for r in rows("Schedule", "A5:H100"):
    if not isinstance(r[0], (int, float)):
        continue
    rounds.append(dict(round=int(r[0]), date=excel_date(r[1]), time=str(r[2] or ""), event=str(r[3] or ""), track=str(r[4] or ""), **{"class":str(r[5] or "")}, format=str(r[6] or ""), notes=str(r[7] or "")))
keys = ["beatAverage", "beatHigher", "ahead3AI", "ahead5AI", "fastestLap", "mostGained", "cleanRace", "beatLeader"]
results = []
for r in rows("Season Results", "A4:T1003"):
    driver, rnd = r[:2]
    if driver not in drivers or not isinstance(rnd, (int, float)):
        continue
    q, race1, race2 = r[2], r[4], r[6]
    # Rows without a qualifying or race finish are blank templates, not scored results.
    if all(x is None or x == "" for x in (q, race1, race2)):
        continue
    bonuses = {key: True for key, val in zip(keys, r[8:16]) if val == 1 or val is True}
    results.append(dict(driver=driver, round=int(rnd), qualifying=int(q) if isinstance(q,(int,float)) else None, race1=int(race1) if isinstance(race1,(int,float)) else None, race2=int(race2) if isinstance(race2,(int,float)) else None, bonuses=bonuses))
snapshot = dict(name="Black Flag Racing", season="Fall 2026", timezone="America/Chicago", drivers=drivers, rounds=rounds, results=results)
output = ROOT / "data" / "championship.json"
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {output}: {len(drivers)} drivers, {len(rounds)} rounds, {len(results)} classified driver-round entries")
