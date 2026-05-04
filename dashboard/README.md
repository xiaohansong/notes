# Strength dashboard

Tracks strength progression off the `workout/YYYYMM/YYYYMMDD` logs. Charts:

- Featured-lift cards: current e1RM, top set, delta vs prior session
- Estimated 1RM trend across all featured lifts
- Squat zoom: every working set
- Strict press zoom: every working set
- Weekly volume by movement pattern
- Recent PRs (8-week trailing)

## Use

Two view modes, both fully static:

- **GitHub** — view [`DASHBOARD.md`](DASHBOARD.md) on github.com.
  Regenerate with `python3 dashboard/render_md.py` (writes the .md plus
  SVG charts under `charts/`). Requires `matplotlib`.
- **Local browser** — open `dashboard/index.html` directly.
  Regenerate with `python3 dashboard/parse.py` (writes `data.js`).

## Adding new lifts to the dashboard

1. Add the lift name (lowercased) to `lift_aliases` in `config.json`, mapping
   to a canonical id.
2. Add the canonical id to `lift_display_names`.
3. To chart it on the e1RM line, add the id to `featured_lifts`.
4. To include it in volume rollups, add the id to one of the
   `pattern_buckets` lists.

## Format

Logs follow `workout/FORMAT.md`. The parser is permissive but the working-set
line (`<load> × <reps>` or `<load> × <reps>, <load> × <reps>, ...`) must be
present for a movement to contribute to charts.
