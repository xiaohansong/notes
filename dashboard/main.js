// Strength dashboard — fetches data.json and renders charts.

const COLORS = {
  back_squat: "#f78166",
  strict_press: "#58a6ff",
  bench_press: "#d29922",
  weighted_pullup: "#a371f7",
  barbell_row: "#3fb950",
  rdl: "#db61a2",
};

const PATTERN_COLORS = {
  squat: "#f78166",
  hinge: "#d29922",
  vertical_push: "#58a6ff",
  horizontal_push: "#79c0ff",
  vertical_pull: "#a371f7",
  horizontal_pull: "#bc8cff",
  carry: "#3fb950",
};

function fmtDate(iso) {
  const [y, m, d] = iso.split("-");
  return `${m}/${d}`;
}

function fmtDateLong(iso) {
  const [y, m, d] = iso.split("-");
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[parseInt(m,10)-1]} ${parseInt(d,10)}`;
}

function setHeader(data) {
  const gen = new Date(data.generated_at);
  document.getElementById("generated").textContent =
    `updated ${gen.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}`;
  document.getElementById("bodyweight").textContent = `BW ${data.bodyweight_lb}#`;
}

function renderFeaturedCards(data) {
  const grid = document.getElementById("featured-grid");
  grid.innerHTML = "";
  for (const lid of data.featured_lifts) {
    const series = data.e1rm_series[lid] || [];
    const name = data.lift_display_names[lid] || lid;
    const card = document.createElement("div");
    card.className = "featured-card";

    if (series.length === 0) {
      card.innerHTML = `
        <div class="lift-name">${name}</div>
        <div class="e1rm">—</div>
        <div class="top-set">no sessions yet</div>
      `;
      grid.appendChild(card);
      continue;
    }

    const latest = series[series.length - 1];
    const prev = series.length > 1 ? series[series.length - 2] : null;
    let delta = "";
    if (prev) {
      const d = latest.e1rm - prev.e1rm;
      const cls = d > 0.5 ? "up" : d < -0.5 ? "down" : "flat";
      const sign = d > 0 ? "+" : "";
      delta = `<div class="delta ${cls}">${sign}${d.toFixed(1)}# vs ${fmtDateLong(prev.date)}</div>`;
    }

    let topLine = `${latest.top_load_lb}# × ${latest.top_reps}`;
    if (latest.added_lb !== null && latest.added_lb !== undefined) {
      topLine = `BW+${latest.added_lb}# × ${latest.top_reps} (system ${latest.top_load_lb}#)`;
    }

    card.innerHTML = `
      <div class="lift-name">${name}</div>
      <div class="e1rm">${latest.e1rm.toFixed(0)}<span class="unit">lb e1RM</span></div>
      <div class="top-set">top set ${topLine} · ${fmtDateLong(latest.date)}</div>
      ${delta}
    `;
    grid.appendChild(card);
  }
}

function renderE1rmAll(data) {
  const ctx = document.getElementById("chart-e1rm-all").getContext("2d");
  const datasets = data.featured_lifts.map((lid) => {
    const series = data.e1rm_series[lid] || [];
    return {
      label: data.lift_display_names[lid] || lid,
      data: series.map((p) => ({ x: p.date, y: p.e1rm })),
      borderColor: COLORS[lid] || "#888",
      backgroundColor: COLORS[lid] || "#888",
      tension: 0.25,
      pointRadius: 4,
      pointHoverRadius: 6,
      borderWidth: 2,
      spanGaps: true,
    };
  });

  new Chart(ctx, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "nearest", intersect: false },
      plugins: {
        legend: { labels: { color: "#e6edf3", boxWidth: 12, padding: 14 } },
        tooltip: {
          callbacks: {
            title: (items) => fmtDateLong(items[0].parsed.x ? new Date(items[0].parsed.x).toISOString().slice(0,10) : items[0].label),
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}# e1RM`,
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: { unit: "day", tooltipFormat: "MMM d", displayFormats: { day: "MMM d" } },
          grid: { color: "#23282f" },
          ticks: { color: "#8b949e" },
        },
        y: {
          title: { display: true, text: "Estimated 1RM (lb)", color: "#8b949e" },
          grid: { color: "#23282f" },
          ticks: { color: "#8b949e" },
        },
      },
    },
  });
}

