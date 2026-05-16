# Egeyuma Dashboard

The dashboard is the SvelteKit app under `dashboard/`. It renders benchmark result
JSON files written by the engine.

## Layout

```text
dashboard/
  package.json
  src/
    app.html
    styles.css
    routes/
      +layout.svelte
      +page.server.ts
      +page.svelte
```

## Data Loading

The dashboard reads `*.json` result files from `../results` at request time. Override
that path with `EGEYUMA_RESULTS_DIR` when running the dashboard from a different
workspace layout.

Invalid JSON files or JSON files that do not match the Egeyuma result payload shape
are ignored.

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

Use SvelteKit server loading for filesystem access. Keep browser components free of
direct Node filesystem imports.

`dashboard/src/app.html` is required by SvelteKit. `dashboard/package-lock.json`
should be committed so dashboard installs remain reproducible.

Run checks from `dashboard/`.
