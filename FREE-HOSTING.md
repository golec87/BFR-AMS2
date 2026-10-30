# Free public hosting — GitHub Pages

The website is configured for a static Next.js export under the repository path `/BFR-AMS2`. This needs no hosting subscription, database, or custom domain.

## One-time GitHub setup

1. Visit https://github.com/golec87/BFR-AMS2/settings/pages
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Visit https://github.com/golec87/BFR-AMS2/actions and select **Deploy free GitHub Pages website**. If needed, click **Run workflow**.
4. After a successful deployment, visit https://golec87.github.io/BFR-AMS2/

Every subsequent push to `main` triggers tests, a static build, and deployment. GitHub Actions and Pages free-tier quotas apply.

## Updating the championship

Run `python scripts/import_excel.py "BFR Fall 2026 League.xlsx"`, review the updated `data/championship.json`, and commit it. The site will rebuild and republish without a monthly hosting fee. The importer excludes Ovi from the active roster.

## Important limits

The site is a public read-only snapshot. A browser cannot access your private local Excel file directly. True automatic ingestion of AMS2 results will require a separate uploader, such as a small Windows script on the race PC that commits generated results to GitHub using a suitably restricted token. Do not expose GitHub tokens in frontend code.
