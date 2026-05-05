# Dashboard refresh

How to regenerate the dashboard after editing workout logs.

There are two outputs, both built from the same parser:

- `dashboard/README.md` + `dashboard/charts/*.svg` — **for GitHub viewing**
- `dashboard/data.js` — for the static `index.html` (open locally)

## Trigger

User says "refresh the dashboard", "update dashboard", "regenerate the
summary", or similar after adding/editing files in `workout/YYYYMM/`.

## Steps

1. **Verify the workout log is in canonical format first.** The parser
   silently produces an empty session for files that don't match
   `workout/FORMAT.md` — running the generators on a malformed log will
   regenerate `README.md` (timestamp moves) without picking up any
   movements, and the charts will look unchanged. See *Pre-flight check*
   below before regenerating.
2. Run both generators (order doesn't matter):

   ```sh
   python3 dashboard/render_md.py    # writes README.md + charts/*.svg
   python3 dashboard/parse.py        # writes data.js
   ```

   Each script prints what it wrote.
3. **Verify the new session actually landed.** Diff `dashboard/README.md`
   — at minimum the timestamp should change AND if the session contained
   a featured lift (squat / press / bench / pull-up / row), the
   featured-lift table or PR table should reflect it. If only the
   timestamp moved, the parser didn't read the movements (see
   *Pre-flight check*).
4. Commit `workout/...` (if edited), `README.md`, and `charts/`. The
   `.md` renders inline on github.com with the SVGs. For the local view,
   open `dashboard/index.html` in a browser (no server).

## Pre-flight check — confirm the parser sees the log

Before regenerating, sanity-check that today's log parses. Run:

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

If the date prints with **zero movement lines**, the file isn't in the
canonical format — fix the file before regenerating. Common causes:

- Prose narration (`Squat every 3:30 for 5 sets / 315# for 5 reps`)
  instead of `## <Lift> — <scheme>` blocks with a `<load> × <reps>` line.
- Missing the leading `# YYYY-MM-DD` header.
- Reps written `5 reps` or `5x5` instead of `5/5/5/5/5` or `5×5`.

See `workout/FORMAT.md` for the spec and reformat the file. Then re-run
the pre-flight before regenerating.

## When parse fails

- The whole session has zero movements → the log isn't in canonical
  format. Run the pre-flight snippet above to confirm, then reformat
  the file per `workout/FORMAT.md`.
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
- Do not edit `data.js`, `README.md`, or anything in `charts/` by hand.
  All generated.
- `matplotlib` is required for `render_md.py`. Install with
  `pip3 install matplotlib` if missing.
