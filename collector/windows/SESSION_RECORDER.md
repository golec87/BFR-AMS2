# BFR Recorder V2 — Windows 11 test guide

V2 reads CREST2 locally and writes provisional session reports. **It does not upload results, update the website, or award championship points.**

## Before starting

1. Update your local `C:\BFR` folder from the GitHub `feature/live-race-control` branch (replace existing files).
2. Start CREST2.exe. AMS2 must have Shared Memory set to Project CARS 2.
3. Open PowerShell in `C:\BFR`.

Run the tests first:

```powershell
py -3 -m unittest discover -s collector/windows/tests -v
```

Start recording:

```powershell
py -3 collector/windows/session_recorder.py
```

Keep PowerShell and CREST2 running through practice, qualifying, and race, including results screens. Stop with Ctrl+C.

## Output

V2 writes to `C:\BFR\collector-output-v2\YYYYMMDD-HHMMSS\`:

- `events.jsonl`: chronological session, pit, and driver-state events
- `001-practice\report.json`, `002-qualifying\report.json`, `003-race\report.json`, etc.
- `start.json`, `last.json`, `grid.json`, `finish-observed.json`, `checkpoint.json` as applicable
- `lap_times.csv`: completed-lap timing for all drivers detected by CREST2
- `lap_position_chart.html`: open locally in a browser to select a driver and overlay lap times with race position changes

One checkpoint is overwritten every 60 seconds; V2 does not write full snapshots every second. This greatly reduces storage, but short-lived events between polls can still be missed. Qualifying and race classifications are **provisional** until checked against AMS2's official results screen.

## Driver mapping

- domo87 → Dom
- mciurej → Michal
- camartin → Craig
- gluc → Marcin
- Kyle → not configured (tag unknown)

Unknown human names are included in the provisional classification but not marked as BFR drivers. The recorder does not reliably distinguish unknown human drivers from AI yet.

## Known limitations and safety

- The first real capture (`bfr 1.zip`) showed practice → qualifying → race, an interrupted race, a second race, and disqualification status 4. Regression tests model these patterns; further on-machine validation is required.
- AMS2 `mRaceState=4` can indicate disqualification; a single driver's state does **not** prove the entire field has finished.
- Pit mode/schedule transitions and disqualification are recorded, but CREST2 does not provide the exact penalty reason.
- A disconnect ends the current segment as interrupted; reconnecting starts a new segment.
- Lap times are recorded only when CREST2 reports a completed-lap increment and a valid `mLastLapTimes`. If a polling gap skips laps, those lap times are unavailable; they are not fabricated.
- No live scoring, GitHub upload, or background startup task.
