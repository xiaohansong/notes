# Dashboard refresh

How to regenerate the dashboard after editing workout logs.

There are two outputs, both built from the same parser:

- `dashboard/DASHBOARD.md` + `dashboard/charts/*.svg` — **for GitHub viewing**
- `dashboard/data.js` — for the static `index.html` (open locally)

## Trigger

User says "refresh the dashboard", "update dashboard", "regenerate the
summary", or similar after adding/editing files in `workout/YYYYMM/`.

## Steps

Run both generators (order doesn't matter):

```sh
python3 dashboard/render_md.py    # writes DASHBOARD.md + charts/*.svg
python3 dashboard/parse.py        # writes data.js
```

Each script prints what it wrote. Then:

- For GitHub: commit `DASHBOARD.md` and `charts/`. The `.md` renders inline
  on github.com with the SVGs.
- For local: open `dashboard/index.html` in a browser (no server).

## When parse fails

- A movement is missing from charts → the lift name in the log isn't in
  `lift_aliases`. Add it to `dashboard/config.json` under `lift_aliases`
  (lowercase name → canonical id) and re-run.
- Working sets not appearing → the working-set line must match
  `<load> × <reps>` (e.g. `185# × 5/5/5/5/5` or
  `305# × 3, 315# × 3`). See `workout/FORMAT.md`.

## Adding a new featured lift

If user wants a new lift charted prominently:

1. `lift_aliases`: add lowercase name → canonical id
2. `lift_display_names`: add canonical id → display name
3. `featured_lifts`: append the canonical id (drives e1RM trend + cards)
4. `pattern_buckets`: add to the matching movement-pattern list (drives
   weekly volume rollup)
5. Re-run both generators.

## Do not

- Do not start a server to view `index.html` — it's intentionally static.
- Do not edit `data.js`, `DASHBOARD.md`, or anything in `charts/` by hand.
  All generated.
- `matplotlib` is required for `render_md.py`. Install with
  `pip3 install matplotlib` if missing.
