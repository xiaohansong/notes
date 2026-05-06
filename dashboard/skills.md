# Dashboard refresh

How to regenerate the dashboard after editing workout logs.

There are two outputs, both built from the same parser:

- `dashboard/README.md` + `dashboard/charts/*.svg` — **for GitHub viewing**
- `dashboard/data.js` — for the static `index.html` (open locally)

## Trigger

User says "refresh the dashboard", "update dashboard", "regenerate the
summary", or similar after adding/editing files in `workout/YYYYMM/`.

## Steps

1. Run both generators (order doesn't matter):

   ```sh
   python3 dashboard/render_md.py    # writes README.md + charts/*.svg
   python3 dashboard/parse.py        # writes data.js
   ```

   Each script prints what it wrote.
2. **Verify the new session actually landed.** Diff `dashboard/README.md`
   — at minimum the timestamp should change AND if the session contained
   a featured lift (squat / press / bench / pull-up / row), the
   featured-lift table or PR table should reflect it. If only the
   timestamp moved, the parser didn't pick up the movements — see
   *Diagnostic* below.
3. Commit `workout/...` (if edited), `README.md`, and `charts/`. The
   `.md` renders inline on github.com with the SVGs. For the local view,
   open `dashboard/index.html` in a browser (no server).

## Diagnostic — did the parser see the log?

The workout log is freeform; the parser only picks up movements when
it recognizes a working-set pattern. To check what landed for a given
date:

```sh
python3 -c "
import sys; sys.path.insert(0, 'dashboard')
from parse import parse_all
DATE = '2026-05-04'  # change to the date you just edited
for s in parse_all():
    if s.date != DATE: continue
    print(s.date, s.type)
    for m in s.movements:
        print(' ', m.lift_id or '?', '|', m.lift_raw,
              '->', [(ws.raw_load, ws.raw_reps) for ws in m.sets])
"
```

If the date prints with **zero movement lines**, the parser didn't find
anything chartable. That's not wrong — the log entry is still valid —
but the dashboard won't graph it. Patterns the parser recognizes:

- A `## <Lift name>` header for each movement.
- A working-set line of the form `<load> × <reps>` underneath:
  `185# × 5/5/5/5/5`, `5×5`, `305# × 3, 315# × 3, 325# × 3`.
- A leading `# YYYY-MM-DD` header on the file.

If you want a session graphed, edit it to include those patterns. If
you don't care about the graph for that session, leave it.

## When a movement is missing from charts

- Lift name not recognized → add it to `lift_aliases` in
  `dashboard/config.json` (lowercase name → canonical id) and re-run.
- Working sets not appearing → the working-set line needs to match
  `<load> × <reps>` (e.g. `185# × 5/5/5/5/5` or
  `305# × 3, 315# × 3`).

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
- Do not edit `data.js`, `README.md`, or anything in `charts/` by hand.
  All generated.
- `matplotlib` is required for `render_md.py`. Install with
  `pip3 install matplotlib` if missing.
