"""BFR Windows 11 AMS2 process watcher (Python standard library only).

Run: py -3 collector/windows/process_watch.py
This is a *process detector*, not yet a telemetry reader.
"""
import csv
import io
import subprocess
import time
from datetime import datetime, timezone

# Steam AMS2 process names may differ by build. Confirm via Task Manager.
PROCESS_NAMES = {"ams2avx.exe", "ams2.exe"}
POLL_SECONDS = 3


def ams2_running():
    result = subprocess.run(
        ["tasklist", "/FO", "CSV", "/NH"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise RuntimeError("Unable to query Windows processes: " + result.stderr.strip())
    for row in csv.reader(io.StringIO(result.stdout)):
        if row and row[0].strip().lower() in PROCESS_NAMES:
            return True
    return False


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main():
    print("BFR AMS2 watcher started. Press Ctrl+C to stop.", flush=True)
    last = None
    while True:
        try:
            active = ams2_running()
            if active != last:
                print(f"[{timestamp()}] AMS2 {'RUNNING' if active else 'CLOSED'}", flush=True)
                if active:
                    print("Telemetry capture not configured yet; no results are uploaded.", flush=True)
                last = active
        except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
            print(f"[{timestamp()}] Process check failed: {exc}", flush=True)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBFR watcher stopped.")