function renderZoomLift(canvasId, data, lid) {
  const sets = data.zoom_sets[lid] || [];
  if (sets.length === 0) {
    const ctx = document.getElementById(canvasId).getContext("2d");
    ctx.fillStyle = "#8b949e";
    ctx.font = "13px system-ui";
    ctx.fillText("no sets yet", 12, 20);
    return;
  }

  // Group by rep count for color/legend
  const byReps = new Map();
  for (const s of sets) {
    if (!byReps.has(s.reps)) byReps.set(s.reps, []);
    byReps.get(s.reps).push(s);
  }
  // Sort rep groups ascending so the legend reads 1, 2, 3, ...
  const repGroups = [...byReps.keys()].sort((a, b) => a - b);

  const palette = ["#f78166", "#d29922", "#3fb950", "#58a6ff", "#a371f7", "#db61a2", "#79c0ff", "#bc8cff"];
  const datasets = repGroups.map((reps, i) => ({
    label: `${reps} rep${reps === 1 ? "" : "s"}`,
    data: byReps.get(reps).map((s) => ({ x: s.date, y: s.load_lb, e1rm: s.e1rm, reps: s.reps })),
    borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length],
    pointRadius: 5,
    pointHoverRadius: 7,
    showLine: false,
  }));

  const ctx = document.getElementById(canvasId).getContext("2d");
  new Chart(ctx, {
    type: "scatter",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#e6edf3", boxWidth: 12, padding: 14 } },
        tooltip: {
          callbacks: {
            title: (items) => fmtDateLong(new Date(items[0].parsed.x).toISOString().slice(0,10)),
            label: (ctx) => {
              const r = ctx.raw;
              const e1 = r.e1rm !== null && r.e1rm !== undefined ? ` (e1RM ${r.e1rm}#)` : "";
              return `${r.y}# × ${r.reps}${e1}`;
            },
          },
        },
      },
      scales: {
        x: {
          type: "time",
          time: { unit: "day", tooltipFormat: "MMM d", displayFormats: { day: "MMM d" } },
          grid: { color: "#23282f" },
          ticks: { color: "#8b949e" },
        },
        y: {
          title: { display: true, text: "Working set load (lb)", color: "#8b949e" },
          grid: { color: "#23282f" },
          ticks: { color: "#8b949e" },
        },
      },
    },
  });
}

function renderVolume(data) {
  const weeks = data.weekly_volume;
  if (weeks.length === 0) return;

  const labels = weeks.map((w) => fmtDateLong(w.week_start));
  const datasets = data.pattern_buckets.map((bucket) => ({
    label: data.pattern_display_names[bucket] || bucket,
    data: weeks.map((w) => w[bucket] || 0),
    backgroundColor: PATTERN_COLORS[bucket] || "#888",
    borderWidth: 0,
  }));

  const ctx = document.getElementById("chart-volume").getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#e6edf3", boxWidth: 12, padding: 14 } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toLocaleString()} lb`,
          },
        },
      },
      scales: {
        x: {
          stacked: true,
          grid: { color: "#23282f" },
          ticks: { color: "#8b949e" },
        },
        y: {
          stacked: true,
          title: { display: true, text: "Volume (load × reps, lb)", color: "#8b949e" },
          grid: { color: "#23282f" },
          ticks: { color: "#8b949e" },
        },
      },
    },
  });
}

function renderPRs(data) {
  const container = document.getElementById("prs-table");
  if (!data.recent_prs || data.recent_prs.length === 0) {
    container.innerHTML = `<div class="empty">No PRs in the last 8 weeks.</div>`;
    return;
  }
  const rows = [...data.recent_prs].sort((a, b) => b.e1rm - a.e1rm);
  const html = `
    <table>
      <thead>
        <tr>
          <th>Lift</th>
          <th>Top set</th>
          <th>e1RM</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map((r) => {
          let topSet;
          if (r.added_lb !== null && r.added_lb !== undefined) {
            topSet = `BW+${r.added_lb}# × ${r.top_reps} (system ${r.top_load_lb}#)`;
          } else {
            topSet = `${r.top_load_lb}# × ${r.top_reps}`;
          }
          return `
            <tr>
              <td>${r.lift_name}</td>
              <td>${topSet}</td>
              <td>${r.e1rm.toFixed(1)}#</td>
              <td>${fmtDateLong(r.date)}</td>
            </tr>
          `;
        }).join("")}
      </tbody>
    </table>
  `;
  container.innerHTML = html;
}

async function main() {
  const res = await fetch(`data.json?t=${Date.now()}`);
  const data = await res.json();
  setHeader(data);
  renderFeaturedCards(data);
  renderE1rmAll(data);
  renderZoomLift("chart-zoom-squat", data, "back_squat");
  renderZoomLift("chart-zoom-ohp", data, "strict_press");
  renderVolume(data);
  renderPRs(data);
}

main().catch((err) => {
  console.error(err);
  document.body.innerHTML = `<pre style="color:#f78166;padding:24px">Failed to load data.json:\n${err.message}\n\nRun: python3 dashboard/parse.py</pre>`;
});
