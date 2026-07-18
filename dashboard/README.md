# Strength dashboard

_Updated Jul 18, 2026 7:36 PM · BW 177#_

## Featured lifts

| Lift | Current e1RM | Top set | Date | Δ vs prior |
|---|---:|---|---|---:|
| **Back squat** | 385# | 385# × 1 | May 19 | +5.0# vs May 12 |
| **Strict press** | 126# | 105# × 6 | Jul 14 | -21.3# vs Jul 10 |
| **Deadlift** | 380# | 345# × 3 | Jul 14 | +3.2# vs Jul 10 |
| **Bench press** | 210# | 175# × 6 | Jul 15 | -5.8# vs May 9 |
| **Weighted pull-up** | 247# | BW+35# × 5 (sys 212#) | May 4 | 0.0# vs Apr 27 |
| **Barbell row** | 171# | 135# × 8 | May 9 | -9.0# vs May 2 |

## Estimated 1RM trend — all featured lifts

![e1RM trend](charts/e1rm_trend.svg)

_Epley estimate from each session's top set. Sets above 10 reps excluded._

## Back squat — daily volume by load

![Squat daily volume](charts/zoom_back_squat.svg)

_One dot per (date, load). Dot size scales with total reps that day at that load._

## Strict press — daily volume by load

![Strict press daily volume](charts/zoom_strict_press.svg)

_One dot per (date, load). Dot size scales with total reps that day at that load. Cycle priority lift._

## Weekly volume by movement pattern

![Weekly volume](charts/weekly_volume.svg)

_Stacked: total load × reps per pattern, week starting Monday._

## Recent PRs (last 8 weeks)

| Lift | Top set | e1RM | Date |
|---|---|---:|---|
| Deadlift | 345# × 3 | 379.5# | Jul 14 |
| Bench press | 175# × 6 | 210.0# | Jul 15 |
| Strict press | 130# × 4 | 147.3# | Jul 10 |


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
