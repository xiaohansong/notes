"""
Render dashboard data as a GitHub-friendly markdown file with embedded SVG charts.

Reads workout logs (via parse.build_dashboard_data), writes:
  - dashboard/DASHBOARD.md         (text + tables + <img> tags)
  - dashboard/charts/*.svg         (line / scatter / bar charts)

Run:
    python3 dashboard/render_md.py
"""

from __future__ import annotations

import sys
from datetime import date as Date, datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

DASH_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DASH_DIR))

from parse import build_dashboard_data  # noqa: E402

CHARTS_DIR = DASH_DIR / "charts"
# README.md so GitHub auto-renders this when navigating to the dashboard/ folder.
OUT_MD = DASH_DIR / "README.md"

README_FOOTER = """
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
"""

# Match the HTML dashboard's dark theme so the SVGs read well on GitHub
# (which renders both light and dark mode).
BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#23282f"

LIFT_COLORS = {
    "back_squat": "#f78166",
    "strict_press": "#58a6ff",
    "bench_press": "#d29922",
    "weighted_pullup": "#a371f7",
    "barbell_row": "#3fb950",
    "rdl": "#db61a2",
}

PATTERN_COLORS = {
    "squat": "#f78166",
    "hinge": "#d29922",
    "vertical_push": "#58a6ff",
    "horizontal_push": "#79c0ff",
    "vertical_pull": "#a371f7",
    "horizontal_pull": "#bc8cff",
    "carry": "#3fb950",
}

REP_PALETTE = [
    "#f78166", "#d29922", "#3fb950", "#58a6ff",
    "#a371f7", "#db61a2", "#79c0ff", "#bc8cff",
]


def _style_axes(ax):
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.grid(True, color=GRID, linewidth=0.6)


def _new_fig(w=9.0, h=4.5):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    _style_axes(ax)
    return fig, ax


def _save(fig, name: str) -> str:
    CHARTS_DIR.mkdir(exist_ok=True)
    path = CHARTS_DIR / name
    fig.tight_layout()
    fig.savefig(path, format="svg", facecolor=BG, edgecolor="none")
    plt.close(fig)
    return f"charts/{name}"


def render_e1rm_trend(data) -> str | None:
    featured = data["featured_lifts"]
    series_map = data["e1rm_series"]
    has_any = any(series_map.get(lid) for lid in featured)
    if not has_any:
        return None

    fig, ax = _new_fig()
    for lid in featured:
        series = series_map.get(lid) or []
        if not series:
            continue
        xs = [datetime.fromisoformat(p["date"]) for p in series]
        ys = [p["e1rm"] for p in series]
        ax.plot(
            xs, ys,
            marker="o", markersize=5, linewidth=2,
            color=LIFT_COLORS.get(lid, "#888"),
            label=data["lift_display_names"].get(lid, lid),
        )
    ax.set_ylabel("Estimated 1RM (lb)")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    leg = ax.legend(loc="lower left", facecolor=BG, edgecolor=GRID, labelcolor=FG)
    for text in leg.get_texts():
        text.set_color(FG)
    return _save(fig, "e1rm_trend.svg")


def render_zoom(data, lid: str, title: str) -> str | None:
    sets = data["zoom_sets"].get(lid) or []
    if not sets:
        return None

    by_reps: dict[int, list[dict]] = {}
    for s in sets:
        by_reps.setdefault(s["reps"], []).append(s)

    fig, ax = _new_fig()
    for i, reps in enumerate(sorted(by_reps.keys())):
        pts = by_reps[reps]
        xs = [datetime.fromisoformat(p["date"]) for p in pts]
        ys = [p["load_lb"] for p in pts]
        ax.scatter(
            xs, ys,
            color=REP_PALETTE[i % len(REP_PALETTE)],
            s=55, label=f"{reps} rep{'' if reps == 1 else 's'}",
            edgecolors="none",
        )
    ax.set_ylabel("Working set load (lb)")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    leg = ax.legend(loc="best", facecolor=BG, edgecolor=GRID, labelcolor=FG)
    for text in leg.get_texts():
        text.set_color(FG)
    return _save(fig, f"zoom_{lid}.svg")


def render_weekly_volume(data) -> str | None:
    weeks = data["weekly_volume"]
    if not weeks:
        return None

    buckets = data["pattern_buckets"]
    labels = [w["week_start"] for w in weeks]
    xs = list(range(len(labels)))

    fig, ax = _new_fig(w=9.0, h=4.8)
    bottoms = [0.0] * len(weeks)
    for bucket in buckets:
        ys = [w.get(bucket, 0) for w in weeks]
        ax.bar(
            xs, ys, bottom=bottoms,
            color=PATTERN_COLORS.get(bucket, "#888"),
            label=data["pattern_display_names"].get(bucket, bucket),
            width=0.7,
        )
        bottoms = [b + y for b, y in zip(bottoms, ys)]

    ax.set_xticks(xs)
    short_labels = [datetime.fromisoformat(d).strftime("%b %d") for d in labels]
    ax.set_xticklabels(short_labels, rotation=30, ha="right")
    ax.set_ylabel("Volume (load × reps, lb)")
    leg = ax.legend(loc="upper left", facecolor=BG, edgecolor=GRID, labelcolor=FG)
    for text in leg.get_texts():
        text.set_color(FG)
    return _save(fig, "weekly_volume.svg")


