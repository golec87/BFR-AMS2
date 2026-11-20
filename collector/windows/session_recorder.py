"""BFR Recorder V2: local, event-driven CREST2 capture. No uploads or scoring.

Run: py -3 collector/windows/session_recorder.py
Test: py -3 -m unittest discover -s collector/windows/tests -v
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from lap_chart import lap_updates, write_lap_outputs

SESSION_NAMES = {1: "practice", 2: "test", 3: "qualifying", 4: "formation", 5: "race", 6: "time_attack"}
DRIVERS = {"domo87": "Dom", "mciurej": "Michal", "camartin": "Craig", "gluc": "Marcin"}
# PCARS2 shared memory: 3 finished, 4 disqualified, 5 retired, 6 DNF.
STATUS = {0: "invalid", 1: "not_started", 2: "racing", 3: "finished",
          4: "DSQ", 5: "retired", 6: "DNF"}
PIT = {0: "none", 1: "driving_in", 2: "in_pit", 3: "driving_out", 4: "in_garage"}
FINISH_STATES = {3, 4}


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_crest(url):
    with urllib.request.urlopen(url, timeout=3) as response:
        data = json.load(response)
    if not isinstance(data, dict) or not isinstance(data.get("gameStates"), dict):
        raise ValueError("Invalid CREST2 gameStates")
    return data


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def competitors(snapshot):
    info = snapshot.get("participants", {}).get("mParticipantInfo", [])
    if not isinstance(info, list):
        return []
    rows = []
    for p in info:
        if not isinstance(p, dict):
            continue
        name = str(p.get("mName") or "").strip()
        car_class = str(p.get("mCarClassNames") or "")
        if not name or "safety car" in name.lower() or "safetycar" in car_class.lower():
            continue
        tag = name.lower()
        state = p.get("mRaceStates")
        rows.append({
            "gamer_tag": name, "bfr_driver": DRIVERS.get(tag),
            "is_bfr_driver": tag in DRIVERS,
            "position": p.get("mRacePosition"),
            "laps": p.get("mLapsCompleted"),
            "fastest_lap_seconds": p.get("mFastestLapTimes"),
            "status": STATUS.get(state, f"unknown_{state}"),
            "status_code": state,
            "car": p.get("mCarNames"),
            "pit_mode": p.get("mPitModes"),
            "pit_schedule": p.get("mPitSchedules"),
            "invalidated_laps": p.get("mLapsInvalidated"),
        })
    return sorted(rows, key=lambda p: p["position"] if isinstance(p["position"], int) and p["position"] > 0 else 99999)


def session_of(snapshot):
    return SESSION_NAMES.get(snapshot["gameStates"].get("mSessionState"))


def signature(snapshot):
    event = snapshot.get("eventInformation", {})
    return (event.get("mTrackLocation"), event.get("mTrackVariation"),
            event.get("mLapsInEvent"), event.get("mSessionDuration"))


class Recorder:
    """Process CREST2 snapshots; unit-testable without network or disk services."""
    def __init__(self, output, checkpoint_seconds=60):
        self.output = Path(output)
        self.checkpoint_seconds = checkpoint_seconds
        self.index = 0
        self.active = None
        self.last = None
        self.last_time = None
        self.last_checkpoint = 0
        self.pit_previous = {}
        self.position_history = {}
        self.lap_previous = {}
        self.lap_records = []
        self.race_started = False
        self.race_seen_finish = False
        self.last_game = None
        self.events = []
        self.reports = []

    def emit(self, kind, **details):
        entry = {"at": stamp(), "event": kind, **details}
        self.events.append(entry)
        with (self.output / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def begin(self, session, snapshot, moment):
        self.index += 1
        folder = self.output / f"{self.index:03d}-{session}"
        folder.mkdir(parents=True, exist_ok=True)
        self.active = {"type": session, "folder": folder, "signature": signature(snapshot),
                       "started_at": stamp(), "best": None, "grid": None, "finish": None}
        self.pit_previous = {}
        self.position_history = {}
        self.lap_previous = {}
        self.lap_records = []
        self.race_started = False
        self.race_seen_finish = False
        self.last_checkpoint = moment
        self.emit("session_start", session=session, folder=folder.name)
        save(folder / "start.json", snapshot)

    def finish(self, reason):
        if not self.active:
            return
        active = self.active
        folder = active["folder"]
        if self.last is not None:
            save(folder / "last.json", self.last)
        rows = competitors(active["best"] or self.last or {})
        report = {
            "schema_version": 2, "session": active["type"],
            "started_at": active["started_at"], "ended_at": stamp(),
            "end_reason": reason, "official": False, "scoring_enabled": False,
            "classification": rows,
            "grid": active["grid"],
            "note": "Provisional CREST2 telemetry; verify against AMS2 official results.",
        }
        if active["type"] == "race":
            report["status"] = ("interrupted" if reason in ("game_closed", "connection_lost", "restart")
                                and not self.race_seen_finish else
                                "provisional_finished" if self.race_seen_finish else "unverified")
            report["finish_observed"] = self.race_seen_finish
            report["positions_gained"] = {}
            if active["grid"]:
                starts = {r["gamer_tag"].lower(): r["position"] for r in active["grid"]}
                for r in rows:
                    pos = r["position"]
                    start = starts.get(r["gamer_tag"].lower())
                    if isinstance(start, int) and isinstance(pos, int):
                        report["positions_gained"][r["gamer_tag"]] = start - pos
        if active["type"] == "race":
            report["position_tracking"] = {}
            for tag, history in self.position_history.items():
                positions = [p["position"] for p in history]
                start = next((r["position"] for r in (active["grid"] or [])
                              if r["gamer_tag"].lower() == tag.lower()), None)
                final = next((r["position"] for r in rows if r["gamer_tag"].lower() == tag.lower()), None)
                report["position_tracking"][tag] = {
                    "start": start, "last_recorded": final,
                    "highest_position": min(positions),
                    "lowest_position": max(positions),
                    "biggest_gain_from_start": max((start - p for p in positions), default=None)
                        if isinstance(start, int) else None,
                    "changes": history,
                }
        if active["type"] == "race":
            report["lap_times"] = self.lap_records
            write_lap_outputs(folder, self.lap_records, report["position_tracking"])
        save(folder / "report.json", report)
        self.reports.append(report)
        self.emit("session_end", session=active["type"], reason=reason, folder=folder.name)
        self.active = None
        self.last = None

    def consume(self, snapshot, moment=None):
        moment = time.monotonic() if moment is None else moment
        game = snapshot["gameStates"]
        game_state = game.get("mGameState")
        session = session_of(snapshot) if game_state != 1 else None
        if session is None:
            if self.active:
                self.finish("game_closed" if game_state == 1 else "session_left")
            self.last_game = game_state
            return

        if self.active and (session != self.active["type"] or signature(snapshot) != self.active["signature"]):
            self.finish("session_changed")
        if not self.active:
            self.begin(session, snapshot, moment)
        elif session == "race":
            # A fresh race after a completed/interrupted one, even on the same track.
            state = game.get("mRaceState")
            if self.race_started and state == 1 and self.last and self.last["gameStates"].get("mRaceState") != 1:
                self.finish("restart")
                self.begin(session, snapshot, moment)

        active = self.active
        folder = active["folder"]
        rows = competitors(snapshot)
        if rows:
            active["best"] = snapshot
        if session == "race":
            race_state = game.get("mRaceState")
            if race_state == 2:
                self.race_started = True
            if race_state in FINISH_STATES:
                self.race_seen_finish = True
            if active["grid"] is None and race_state in (1, 2) and rows:
                active["grid"] = rows
                save(folder / "grid.json", rows)
                self.emit("grid_captured", drivers=len(rows))
            # Capture completed laps for every driver; never invent missing times.
            for lap in lap_updates(snapshot, self.lap_previous):
                self.lap_records.append(lap)
                self.emit("lap_completed", **lap)
            # Track every driver's position changes without full per-second snapshots.
            for row in rows:
                tag = row["gamer_tag"]
                pos = row["position"]
                if not isinstance(pos, int) or pos < 1:
                    continue
                history = self.position_history.setdefault(tag, [])
                if not history or history[-1]["position"] != pos:
                    entry = {"at": stamp(), "position": pos, "lap": row["laps"]}
                    if history:
                        self.emit("position_change", driver=tag,
                                  previous=history[-1]["position"], current=pos,
                                  lap=row["laps"])
                    history.append(entry)
                        # Log local pit telemetry and all BFR drivers' status/pit transitions.
            pit = snapshot.get("pitInfo", {})
            viewed = snapshot.get("participants", {}).get("mViewedParticipantIndex")
            all_participants = snapshot.get("participants", {}).get("mParticipantInfo", [])
            if isinstance(all_participants, list) and isinstance(viewed, int) and 0 <= viewed < len(all_participants):
                local_name = str(all_participants[viewed].get("mName") or "").strip()
            else:
                local_name = None
            watch = {}
            for row in rows:
                if row["is_bfr_driver"] or row["gamer_tag"] == local_name:
                    watch[row["gamer_tag"]] = (row["status_code"], row["pit_mode"], row["pit_schedule"])
            watch["_local_pit"] = (pit.get("mPitMode"), pit.get("mPitSchedule"), pit.get("mEnforcedPitStopLap"))
            for driver, value in watch.items():
                old = self.pit_previous.get(driver)
                if old is not None and old != value:
                    self.emit("driver_state_change", driver=driver, previous=old, current=value)
                self.pit_previous[driver] = value
            if race_state in FINISH_STATES:
                save(folder / "finish-observed.json", snapshot)

        if moment - self.last_checkpoint >= self.checkpoint_seconds:
            save(folder / "checkpoint.json", snapshot)
            self.last_checkpoint = moment
        self.last = snapshot

    def disconnect(self):
        if self.active:
            self.finish("connection_lost")


def main():
    parser = argparse.ArgumentParser(description="BFR V2 CREST2 local session recorder")
    parser.add_argument("--url", default="http://127.0.0.1:8180/crest2/v1/api")
    parser.add_argument("--output", type=Path, default=Path("collector-output-v2"))
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--checkpoint-seconds", type=float, default=60)
    args = parser.parse_args()
    if args.interval < 0.2 or args.checkpoint_seconds < 1:
        parser.error("interval must be >=0.2 and checkpoint-seconds >=1")
    folder = args.output / datetime.now().strftime("%Y%m%d-%H%M%S")
    folder.mkdir(parents=True, exist_ok=True)
    recorder = Recorder(folder, args.checkpoint_seconds)
    print(f"BFR Recorder V2 saving locally to {folder}; no uploads or scoring. Ctrl+C to stop.", flush=True)
    connected = False
    try:
        while True:
            try:
                snapshot = read_crest(args.url)
                if not connected:
                    print("CREST2 connected", flush=True)
                    connected = True
                before = len(recorder.events)
                recorder.consume(snapshot)
                for event in recorder.events[before:]:
                    print(f"[{event['at']}] {event['event']}: {event.get('session', event.get('driver', ''))}", flush=True)
            except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as exc:
                if connected:
                    print(f"CREST2 disconnected ({exc}); waiting to reconnect", flush=True)
                    recorder.disconnect()
                    connected = False
            time.sleep(args.interval)
    except KeyboardInterrupt:
        recorder.finish("recorder_stopped")
        print("\nRecorder stopped. Review report.json in each session folder.", flush=True)


if __name__ == "__main__":
    main()
