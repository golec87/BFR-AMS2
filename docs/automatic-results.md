# BFR automatic post-race results — player-hosted AMS2

## Goal
Automatically publish **completed** qualifying/race classifications and recalculate championship standings, without manual uploads or race-result entry. No live timing required.

## Important feasibility gate
AMS2 player-hosted lobbies do not provide the dedicated-server HTTP API. Before committing to a Windows telemetry collector, test on two real multiplayer machines whether AMS2 shared-memory telemetry exposes **all opponents' final positions**, stable driver identities, qualifying classification, DNF/DSQ status, session identifiers and final penalty-adjusted classification. Some telemetry sources expose only live positions, not authoritative results. Do not substitute inferred finishing order for final classification.

## Proposed flow
1. Each BFR member may install a small Windows tray collector. It watches the AMS2 process and detects qualifying and race session transitions.
2. The collector keeps local observations while racing and waits for the final classification to stabilize. It stores a local retry queue and uploads over HTTPS when connectivity returns.
3. The backend authenticates devices, accepts immutable candidate submissions, assigns a race identity (season/round/session kind/track/start timestamp), and deduplicates uploads.
4. The backend reconciles submissions from multiple drivers, requiring consistent classifications. Conflicts or incomplete classifications enter **needs verification** and do not change official standings.
5. When the classification is trustworthy, map AMS2 participant IDs to the five league drivers (Craig, Dom, Kyle, Michal, Marcin); exclude unrelated participants from league points but preserve AI participation where needed for bonus rules.
6. Recalculate results using the existing `lib/scoring.ts` scoring engine. Publish a new authoritative season-results snapshot atomically, preserving historical results and an audit trail.
7. Update the Next.js site via database reads or deployment webhook/revalidation. Do not write directly to GitHub from players' computers.

## League-specific scoring considerations
Existing `Result` records have `qualifying`, `race1`, `race2`, and bonus flags. Some rounds may have two races; never assume every event has exactly one. The scoring engine gives 3/2/1 qualifying points, 25/22/20/18/16/14 race points, a bonus cap of 10 except round 10, and 1.5x race-position points in round 10. The top eight rounds count. Automatic bonus assignment needs a separate, tested mapping for fastest lap, most gained, clean race, AI counts, and relative-driver bonuses. Unknown flags must not be guessed or silently awarded.

## Security and reliability
- Device credentials per driver; revoke independently; never embed write tokens in the website.
- Server validates JSON shape, sizes, timestamps, event IDs and driver mapping.
- Idempotent submissions with deterministic fingerprints, and retries with exponential backoff.
- Store raw evidence and decision reason; require consensus or an authoritative final result before publishing.
- Never let a stale or partial session overwrite a published result.
- No automatic points when classifications conflict.
- Keep a manual recovery path for exceptional game-data failures, even though routine operation requires no human input.

## Phase gates
**A — Feasibility:** Run a player-hosted AMS2 test with two drivers; inspect telemetry from both machines and compare with the game's final result screen. Confirm whether qualifying and race classifications are available.

**B — Collector:** Implement and test Windows background collector against the verified data source; handle game restarts and offline retries.

**C — Backend:** Add authenticated result ingestion, deduplication, session reconciliation, persistence, and publication.

**D — Website:** Replace the checked-in static results snapshot with a trusted results service or an automated publishing process. Reuse `lib/scoring.ts`, and keep historical workbook data intact.

## Current status
Design only. No AMS2 adapter, live collector, backend, or automatic publishing is implemented. The earlier live-timing concept is intentionally out of scope.
