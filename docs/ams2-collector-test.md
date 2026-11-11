# AMS2 multiplayer result capture — validation checklist

Use a player-hosted lobby with at least two human drivers and (optionally) AI. Run a short qualifying session followed by a three-lap race. Each tester runs the same candidate telemetry adapter on their own Windows PC.

Record whether the adapter supplies: stable player identifier; player name; all multiplayer participants; session type; session start/end; track; qualifying classification; final race order after penalties; DNF/DSQ; fastest lap; lap counts; AI flag; and pit-stop status.

Compare each participant's collected data with the final in-game result screen. Repeat with the hosting driver switched, one disconnect, and a penalty. Verify that the non-host collector can see the same official classification.

**Pass:** at least one collector consistently sees complete, final, penalty-adjusted classifications for all drivers, with enough identifiers to match a scheduled BFR round.

**Fail:** only intermediate positions are visible, classification disappears before capture, or the telemetry omits key opponents/penalties. In that case evaluate an AMS2-compatible race-results export/plugin or a dedicated server for official results; do not silently infer standings from last observed positions.

No collector should be advertised as fully automatic until this validation passes.
