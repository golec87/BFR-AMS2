# BFR Automatic Session Recorder — Windows test

This is an **experimental local-only** CREST2 telemetry recorder. It does not upload to GitHub, score league points, or modify the live website.

## Requirements
- Windows 11 with AMS2 configured for Shared Memory / Project CARS 2
- CREST2.exe running and serving http://localhost:8180/crest2/v1/api
- Python 3 (no third-party packages)

## Run
1. Download the updated `feature/live-race-control` branch as a ZIP, extract it, and open PowerShell in its root folder.
2. Start CREST2.exe.
3. Run:

```powershell
py -3 collector/windows/session_recorder.py
```

4. Run an AMS2 practice → qualifying → race weekend. Keep the recorder open throughout, including the results screens.
5. Press Ctrl+C when finished.

Output appears under `collector-output/YYYYMMDD-HHMMSS/`. The recorder saves **one full JSON file per second**, plus `*-end-*.json` snapshots on session changes and `latest-race-finish.json` when a race-finished state is detected. It can create many files; delete old test folders after reviewing.

## What to send back
Zip the newest folder inside `collector-output` and upload it. Compare qualifying and race classifications with AMS2 results screenshots, especially before treating any classification as official.

## Limitations
- This is an untested first implementation. Session state values and transitions need confirmation with real practice and qualifying captures.
- CREST2's race-finished flag can appear while other competitors are still on track. Finishing classification is provisional.
- No persistent upload, multiplayer validation, automatic scoring, or Windows startup integration yet.
- Keep CREST2 running; if disconnected, the recorder retries.
