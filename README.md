# Black Flag Racing — AMS2 Championship

Public, read-only Next.js championship website for the Black Flag Racing Fall 2026 season.

## Run locally
Requires Node.js 20+ and npm.

```bash
npm install
npm run dev
```

Open http://localhost:3000. Pages: Overview, Standings, Calendar, Results, Drivers.

## Excel import
Ovi is deliberately excluded by the importer (five active competitors), even while he remains in the historical Excel workbook.\n\nThe checked-in `data/championship.json` is a snapshot of the supplied **BFR Fall 2026 League.xlsx** workbook. The site reads this file at build time. To refresh it after editing the workbook:

```bash
python scripts/import_excel.py "/path/to/BFR Fall 2026 League.xlsx"
npm run build
```

Requires Python 3 and `pip install artifact-tool`. The importer reads Schedule, Drivers, and Season Results. Commit the updated JSON to publish changes after deployment. The original workbook is not committed.

## Validation\n\n```bash\nnpm test\nnpm run typecheck\nnpm run build\n```\n\nGitHub Actions is configured to run these checks for every push and pull request. Check the Actions tab for the first verified result; local package installation was unavailable in the initial development environment.\n\n## Scoring
Qualifying positions 1–3: 3, 2, 1 points. Race positions 1–6: 25, 22, 20, 18, 16, 14. Achievement bonuses follow the workbook. Five-AI bonus replaces three-AI bonus. Bonus cap 10 except in Round 10; Round 10 multiplies race-position points by 1.5 only. Best 8 of 10 round totals count. Only entered results are counted. Tie-break ordering is provisional until the league confirms its official rules.

## Current limitations
This is **Phase 1–2**: a functioning public site and deterministic scoring engine, not yet live-hosted or automatically synced to Excel/AMS2. Data refresh currently requires running the importer and committing the generated JSON. No admin login, database, automated deployment, telemetry capture, or live results ingestion is configured yet. The initial snapshot contains only populated results from rounds 1–3; absent rows are not interpreted as finishes. This is not an official timing system.

## Deployment
Connect this GitHub repository to a Next.js-compatible host (e.g. Vercel), use `npm run build`, and configure automatic deployments from `main`. No secrets are required for the public read-only prototype.
