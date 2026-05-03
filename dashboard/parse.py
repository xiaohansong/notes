"""
Parse workout/YYYYMM/YYYYMMDD logs into structured JSON for the dashboard.

Format spec lives in workout/FORMAT.md. The parser is permissive about
whitespace and casing but strict about the working-set line shape.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from datetime import date as Date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
WORKOUT_DIR = ROOT / "workout"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"

DATE_HEADER_RE = re.compile(r"^#\s*(\d{4})-(\d{2})-(\d{2})\s*$")
MOVEMENT_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$")
REST_RE = re.compile(r"\brest day\b", re.IGNORECASE)
ACTIVE_REST_HINT_RE = re.compile(r"\b(hike|hiking|bike|swim|walk|outdoor)\b", re.IGNORECASE)

# Working-set line patterns
LOAD_REPS_SPLIT_RE = re.compile(r"\s*[×x]\s*", re.IGNORECASE)


@dataclass
class WorkingSet:
    load_lb: float | None  # absolute load in lb (BW resolved). None = no measurable load.
    added_lb: float | None  # added load on top of BW (for weighted-bodyweight movements)
    reps: int | None
    duration_s: int | None  # for time holds
    distance_ft: int | None  # for carries
    raw_load: str = ""
    raw_reps: str = ""


@dataclass
class Movement:
    lift_raw: str
    lift_id: str  # canonical id from aliases, or "" if unknown
    scheme: str
    superset: bool
    sets: list[WorkingSet] = field(default_factory=list)
    notes: str = ""


@dataclass
class Session:
    date: str  # ISO YYYY-MM-DD
    type: str  # "workout" | "rest" | "active_rest"
    movements: list[Movement] = field(default_factory=list)
    raw_notes: str = ""


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def normalize_lift_name(raw: str, aliases: dict[str, str]) -> tuple[str, str, bool]:
    """Returns (lift_id, scheme, superset)."""
    superset = False
    s = raw.strip()
    # Strip trailing "(superset)" annotation
    m = re.search(r"\(superset[^)]*\)", s, re.IGNORECASE)
    if m:
        superset = True
        s = (s[: m.start()] + s[m.end() :]).strip()

    # Split off scheme on em-dash or hyphen-with-spaces
    parts = re.split(r"\s+—\s+|\s+-\s+", s, maxsplit=1)
    name = parts[0].strip()
    scheme = parts[1].strip() if len(parts) > 1 else ""

    name_norm = name.lower()
    lift_id = aliases.get(name_norm, "")
    if not lift_id:
        # Try a few looser variants — strip trailing 's', spaces, hyphens
        candidates = [
            name_norm.rstrip("s"),
            name_norm.replace("-", " "),
            name_norm.replace("  ", " "),
        ]
        for c in candidates:
            if c in aliases:
                lift_id = aliases[c]
                break

    return lift_id, scheme, superset


def parse_load(token: str, bodyweight: float) -> tuple[float | None, float | None]:
    """Returns (absolute_load_lb, added_lb).

    For BW: (bodyweight, None).
    For BW+35#: (bodyweight + 35, 35).
    For 185#: (185, None).
    For 90kg: (90 * 2.20462, None).
    For band/red band: (None, None).
    For unknowns: (None, None).
    """
    t = token.strip()
    if not t:
        return None, None

    t_low = t.lower()

    if t_low == "bw":
        return bodyweight, None
    m = re.match(r"^bw\s*\+\s*(\d+(?:\.\d+)?)\s*#?$", t_low)
    if m:
        added = float(m.group(1))
        return bodyweight + added, added

    m = re.match(r"^(\d+(?:\.\d+)?)\s*kg$", t_low)
    if m:
        return float(m.group(1)) * 2.20462, None

    m = re.match(r"^(\d+(?:\.\d+)?)\s*#$", t_low)
    if m:
        return float(m.group(1)), None

    # Unitless number — assume lb (e.g. user wrote "255" without #)
    m = re.match(r"^(\d+(?:\.\d+)?)$", t_low)
    if m:
        return float(m.group(1)), None

    # Box height in inches — not a load
    if re.match(r"^\d+\"$", t):
        return None, None

    if t_low in {"band", "red band", "blue band", "green band", "black band"}:
        return None, None

    return None, None


def parse_rep_token(token: str) -> tuple[int | None, int | None, int | None]:
    """Returns (reps, duration_s, distance_ft) — exactly one is non-None or all None."""
    t = token.strip().lower()
    if not t or t == "?":
        return None, None, None

    m = re.match(r"^(\d+)\s*s$", t)
    if m:
        return None, int(m.group(1)), None

    m = re.match(r"^(\d+)\s*ft$", t)
    if m:
        return None, None, int(m.group(1))

    m = re.match(r"^(\d+)$", t)
    if m:
        return int(m.group(1)), None, None

    return None, None, None


def parse_working_set_line(line: str, bodyweight: float) -> list[WorkingSet]:
    """Parse a working-set line into one or more sets.

    Constant load: "185# × 5/5/5/5/5"  -> 5 sets of 5 at 185#
    Varying:       "305# × 3, 315# × 3, 325# × 3"  -> 3 sets at varying loads
    """
    line = line.strip()
    if not line:
        return []

    # Strip trailing parenthetical annotations like "(each hand)" before parsing.
    # We need to keep them in raw notes — caller can handle separately. Here we
    # strip just for parse cleanliness.
    line_for_parse = re.sub(r"\([^)]*\)\s*$", "", line).strip()

    # Split on commas to handle varying loads
    chunks = [c.strip() for c in line_for_parse.split(",") if c.strip()]
    sets: list[WorkingSet] = []

    for chunk in chunks:
        parts = LOAD_REPS_SPLIT_RE.split(chunk, maxsplit=1)
        if len(parts) != 2:
            continue
        load_str, reps_str = parts[0].strip(), parts[1].strip()
        # Reps str may contain trailing words like "each side" — strip them.
        reps_str_clean = re.split(r"\s+(?:each|alternating|alt)\b", reps_str, maxsplit=1)[0].strip()

        load_lb, added_lb = parse_load(load_str, bodyweight)

        # Reps split on / for per-set
        rep_tokens = [r.strip() for r in reps_str_clean.split("/") if r.strip()]
        for rt in rep_tokens:
            reps, dur, dist = parse_rep_token(rt)
            if reps is None and dur is None and dist is None:
                continue
            sets.append(
                WorkingSet(
                    load_lb=load_lb,
                    added_lb=added_lb,
                    reps=reps,
                    duration_s=dur,
                    distance_ft=dist,
                    raw_load=load_str,
                    raw_reps=rt,
                )
            )
    return sets


def parse_session(text: str, file_date: Date, config: dict[str, Any]) -> Session:
    bodyweight = float(config["bodyweight_lb"])
    aliases = config["lift_aliases"]

    lines = text.splitlines()
    iso_date = file_date.isoformat()

    # Find date header
    for line in lines:
        m = DATE_HEADER_RE.match(line.strip())
        if m:
            iso_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            break

    # Detect rest-only file
    body = "\n".join(l for l in lines if not DATE_HEADER_RE.match(l.strip())).strip()
    has_movements = any(MOVEMENT_HEADER_RE.match(l.strip()) for l in lines)

    if not has_movements:
        if REST_RE.search(body):
            session_type = "active_rest" if ACTIVE_REST_HINT_RE.search(body) else "rest"
            return Session(date=iso_date, type=session_type, raw_notes=body)
        return Session(date=iso_date, type="rest", raw_notes=body)

    # Walk through, splitting on `## ` headers
    movements: list[Movement] = []
    current: Movement | None = None
    pending_lines: list[str] = []

    def flush_current():
        nonlocal current, pending_lines
        if current is None:
            return
        # First non-empty line of pending = working-set line; rest = notes.
        ws_line = ""
        notes_lines: list[str] = []
        seen_ws = False
        for pl in pending_lines:
            if not pl.strip():
                if seen_ws:
                    notes_lines.append(pl)
                continue
            if not seen_ws:
                ws_line = pl.strip()
                seen_ws = True
            else:
                notes_lines.append(pl)
        if ws_line:
            current.sets = parse_working_set_line(ws_line, bodyweight)
        current.notes = "\n".join(notes_lines).strip()
        movements.append(current)
        current = None
        pending_lines = []

    for line in lines:
        stripped = line.strip()
        if DATE_HEADER_RE.match(stripped):
            continue
        m = MOVEMENT_HEADER_RE.match(stripped)
        if m:
            flush_current()
            header = m.group(1)
            lift_id, scheme, superset = normalize_lift_name(header, aliases)
            current = Movement(
                lift_raw=header,
                lift_id=lift_id,
                scheme=scheme,
                superset=superset,
            )
            continue
        if current is not None:
            pending_lines.append(line)

    flush_current()

    return Session(date=iso_date, type="workout", movements=movements)


def parse_all() -> list[Session]:
    config = load_config()
    sessions: list[Session] = []
    for month_dir in sorted(WORKOUT_DIR.iterdir()):
        if not month_dir.is_dir():
            continue
        if not re.match(r"^\d{6}$", month_dir.name):
            continue
        for f in sorted(month_dir.iterdir()):
            if not re.match(r"^\d{8}$", f.name):
                continue
            try:
                file_date = Date(int(f.name[0:4]), int(f.name[4:6]), int(f.name[6:8]))
            except ValueError:
                continue
            text = f.read_text()
            session = parse_session(text, file_date, config)
            sessions.append(session)
    sessions.sort(key=lambda s: s.date)
    return sessions


# ---------- Derived metrics ----------

def epley_e1rm(load: float, reps: int) -> float:
    """Estimated 1RM using Epley. Valid for reps ~1–10."""
    if reps <= 0:
        return 0.0
    if reps == 1:
        return load
    return load * (1.0 + reps / 30.0)


def best_e1rm_for_session(movement: Movement) -> float | None:
    """Best e1RM across the working sets in this movement."""
    best = 0.0
    for s in movement.sets:
        if s.load_lb is None or s.reps is None:
            continue
        if s.reps > 10:
            continue  # Epley over-estimates beyond ~10 reps
        e = epley_e1rm(s.load_lb, s.reps)
        if e > best:
            best = e
    return best if best > 0 else None


def session_volume_lb(movement: Movement) -> float:
    """Sum of load × reps across sets."""
    total = 0.0
    for s in movement.sets:
        if s.load_lb is None or s.reps is None:
            continue
        total += s.load_lb * s.reps
    return total


def iso_week_start(d: Date) -> str:
    """Return ISO date string of the Monday of the week containing d."""
    monday = d - __import__("datetime").timedelta(days=d.weekday())
    return monday.isoformat()


def build_dashboard_data() -> dict[str, Any]:
    config = load_config()
    sessions = parse_all()

    aliases = config["lift_aliases"]
    featured = config["featured_lifts"]
    zoom = config["zoom_lifts"]
    pattern_buckets = config["pattern_buckets"]
    display_names = config["lift_display_names"]
    pattern_names = config["pattern_display_names"]

    # Build lift_id -> bucket map
    lift_to_bucket: dict[str, str] = {}
    for bucket, lifts in pattern_buckets.items():
        for l in lifts:
            lift_to_bucket[l] = bucket

    # Per-lift e1RM time series (only featured)
    e1rm_series: dict[str, list[dict[str, Any]]] = {l: [] for l in featured}
    # Squat working sets (zoom): every set for back_squat
    zoom_working_sets: dict[str, list[dict[str, Any]]] = {z: [] for z in zoom}
    # Weekly volume by pattern
    weekly_volume: dict[str, dict[str, float]] = {}  # week_start -> bucket -> lb
    # Recent PRs: best e1RM per lift in last 8 weeks, with date
    recent_prs: dict[str, dict[str, Any]] = {}

    from datetime import datetime, timedelta
    today = Date.today()
    pr_window_start = today - timedelta(weeks=8)

    for session in sessions:
        if session.type != "workout":
            continue
        try:
            sdate = Date.fromisoformat(session.date)
        except ValueError:
            continue

        for mv in session.movements:
            lid = mv.lift_id
            if not lid:
                continue

            # e1RM series
            if lid in featured:
                e = best_e1rm_for_session(mv)
                if e is not None:
                    # Find the top set that produced it
                    top = None
                    for s in mv.sets:
                        if s.load_lb is None or s.reps is None or s.reps > 10:
                            continue
                        if top is None or epley_e1rm(s.load_lb, s.reps) > epley_e1rm(top.load_lb, top.reps):  # type: ignore
                            top = s
                    e1rm_series[lid].append(
                        {
                            "date": session.date,
                            "e1rm": round(e, 1),
                            "top_load_lb": top.load_lb if top else None,
                            "top_reps": top.reps if top else None,
                            "added_lb": top.added_lb if top else None,
                        }
                    )

            # Zoom: list every set for zoom lifts
            if lid in zoom:
                for s in mv.sets:
                    if s.load_lb is None or s.reps is None:
                        continue
                    zoom_working_sets[lid].append(
                        {
                            "date": session.date,
                            "load_lb": s.load_lb,
                            "reps": s.reps,
                            "e1rm": round(epley_e1rm(s.load_lb, s.reps), 1) if s.reps <= 12 else None,
                        }
                    )

            # Weekly volume
            bucket = lift_to_bucket.get(lid)
            if bucket:
                vol = session_volume_lb(mv)
                if vol > 0:
                    week_start = iso_week_start(sdate)
                    if week_start not in weekly_volume:
                        weekly_volume[week_start] = {}
                    weekly_volume[week_start][bucket] = (
                        weekly_volume[week_start].get(bucket, 0.0) + vol
                    )

            # Recent PRs
            if sdate >= pr_window_start and lid in featured:
                e = best_e1rm_for_session(mv)
                if e is not None:
                    if lid not in recent_prs or e > recent_prs[lid]["e1rm"]:
                        # Find top set details
                        top = max(
                            (s for s in mv.sets if s.load_lb and s.reps and s.reps <= 12),
                            key=lambda s: epley_e1rm(s.load_lb, s.reps),  # type: ignore
                            default=None,
                        )
                        recent_prs[lid] = {
                            "lift_id": lid,
                            "lift_name": display_names.get(lid, lid),
                            "e1rm": round(e, 1),
                            "date": session.date,
                            "top_load_lb": top.load_lb if top else None,
                            "top_reps": top.reps if top else None,
                            "added_lb": top.added_lb if top else None,
                        }

    # Format weekly volume as sorted array
    weekly_volume_arr = []
    for week in sorted(weekly_volume.keys()):
        entry = {"week_start": week}
        for bucket in pattern_buckets.keys():
            entry[bucket] = round(weekly_volume[week].get(bucket, 0.0), 0)
        weekly_volume_arr.append(entry)

    return {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "bodyweight_lb": config["bodyweight_lb"],
        "featured_lifts": featured,
        "zoom_lifts": zoom,
        "lift_display_names": display_names,
        "pattern_display_names": pattern_names,
        "pattern_buckets": list(pattern_buckets.keys()),
        "e1rm_series": {
            lid: e1rm_series[lid] for lid in featured
        },
        "zoom_sets": zoom_working_sets,
        "weekly_volume": weekly_volume_arr,
        "recent_prs": list(recent_prs.values()),
        "sessions": [
            {
                "date": s.date,
                "type": s.type,
                "movement_count": len(s.movements),
            }
            for s in sessions
        ],
    }


def main():
    data = build_dashboard_data()
    out_path = Path(__file__).resolve().parent / "data.json"
    out_path.write_text(json.dumps(data, indent=2, default=str))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
