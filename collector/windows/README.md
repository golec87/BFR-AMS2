# BFR Windows 11 collector — first verification

This first-stage script detects the Steam Automobilista 2 process. It **does not yet read telemetry, capture results, or upload anything**. That requires confirming a multiplayer-compatible AMS2 data source.

## Requirements
- Windows 11, Steam edition of Automobilista 2
- Python 3 installed from python.org or Microsoft Store
- No extra Python packages

## Test
1. Open PowerShell in the BFR-AMS2 repository folder.
2. Run `py -3 collector/windows/process_watch.py`.
3. Launch AMS2 through Steam. Look for `AMS2 RUNNING`.
4. Close AMS2. Look for `AMS2 CLOSED`.
5. Press Ctrl+C to exit.

If the script does not detect AMS2, open Task Manager > Details and note the executable name. Update `PROCESS_NAMES` in the script.

## Why it does not start automatically yet
We should not register a startup task until detection and the final-results telemetry adapter are tested. Once verified, Windows Task Scheduler can launch the lightweight watcher at sign-in; it will remain idle outside AMS2 and only activate telemetry capture while the game is running.

## Next validation
Test a real player-hosted multiplayer session with two participants. Determine whether the available shared-memory API/adapter exposes all participants' final, penalty-adjusted race classification and qualifying results. See `docs/ams2-collector-test.md`.
