"""Regression tests for the BFR CREST2 recorder, including first real-session patterns."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "session_recorder.py"
spec = importlib.util.spec_from_file_location("bfr_session_recorder", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample(session=5, game=2, race=2, position=2, driver_state=2, pit=0):
    return {
        "gameStates": {"mGameState": game, "mSessionState": session, "mRaceState": race},
        "eventInformation": {"mTrackLocation": "Spa", "mTrackVariation": "Spa_2022",
                             "mLapsInEvent": 16, "mSessionDuration": 0},
        "participants": {"mViewedParticipantIndex": 0, "mParticipantInfo": [
            {"mName": "domo87", "mRacePosition": position, "mRaceStates": driver_state,
             "mLapsCompleted": 4, "mFastestLapTimes": 126.2,
             "mCarNames": "Nissan R89C", "mCarClassNames": "Group C",
             "mPitModes": pit, "mPitSchedules": 0},
            {"mName": "mciurej", "mRacePosition": 1, "mRaceStates": 2,
             "mCarClassNames": "Group C"},
            {"mName": "Safety Car  (AI)", "mRacePosition": 25,
             "mCarClassNames": "SafetyCar"},
        ]},
        "pitInfo": {"mPitMode": pit, "mPitSchedule": 0, "mEnforcedPitStopLap": 1},
    }


class RecorderTests(unittest.TestCase):
    def test_driver_mapping_and_safety_car(self):
        rows = module.competitors(sample())
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["bfr_driver"] for r in rows}, {"Dom", "Michal"})
        self.assertFalse(any("Safety" in r["gamer_tag"] for r in rows))

    def test_practice_qualifying_race_and_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = module.Recorder(directory, checkpoint_seconds=60)
            recorder.consume(sample(session=1), moment=1)
            recorder.consume(sample(session=3), moment=2)
            recorder.consume(sample(session=5, race=1), moment=3)
            recorder.consume(sample(session=5, race=2), moment=4)
            recorder.consume(sample(session=5, race=4, driver_state=4, position=24), moment=5)
            recorder.consume(sample(session=0, game=1, race=0), moment=6)
            self.assertEqual([r["session"] for r in recorder.reports],
                             ["practice", "qualifying", "race"])
            race = recorder.reports[-1]
            self.assertEqual(race["status"], "provisional_finished")
            self.assertFalse(race["official"])
            self.assertFalse(race["scoring_enabled"])
            self.assertEqual(race["positions_gained"]["domo87"], -22)
            self.assertEqual(next(r for r in race["classification"] if r["gamer_tag"] == "domo87")["status"], "DSQ")
            self.assertTrue((Path(directory) / "003-race" / "report.json").exists())

    def test_crash_and_restart_same_track(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = module.Recorder(directory)
            recorder.consume(sample(race=1), moment=1)
            recorder.consume(sample(race=2), moment=2)
            recorder.consume(sample(session=0, game=1, race=0), moment=3)
            recorder.consume(sample(race=1), moment=4)
            recorder.consume(sample(race=2), moment=5)
            recorder.consume(sample(race=4, driver_state=4), moment=6)
            recorder.consume(sample(session=0, game=1, race=0), moment=7)
            self.assertEqual(len(recorder.reports), 2)
            self.assertEqual(recorder.reports[0]["status"], "interrupted")
            self.assertEqual(recorder.reports[1]["status"], "provisional_finished")

    def test_pit_diagnostics_and_compact_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = module.Recorder(directory, checkpoint_seconds=60)
            recorder.consume(sample(pit=0), moment=1)
            recorder.consume(sample(pit=1), moment=2)
            recorder.consume(sample(pit=2), moment=3)
            recorder.consume(sample(pit=3), moment=4)
            recorder.consume(sample(driver_state=4), moment=5)
            recorder.finish("recorder_stopped")
            self.assertGreaterEqual(len([e for e in recorder.events if e["event"] == "driver_state_change"]), 4)
            files = list(Path(directory).rglob("*.json"))
            self.assertLessEqual(len(files), 5)


if __name__ == "__main__":
    unittest.main()
