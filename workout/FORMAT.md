# Workout log format

The dashboard parser reads files in `workout/YYYYMM/YYYYMMDD`. Keep this format
consistent and the dashboard charts will stay accurate.

## File header

First line is the date in ISO form:

```
# 2026-05-04
```

## Each movement is its own block

```
## <Lift name> — <scheme>
<load> × <per-set reps>
<optional notes line(s)>
```

- **Lift name** — match prior usage (case-insensitive). Canonical names the
  parser already understands: `back squat`, `front squat`, `bench press`,
  `incline bench press`, `strict press`, `push press`, `weighted pull-up`,
  `weighted chin-up`, `weighted dip`, `barbell row`, `db row`, `rdl`,
  `deadlift`, `bulgarian split squat`, `goblet squat`, `kb swing`,
  `suitcase carry`. Anything else is logged but not charted.
- **Scheme** — freeform, e.g. `E3:00 × 5`, `5×5`, `5 sets NFT`, `AMRAP 10:00`,
  `build to heavy 3`. Parser ignores this field; it's for you.
- **Load** — `185#` (lb), `90kg`, `BW`, `BW+35#` (added load on
  bodyweight movement). `BW` resolves to the bodyweight in
  `dashboard/config.json`.
- **Per-set reps** — slash-separated, one number per set. Examples:
  - All sets equal: `5/5/5/5/5` *or* the single-number shortcut `5×5` (5 sets
    of 5)
  - Cut on last set: `5/5/5/5/4`
  - Time hold: `25s/25s/25s/25s` (parser treats as duration, not reps)
  - Carry distance: `100ft/100ft/100ft` (each round)

### Loads vary across sets

When the load climbs (or drops) across sets, write each set as its own
`load × reps` pair, comma-separated:

```
## Back squat — build to heavy 3
305# × 3, 315# × 3, 325# × 3, 335# × 3, 345# × 2
```

### Supersets

Two movements paired in one block — write each as its own `##` section, and
add `(superset)` to the second one's scheme line:

```
## Bench press — E3:00 × 5
185# × 5/5/5/5/5

## Barbell row — E3:00 × 5 (superset)
135# × 10/10/8/8/8
```

### Failed attempts

The working-set line is **completed sets only** — do NOT list reps that
failed. Put failed attempts in the notes below the load line:

```
## Strict press — build to heavy single
135# × 3, 145# × 2, 150# × 2
attempted 155# × 1 twice, both failed.
```

This keeps the e1RM and zoom-chart points honest. A "cut" mid-set (e.g.
went for 5, finished 4) is fine to write as `4` on the slash list — that
counts as a completed 4-rep set.

### Notes

Anything below the load line, until the next `##` header, is freeform notes:
RPE, failed attempts, tempo, how it felt. Parser preserves it in the data
but doesn't try to extract structure.

```
## Strict press — E2:30 × 5
120# × 5/5/5/5/5
RPE 8 on last set. shoulder felt fine.
```

## Rest days

Single line, no movement blocks:

```
# 2026-05-03

Rest day.
```

Active rest (hike, easy bike, etc.) — note it on the same line:

```
# 2026-04-25

Rest day. Hiking.
```

## Conditioning / accessory work

Log it the same way (`##` block, scheme, load, reps). The dashboard filters
to main lifts for the e1RM and volume charts, so accessory and conditioning
sit in the data without polluting the headline charts.
