# Strength dashboard

_Updated May 3, 2026 9:57 PM · BW 180#_

## Featured lifts

| Lift | Current e1RM | Top set | Date | Δ vs prior |
|---|---:|---|---|---:|
| **Back squat** | 368# | 335# × 3 | May 1 | +12.7# vs Apr 27 |
| **Strict press** | 140# | 120# × 5 | Apr 29 | -20.0# vs Apr 22 |
| **Bench press** | 216# | 185# × 5 | May 2 | 0.0# vs Apr 26 |
| **Weighted pull-up** | 251# | BW+35# × 5 (sys 215#) | Apr 27 | 0.0# vs Apr 22 |
| **Barbell row** | 180# | 135# × 10 | May 2 | +53.3# vs Apr 23 |
| **RDL** | 260# | 195# × 10 | Apr 23 | -4.0# vs Apr 17 |

## Estimated 1RM trend — all featured lifts

![e1RM trend](charts/e1rm_trend.svg)

_Epley estimate from each session's top set. Sets above 10 reps excluded._

## Back squat — every working set

![Squat working sets](charts/zoom_back_squat.svg)

_Each point is one set, colored by rep count._

## Strict press — every working set

![Strict press working sets](charts/zoom_strict_press.svg)

_Cycle priority lift._

## Weekly volume by movement pattern

![Weekly volume](charts/weekly_volume.svg)

_Stacked: total load × reps per pattern, week starting Monday._

## Recent PRs (last 8 weeks)

| Lift | Top set | e1RM | Date |
|---|---|---:|---|
| Back squat | 335# × 3 | 368.5# | May 1 |
| RDL | 198# × 10 | 264.0# | Apr 17 |
| Weighted pull-up | BW+35# × 5 (sys 215#) | 250.8# | Apr 27 |
| Bench press | 185# × 5 | 215.8# | May 2 |
| Barbell row | 135# × 10 | 180.0# | Apr 19 |
| Strict press | 150# × 2 | 160.0# | Apr 22 |


---

## How this is generated

Two view modes, both fully static:

- **GitHub** — this `README.md`, rendered above. Regenerate with
  `python3 dashboard/render_md.py` (writes the .md plus SVG charts under
  `charts/`). Requires `matplotlib`.
- **Local browser** — open `dashboard/index.html` directly. Regenerate
  with `python3 dashboard/parse.py` (writes `data.js`).

### Adding a new lift to the dashboard

1. Add the lift name (lowercased) to `lift_aliases` in `config.json`,
   mapping to a canonical id.
2. Add the canonical id to `lift_display_names`.
3. To chart it on the e1RM line, add the id to `featured_lifts`.
4. To include it in volume rollups, add the id to one of the
   `pattern_buckets` lists.

### Format

Logs follow `workout/FORMAT.md`. The parser is permissive but the
working-set line (`<load> × <reps>` or `<load> × <reps>, ...`) must be
present for a movement to contribute to charts.
