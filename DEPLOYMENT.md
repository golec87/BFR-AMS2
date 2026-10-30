# Deploy Black Flag Racing to Vercel

1. Sign in to https://vercel.com with GitHub.
2. Select **Add New → Project** and import **golec87/BFR-AMS2**. If it is not visible, grant Vercel GitHub app access to this repository.
3. Leave the framework preset as **Next.js**, root directory as **./**, and build command as **npm run build**.
4. Click **Deploy**. Vercel will issue a public `*.vercel.app` URL after a successful build.
5. In **Project → Settings → Domains**, optionally add a custom domain. Follow the exact DNS records Vercel displays.
6. Later pushes to `main` trigger redeployments. The current data source is `data/championship.json`, not a live workbook feed.

Before deployment, run `npm install && npm test && npm run typecheck && npm run build`. The GitHub Actions workflow also validates pushes and PRs.

## Data refresh

Run `python scripts/import_excel.py "/path/to/BFR Fall 2026 League.xlsx"` after changing the spreadsheet, then commit `data/championship.json`. Ovi is excluded from the active roster by the importer.

**Security:** The site is public and read-only. Do not commit private data, Excel files with personal information, tokens, or Vercel credentials.
