// tracker/static/tracker/js/create_plan.js

let selectedPlan = []; // { key, name, category, value, unit, min, max }

document.addEventListener("DOMContentLoaded", () => {

  // ---------- View Details (delegation: works for all cards incl. extras) ----------
  document.addEventListener("click", (e) => {
    if (!e.target.classList.contains("view-details")) return;

    const card = e.target.closest(".exercise-card");
    if (!card) return;

    const details = card.querySelector(".exercise-details");
    if (details) details.classList.toggle("d-none");
  });

  // ---------- Plus/Minus (delegation, respects min/max, keeps selectedPlan synced) ----------
  document.addEventListener("click", (e) => {
    if (!e.target.classList.contains("plus") && !e.target.classList.contains("minus")) return;

    const card = e.target.closest(".exercise-card");
    if (!card) return;

    const input = card.querySelector(".time-input") || card.querySelector(".frequency-input");
    if (!input) return;

    const min = input.min ? parseInt(input.min) : 1;
    const max = input.max ? parseInt(input.max) : 999999;

    let val = parseInt(input.value || "0");
    val = e.target.classList.contains("plus") ? val + 1 : val - 1;

    if (val < min) val = min;
    if (val > max) val = max;

    input.value = val;

    // keep selectedPlan in sync if this card is already selected
    const name = (card.querySelector("h6")?.innerText || "").trim();
    const category = (card.querySelector("small")?.innerText || "").trim();
    const key = `${name}__${category}`;

    const idx = selectedPlan.findIndex(x => x.key === key);
    if (idx !== -1) selectedPlan[idx].value = val;
  });

  // ---------- Add/Remove toggle (delegation: works for all cards incl. extras) ----------
  document.addEventListener("click", (e) => {
    if (!e.target.classList.contains("add-btn")) return;

    const btn = e.target;
    const card = btn.closest(".exercise-card");
    if (!card) return;

    const name = (card.querySelector("h6")?.innerText || "").trim();
    const category = (card.querySelector("small")?.innerText || "").trim();
    const input = card.querySelector(".time-input") || card.querySelector(".frequency-input");

    const value = input ? parseInt(input.value || "0") : 0;
    const unit = card.querySelector(".time-input") ? "min" : "freq";

    const min = input?.min ? parseInt(input.min) : 1;
    const max = input?.max ? parseInt(input.max) : 999999;

    const key = `${name}__${category}`;
    const already = selectedPlan.findIndex(x => x.key === key);

    if (already === -1) {
      selectedPlan.push({ key, name, category, value, unit, min, max });
      btn.classList.remove("btn-success");
      btn.classList.add("btn-danger");
      btn.textContent = "Added";
    } else {
      selectedPlan.splice(already, 1);
      btn.classList.remove("btn-danger");
      btn.classList.add("btn-success");
      btn.textContent = "Add";
    }
  });

  // ---------- Reset ----------
  const resetBtn = document.getElementById("resetPlan");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      selectedPlan = [];

      document.querySelectorAll(".exercise-card").forEach(card => {
        const addBtn = card.querySelector(".add-btn");
        if (addBtn) {
          addBtn.classList.remove("btn-danger");
          addBtn.classList.add("btn-success");
          addBtn.textContent = "Add";
        }

        const input = card.querySelector(".time-input") || card.querySelector(".frequency-input");
        if (input) {
          const defaultVal = input.getAttribute("value");
          if (defaultVal !== null) input.value = defaultVal;
        }

        const details = card.querySelector(".exercise-details");
        if (details) details.classList.add("d-none");
      });
    });
  }

  // ---------- Save Plan -> Open Modal ----------
  const saveBtn = document.getElementById("savePlan");
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      renderModalPlan();
      const modal = new bootstrap.Modal(document.getElementById("planModal"));
      modal.show();
    });
  }

  // ---------- Confirm (save to backend) ----------
  const confirmBtn = document.getElementById("confirmPlanBtn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", async () => {
      if (selectedPlan.length === 0) {
        alert("No exercises selected!");
        return;
      }

      const payload = {
        items: selectedPlan.map(item => ({
          name: item.name,
          category: item.category, // MUST be: Physical Exercise / Yoga / Meditation
          value: item.value,
          unit: item.unit          // freq / min
        }))
      };

      try {
        const res = await fetch("/save-plan/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify(payload),
        });

        const data = await res.json();

        // close modal
        const modalEl = document.getElementById("planModal");
        bootstrap.Modal.getInstance(modalEl).hide();

        // show success message
        alert("✅ " + data.message);

        // redirect
        window.location.href = "/profile/";

      } catch (err) {
        alert("Error saving plan. Please try again.");
        console.error(err);
      }
    });
  }

  // ---------- View More / View Less ----------
  document.querySelectorAll(".view-more-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const levelSection = btn.closest(".level-section");
      if (!levelSection) return;

      const extra = levelSection.querySelector(".extra-exercises");
      if (!extra) return;

      extra.classList.toggle("d-none");
      btn.textContent = extra.classList.contains("d-none") ? "View More" : "View Less";
    });
  });

});


