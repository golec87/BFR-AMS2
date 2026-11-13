"""BFR CREST2 session recorder. Standard library only; local files, no uploads.

Run on Windows while CREST2.exe is running:
    py -3 collector/windows/session_recorder.py
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = "http://127.0.0.1:8180/crest2/v1/api"
# CREST2 / Project CARS 2 shared-memory session values, verified against samples.
SESSION_NAMES = {0: "invalid", 1: "practice", 2: "test", 3: "qualifying", 4: "formation", 5: "race", 6: "time_attack"}
RACE_FINISHED = 3


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_snapshot(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("gameStates"), dict):
        raise ValueError("CREST2 response has no gameStates object")
    return payload


def session_label(snapshot):
    state = snapshot["gameStates"].get("mSessionState")
    return SESSION_NAMES.get(state, f"unknown_{state}")


def classification(snapshot):
    participants = snapshot.get("participants", {}).get("mParticipantInfo", [])
    if not isinstance(participants, list):
        return []
    result = []
    for participant in participants:
        if not isinstance(participant, dict):
            continue
        if participant.get("mCarClassNames") == "SafetyCar" or participant.get("mName") == "Safety Car":
            continue
        result.append({
            "driver": participant.get("mName"),
            "position": participant.get("mRacePosition"),
            "laps_completed": participant.get("mLapsCompleted"),
            "fastest_lap_seconds": participant.get("mFastestLapTimes"),
            "race_state": participant.get("mRaceStates"),
            "car": participant.get("mCarNames"),
            "class": participant.get("mCarClassNames"),
        })
    return sorted(result, key=lambda x: (x["position"] if isinstance(x["position"], int) and x["position"] > 0 else 9999))


def save_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def record(url, output, interval):
    run_dir = output / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"BFR recorder started: {run_dir} (Ctrl+C to stop)", flush=True)
    print("Local capture only. Nothing is uploaded or added to standings.", flush=True)
    previous_session = None
    last_snapshot = None
    sample_number = 0
    last_finish_signature = None
    disconnected = False
    while True:
        try:
            snapshot = fetch_snapshot(url)
            if disconnected:
                print(f"[{now()}] CREST2 connected", flush=True)
                disconnected = False
            session = session_label(snapshot)
            if session != previous_session:
                if last_snapshot is not None:
                    save_json(run_dir / f"{sample_number:05d}-end-{previous_session}.json", last_snapshot)
                    print(f"[{now()}] Saved end of {previous_session}", flush=True)
                print(f"[{now()}] Session: {session}", flush=True)
                previous_session = session
                last_finish_signature = None
            sample_number += 1
            # Keep each poll so that the final qualifying order and the pre-race grid
            # can be reconstructed even if the session changes between polls.
            save_json(run_dir / f"{sample_number:05d}-{session}.json", snapshot)
            last_snapshot = snapshot
            states = snapshot["gameStates"]
            if session == "race" and states.get("mRaceState") == RACE_FINISHED:
                rows = classification(snapshot)
                signature = json.dumps(rows, sort_keys=True)
                if signature != last_finish_signature:
                    save_json(run_dir / "latest-race-finish.json", {
                        "captured_at": now(),
                        "track": snapshot.get("eventInformation", {}).get("mTranslatedTrackVariation"),
                        "provisional": True,
                        "reason": "Some drivers may still be racing; compare with official results.",
                        "classification": rows,
                    })
                    last_finish_signature = signature
                    print(f"[{now()}] Saved provisional race classification ({len(rows)} drivers)", flush=True)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
            if not disconnected:
                print(f"[{now()}] CREST2 unavailable: {exc}. Retrying...", flush=True)
                disconnected = True
            # Prevent carrying an old session across a lost connection.
            last_snapshot = None
            previous_session = None
            last_finish_signature = None
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Capture CREST2 practice, qualifying and race telemetry")
    parser.add_argument("--url", default=DEFAULT_URL, help="Local CREST2 API URL")
    parser.add_argument("--output", type=Path, default=Path("collector-output"), help="Local output folder")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds")
    args = parser.parse_args()
    if args.interval < 0.2:
        parser.error("--interval must be at least 0.2 seconds")
    try:
        record(args.url, args.output, args.interval)
    except KeyboardInterrupt:
        print("\nBFR recorder stopped.", flush=True)


if __name__ == "__main__":
    main()
