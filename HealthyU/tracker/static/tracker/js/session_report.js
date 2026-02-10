function getCookie(name){
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function badge(status){
  if(status === "completed") return `<span class="badge bg-success">Completed</span>`;
  if(status === "partial") return `<span class="badge bg-info">Partial</span>`;
  if(status === "skipped") return `<span class="badge bg-warning text-dark">Skipped</span>`;
  return `<span class="badge bg-secondary">Pending</span>`;
}

function addItems(containerId, items){
  const box = document.getElementById(containerId);
  box.innerHTML = "";

  if(!items || items.length === 0){
    box.innerHTML = `<div class="text-muted">No items</div>`;
    return;
  }

  items.forEach(it => {
    const valueText = it.unit === "min" ? `${it.value} min` : `${it.value}x`;
    const row = document.createElement("div");
    row.className = "list-group-item d-flex justify-content-between align-items-center";
    row.innerHTML = `
      <div>
        <div class="fw-semibold">${it.name}</div>
        <small class="text-muted">${valueText}</small>
      </div>
      ${badge(it.status)}
    `;
    box.appendChild(row);
  });
}

// ------------------ LOAD REPORT ------------------
const raw = sessionStorage.getItem("sessionReport");
let report = null;

if(!raw){
  document.getElementById("progressPct").innerText = "0%";
  document.getElementById("saveSessionBtn").disabled = true;
} else {
  try {
    report = JSON.parse(raw);
  } catch(e) {
    report = null;
    document.getElementById("progressPct").innerText = "0%";
    document.getElementById("saveSessionBtn").disabled = true;
  }
}

if(report){
  // HARD CAPS
  const cappedProgress = Math.min(parseInt(report.progress || 0), 100);
  const cappedPoints   = Math.min(parseInt(report.points || 0), 100);
  const cappedTime     = Math.max(parseInt(report.time_minutes || 0), 0);

  // DISPLAY
  document.getElementById("progressPct").innerText = cappedProgress + "%";
  document.getElementById("pointsEarned").innerText = cappedPoints;
  document.getElementById("timeTaken").innerText = cappedTime + " min";

  // Handle meditation data
  document.getElementById("medPlanned").innerText = report.meditation_planned_total || 0;
  
  const completedMedCount = report.meditation_completed_count || 0;
  const totalMedCount = report.meditation_total_count || 0;
  document.getElementById("medSpent").innerText = completedMedCount + " of " + totalMedCount;
  
  document.getElementById("medStatusBadge").innerHTML =
    badge(report.meditation_status || "skipped");

  addItems("physicalList", report.physical || []);
  addItems("yogaList", report.yoga || []);
  addItems("meditationList", report.meditation || []);
}

// ------------------ SAVE SESSION ------------------
document.getElementById("saveSessionBtn").onclick = async () => {
  if(!report){
    alert("No report found to save.");
    return;
  }

  try {
    const res = await fetch("/submit-session/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      },
      body: JSON.stringify({
        points: Math.min(parseInt(report.points || 0), 100),
        report: report
      })
    });

    const data = await res.json().catch(() => ({}));

    if(!res.ok){
      alert(data.message || "Unable to save session.");
      return;
    }

    // ✅ show backend message (includes streak info)
    alert(data.message || "Saved!");

    // ✅ disable save button so user cannot spam
    document.getElementById("saveSessionBtn").disabled = true;

    // ✅ optional: redirect to profile after ok
    window.location.href = "/profile/";

  } catch(err){
    console.error(err);
    alert("Network/JS error saving session.");
  }
};

// ---- DELETE SESSION ----
document.getElementById("deleteSessionBtn").onclick = async () => {
  if(!confirm("Are you sure you want to delete this session? Points will be removed.")) {
    return;
  }

  try {
    const res = await fetch("/delete-session/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken")
      }
    });

    const data = await res.json().catch(() => ({}));

    if(!res.ok){
      alert(data.message || "Error deleting session.");
      return;
    }

    alert("Session deleted successfully!");
    sessionStorage.removeItem("sessionReport");
    window.location.href = "/profile/";

  } catch(err){
    console.error(err);
    alert("Network/JS error deleting session.");
  }
};


