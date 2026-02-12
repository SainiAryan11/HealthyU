async function loadProgress() {
  const res = await fetch(PROGRESS_DATA_URL, { headers: { "Accept": "application/json" } });
  const data = await res.json();

  // Daily (30 days): line chart progress + points (2 traces)
  Plotly.newPlot("dailyChart", [
    {
      x: data.daily.labels,
      y: data.daily.progress,
      type: "scatter",
      mode: "lines+markers",
      name: "Progress (%)",
    },
    {
      x: data.daily.labels,
      y: data.daily.points,
      type: "scatter",
      mode: "lines+markers",
      name: "Points",
    }
  ], {
    margin: { t: 10, l: 40, r: 10, b: 40 },
    yaxis: { range: [0, 100], title: "" },
    xaxis: { title: "" },
    legend: { orientation: "h" }
  }, { responsive: true });

  // Weekly: bar chart avg progress
  Plotly.newPlot("weeklyChart", [
    {
      x: data.weekly.labels,
      y: data.weekly.avg_progress,
      type: "bar",
      name: "Avg Progress (%)",
    }
  ], {
    margin: { t: 10, l: 40, r: 10, b: 40 },
    yaxis: { range: [0, 100] },
  }, { responsive: true });

  // Monthly: bar chart avg progress
  Plotly.newPlot("monthlyChart", [
    {
      x: data.monthly.labels,
      y: data.monthly.avg_progress,
      type: "bar",
      name: "Avg Progress (%)",
    }
  ], {
    margin: { t: 10, l: 40, r: 10, b: 40 },
    yaxis: { range: [0, 100] },
  }, { responsive: true });
}

document.addEventListener("DOMContentLoaded", loadProgress);
