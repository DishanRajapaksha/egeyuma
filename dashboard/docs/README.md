# Egeyuma Dashboard

The dashboard is the SvelteKit app under `dashboard/`. It renders benchmark result
JSON files written by the engine.

## Layout

```text
dashboard/
  package.json
  src/
    app.html
    scripts/
      prepare-results.mjs
    static/
      results/
    styles.css
    routes/
      +layout.svelte
      +page.ts
      +page.svelte
```

## Data Loading

The dashboard is static-page friendly. Before `dev` and `build`, the
`prepare-results` script copies committed result files from `../results/published`
into `dashboard/static/results` and writes a `results/index.json` manifest.

Invalid JSON files or JSON files that do not match the Egeyuma result payload shape
fail the prepare step. Raw local result files should stay under `results/` and remain
ignored; only curated publishable JSON belongs in `results/published/`.

## UI Structure

The main dashboard renders:

- summary metrics for run count, best accuracy, latest accuracy, and invalid rate
- leaderboard ranked by accuracy and then by latest modification time
- latest-run details and run metadata
- breakdown cards for subject, domain, difficulty, and language style
- sample-level audit table with gold labels, predictions, status, and raw response

The styling is intentionally closer to standard model benchmarking dashboards than
to a marketing landing page: dense tables, compact metric cards, restrained colors,
and scan-friendly typography.

## Development Notes

Use SvelteKit universal loading and `fetch` for result data so the app can run from
GitHub Pages. Keep Node filesystem access inside `scripts/prepare-results.mjs`.

`dashboard/src/app.html` is required by SvelteKit. `dashboard/package-lock.json`
should be committed so dashboard installs remain reproducible.

The Pages workflow builds the dashboard with `BASE_PATH=/egeyuma/benchmarks` and
copies `dashboard/build` into the combined Pages artifact at `benchmarks/`.

Run checks from `dashboard/`.