// ---------- Modal Render + Edit ----------
function renderModalPlan() {
  const list = document.getElementById("modalPlanList");
  const emptyMsg = document.getElementById("emptyModalMsg");

  list.innerHTML = "";

  if (selectedPlan.length === 0) {
    emptyMsg.classList.remove("d-none");
    return;
  }
  emptyMsg.classList.add("d-none");

  selectedPlan.forEach((item, i) => {
    const unitLabel = item.unit === "min" ? "min" : "freq";

    const row = document.createElement("div");
    row.className = "list-group-item";

    row.innerHTML = `
      <div class="d-flex justify-content-between align-items-start gap-3">
        <div class="flex-grow-1">
          <div class="fw-semibold">${item.name}</div>
          <div class="text-muted small">${item.category}</div>
        </div>

        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-outline-secondary btn-sm" data-action="mminus" data-index="${i}">−</button>

          <input type="number"
                 class="form-control form-control-sm"
                 style="width: 90px;"
                 value="${item.value}"
                 min="${item.min}"
                 max="${item.max}"
                 data-action="minput"
                 data-index="${i}" />

          <button class="btn btn-outline-secondary btn-sm" data-action="mplus" data-index="${i}">+</button>

          <span class="small text-muted">${unitLabel}</span>

          <button class="btn btn-outline-danger btn-sm" data-action="mremove" data-index="${i}">
            Remove
          </button>
        </div>
      </div>
    `;

    list.appendChild(row);
  });

  // modal events (delegation)
  list.onclick = (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;

    const action = btn.dataset.action;
    const idx = parseInt(btn.dataset.index);

    if (action === "mremove") {
      removeFromPlan(idx);
      return;
    }
    if (action === "mplus" || action === "mminus") {
      const delta = action === "mplus" ? 1 : -1;
      changeModalValue(idx, delta);
      return;
    }
  };

  list.oninput = (e) => {
    const input = e.target;
    if (input.dataset.action !== "minput") return;

    const idx = parseInt(input.dataset.index);

    const min = parseInt(input.min);
    const max = parseInt(input.max);
    let val = parseInt(input.value || min);

    if (val < min) val = min;
    if (val > max) val = max;
    input.value = val;

    selectedPlan[idx].value = val;
    syncCardInput(selectedPlan[idx]);
  };
}

function changeModalValue(idx, delta) {
  const item = selectedPlan[idx];
  let val = item.value + delta;

  if (val < item.min) val = item.min;
  if (val > item.max) val = item.max;

  item.value = val;
  renderModalPlan();
  syncCardInput(item);
}

function removeFromPlan(idx) {
  const item = selectedPlan[idx];
  selectedPlan.splice(idx, 1);

  // switch main page button back to "Add"
  const card = findCard(item.name, item.category);
  if (card) {
    const addBtn = card.querySelector(".add-btn");
    if (addBtn) {
      addBtn.classList.remove("btn-danger");
      addBtn.classList.add("btn-success");
      addBtn.textContent = "Add";
    }
  }

  renderModalPlan();
}

function syncCardInput(item) {
  const card = findCard(item.name, item.category);
  if (!card) return;

  const input = card.querySelector(".time-input") || card.querySelector(".frequency-input");
  if (input) input.value = item.value;
}

function findCard(name, category) {
  const cards = document.querySelectorAll(".exercise-card");
  for (const card of cards) {
    const n = (card.querySelector("h6")?.innerText || "").trim();
    const c = (card.querySelector("small")?.innerText || "").trim();
    if (n === name && c === category) return card;
  }
  return null;
}


// ---------- CSRF helper ----------
function getCookie(name) {
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