# ---------- markdown helpers ----------

def fmt_date_long(iso: str) -> str:
    return datetime.fromisoformat(iso).strftime("%b %-d")


def featured_table(data) -> str:
    rows = ["| Lift | Current e1RM | Top set | Date | Δ vs prior |",
            "|---|---:|---|---|---:|"]
    for lid in data["featured_lifts"]:
        name = data["lift_display_names"].get(lid, lid)
        series = data["e1rm_series"].get(lid) or []
        if not series:
            rows.append(f"| {name} | — | no sessions yet | — | — |")
            continue
        latest = series[-1]
        prev = series[-2] if len(series) > 1 else None
        if latest.get("added_lb") is not None:
            top = f"BW+{latest['added_lb']:g}# × {latest['top_reps']} (sys {latest['top_load_lb']:g}#)"
        else:
            top = f"{latest['top_load_lb']:g}# × {latest['top_reps']}"
        if prev:
            d = latest["e1rm"] - prev["e1rm"]
            sign = "+" if d > 0 else ""
            delta = f"{sign}{d:.1f}# vs {fmt_date_long(prev['date'])}"
        else:
            delta = "—"
        rows.append(
            f"| **{name}** | {latest['e1rm']:.0f}# | {top} | {fmt_date_long(latest['date'])} | {delta} |"
        )
    return "\n".join(rows)


def prs_table(data) -> str:
    prs = sorted(data["recent_prs"], key=lambda r: -r["e1rm"])
    if not prs:
        return "_No PRs in the last 8 weeks._"
    rows = ["| Lift | Top set | e1RM | Date |",
            "|---|---|---:|---|"]
    for r in prs:
        if r.get("added_lb") is not None:
            top = f"BW+{r['added_lb']:g}# × {r['top_reps']} (sys {r['top_load_lb']:g}#)"
        else:
            top = f"{r['top_load_lb']:g}# × {r['top_reps']}"
        rows.append(
            f"| {r['lift_name']} | {top} | {r['e1rm']:.1f}# | {fmt_date_long(r['date'])} |"
        )
    return "\n".join(rows)


def render_markdown(data, chart_paths: dict[str, str | None]) -> str:
    gen = datetime.fromisoformat(data["generated_at"])
    parts = [
        "# Strength dashboard",
        "",
        f"_Updated {gen.strftime('%b %-d, %Y %-I:%M %p')} · BW {data['bodyweight_lb']}#_",
        "",
        "## Featured lifts",
        "",
        featured_table(data),
        "",
    ]

    if chart_paths.get("e1rm"):
        parts += [
            "## Estimated 1RM trend — all featured lifts",
            "",
            f"![e1RM trend]({chart_paths['e1rm']})",
            "",
            "_Epley estimate from each session's top set. Sets above 10 reps excluded._",
            "",
        ]

    if chart_paths.get("squat"):
        parts += [
            "## Back squat — every working set",
            "",
            f"![Squat working sets]({chart_paths['squat']})",
            "",
            "_Each point is one set, colored by rep count._",
            "",
        ]

    if chart_paths.get("ohp"):
        parts += [
            "## Strict press — every working set",
            "",
            f"![Strict press working sets]({chart_paths['ohp']})",
            "",
            "_Cycle priority lift._",
            "",
        ]

    if chart_paths.get("volume"):
        parts += [
            "## Weekly volume by movement pattern",
            "",
            f"![Weekly volume]({chart_paths['volume']})",
            "",
            "_Stacked: total load × reps per pattern, week starting Monday._",
            "",
        ]

    parts += [
        "## Recent PRs (last 8 weeks)",
        "",
        prs_table(data),
        "",
        README_FOOTER,
    ]

    return "\n".join(parts)


def main():
    data = build_dashboard_data()
    chart_paths = {
        "e1rm": render_e1rm_trend(data),
        "squat": render_zoom(data, "back_squat", "Back squat"),
        "ohp": render_zoom(data, "strict_press", "Strict press"),
        "volume": render_weekly_volume(data),
    }
    md = render_markdown(data, chart_paths)
    OUT_MD.write_text(md)
    print(f"Wrote {OUT_MD}")
    for k, v in chart_paths.items():
        if v:
            print(f"  · {v}")


if __name__ == "__main__":
    main()
