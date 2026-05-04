# Training repo

Personal strength-training log and Claude-driven programming workflow.
Workouts, plans, and analysis live as flat markdown files; the dashboard
renders the log into charts.

## Start here

If you just want to see where things stand:

1. **[dashboard/README.md](dashboard/README.md)** — current e1RM trend,
   per-lift zoom charts, weekly volume, recent PRs. Regenerated from the
   workout log.
2. **[Balance](Balance)** — rolling 28-day movement-pattern volume,
   capacity snapshot, currently flagged imbalances, and the programming
   assumptions in effect for the cycle.
3. **`planning/YYYYMM/`** — the next ~7 days of prescribed sessions.
4. **`workout/YYYYMM/`** — what was actually done.

## Layout

| Path | What's in it |
|---|---|
| `Skills` | Programmer agent instructions: role, naming convention, progression rules, planning file format. Read this to understand how plans are generated. |
| `Feedback.md` | Independent reviewer agent instructions: audits last session vs plan and grades the upcoming week. |
| `Balance` | Weekly-review artifact: movement-pattern volume, capacity snapshot, imbalances, cycle assumptions. |
| `Record/` | Personal lifting bests. |
| `planning/YYYYMM/YYYYMMDD[.md]` | Generated daily plans (prescription + coach's notes). |
| `workout/YYYYMM/YYYYMMDD` | Actual session log. Format spec: [workout/FORMAT.md](workout/FORMAT.md). |
| `notes/` | Weekly programmer notes (date-range filenames, e.g. `0420-0425`). Context the programmer carries forward week to week. |
| `feedback/YYYYMMDD.md` | Per-session reviewer output (adherence + plan-quality grade). |
| `dashboard/` | Static dashboard. `index.html` for local browser view; `README.md` for the GitHub-rendered version. |

## Workflow

- **Each session** — log to `workout/YYYYMM/YYYYMMDD` per
  [workout/FORMAT.md](workout/FORMAT.md). The reviewer agent
  (`Feedback.md`) writes a feedback file the next day.
- **Each week** — programmer agent (`Skills`) reads recent workouts,
  refreshes `Balance`, appends a note to `notes/`, and writes the next
  7 days into `planning/`.
- **Dashboard refresh** — `python3 dashboard/render_md.py` rebuilds
  `dashboard/README.md` and the SVG charts under `dashboard/charts/`.
  `python3 dashboard/parse.py` rebuilds `dashboard/data.js` for the
  local HTML view.

## Conventions

- Dates are ISO-like with no separators in filenames: `20260503` =
  2026-05-03.
- Month folders (`YYYYMM/`) under `planning/` and `workout/`. Reads
  that span week boundaries cross month folders.
- Loads in pounds with a trailing `#` (`185#`); `BW` and `BW+35#` for
  bodyweight movements. Bodyweight lives in `dashboard/config.json`.
- No personal identifiers in any repo file — the repo is pushed to
  GitHub.
