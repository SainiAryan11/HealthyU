console.log("today_session.js loaded", Date.now());

// -------------------- DOM --------------------
const exName = document.getElementById("exName");
const exDesc = document.getElementById("exDesc");
const phaseText = document.getElementById("phaseText");
const stepsGrid = document.getElementById("stepsGrid");
const progressText = document.getElementById("progressText");

const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const skipBtn = document.getElementById("skipBtn");
const endBtn  = document.getElementById("endBtn");
const doBtn   = document.getElementById("doBtn");

// modal
const phaseModal = document.getElementById("phaseModal");
const modalTitle = document.getElementById("modalTitle");
const modalText  = document.getElementById("modalText");
const modalSubText = document.getElementById("modalSubText");
const modalBackBtn = document.getElementById("modalBackBtn");
const modalEndBtn  = document.getElementById("modalEndBtn");
const modalNextPhaseBtn = document.getElementById("modalNextPhaseBtn");
const modalFinishBtn = document.getElementById("modalFinishBtn");

let totalMedSpentSec = 0;
let totalMedPlannedSec = 0;     


// -------------------- SESSION STATE --------------------
const activeCategories = [];
if (Array.isArray(PHYSICAL) && PHYSICAL.length) activeCategories.push("physical");
if (Array.isArray(YOGA) && YOGA.length) activeCategories.push("yoga");
if (Array.isArray(MEDITATION_LIST) && MEDITATION_LIST.length) activeCategories.push("meditation");

const CATEGORY_WEIGHT = 100 / (activeCategories.length || 1);
const CATEGORY_POINTS = 100 / (activeCategories.length || 1);

// ✅ phase order only includes real phases
const phaseOrder = activeCategories.slice();
let phaseIndex = 0;
let phase = phaseOrder[phaseIndex] || "physical";

let i = 0;

// ✅ Session start time tracking
const sessionStartTime = Date.now();

// counters (derived from status arrays)
let completedPhysical = 0, skippedPhysical = 0;
let completedYoga = 0, skippedYoga = 0;

// Track status per exercise: "pending" | "completed" | "skipped"
const physicalStatus = new Array(PHYSICAL.length).fill("pending");
const yogaStatus = new Array(YOGA.length).fill("pending");
const meditationStatus = new Array(MEDITATION_LIST.length).fill("pending");

function recalcCounts() {
  completedPhysical = physicalStatus.filter(s => s === "completed").length;
  skippedPhysical   = physicalStatus.filter(s => s === "skipped").length;

  completedYoga = yogaStatus.filter(s => s === "completed").length;
  skippedYoga   = yogaStatus.filter(s => s === "skipped").length;
}

// meditation timer
let medList = []; // will hold meditation items during meditation phase
let medIndex = 0; // current meditation item
let medTotalSec = 0; // total seconds for current meditation
let medSpentSec = 0; // seconds spent on current meditation
let medTimer = null;

// skip limit (Physical + Yoga only)
const totalSkippable = (PHYSICAL.length || 0) + (YOGA.length || 0);
const maxSkips = Math.floor(totalSkippable * 0.25);


// -------------------- HELPERS --------------------

function getEffectiveMedSpentSec() {
  return totalMedSpentSec + (medTimer ? medSpentSec : 0);
}

function listForPhase(ph) {
  if (ph === "physical") return PHYSICAL;
  if (ph === "yoga") return YOGA;
  return [];
}

function getMeditationMinutes(m) {
  const raw =
    m?.value ??
    m?.minutes ??
    m?.time_minutes ??
    m?.duration ??
    m?.selected_minutes ??
    0;

  const n = parseInt(raw, 10);
  return Number.isFinite(n) && n > 0 ? n : 0;
}

if (Array.isArray(MEDITATION_LIST) && MEDITATION_LIST.length) {
  totalMedPlannedSec = MEDITATION_LIST.reduce((sum, m) => {
    const minutes = getMeditationMinutes(m);
    return sum + (minutes > 0 ? minutes * 60 : 0);
  }, 0);
} else {
  totalMedPlannedSec = 0;
}

console.log("TOTAL PLANNED:", totalMedPlannedSec);


function labelForPhase(ph) {
  if (ph === "physical") return "Physical";
  if (ph === "yoga") return "Yoga";
  return "Meditation";
}

function openModal(title, text, subText, showContinue, showFinish) {
  modalTitle.innerText = title;
  modalText.innerText = text;
  modalSubText.innerText = subText || "";

  modalNextPhaseBtn.style.display = showContinue ? "inline-block" : "none";
  modalFinishBtn.style.display = showFinish ? "inline-block" : "none";

  phaseModal.style.display = "flex";
}

function closeModal() {
  phaseModal.style.display = "none";
}

function updateProgress() {
  recalcCounts();

  const pTotal = PHYSICAL.length || 1;
  const yTotal = YOGA.length || 1;

  let pProg = 0, yProg = 0, mProg = 0;

  // Physical
  if (PHYSICAL.length) {
    pProg = (completedPhysical / pTotal) * CATEGORY_WEIGHT;
  }

  // Yoga
  if (YOGA.length) {
    yProg = (completedYoga / yTotal) * CATEGORY_WEIGHT;
  }

  // Meditation (time-based)
  if (MEDITATION_LIST.length && totalMedPlannedSec > 0) {
    const effectiveMedSpentSec =
      totalMedSpentSec + (medTimer ? medSpentSec : 0);

    const ratio = Math.min(effectiveMedSpentSec / totalMedPlannedSec, 1);

    mProg = ratio * CATEGORY_WEIGHT;
  }

  const totalRaw = pProg + yProg + mProg;
  const total = Math.min(totalRaw, 100);

  progressText.innerText = total.toFixed(1) + "%";
}


function renderExercise() {
  phaseText.innerText = `Phase: ${labelForPhase(phase)}`;

  // meditation phase
  if (phase === "meditation") {
    renderMeditation();
    return;
  }

  const list = listForPhase(phase);

  // ✅ if phase has no items, skip it automatically
  if (!list || list.length === 0) {
    gotoNextAvailablePhaseOrFinish();
    return;
  }

  // clamp
  if (i < 0) i = 0;
  if (i >= list.length) i = list.length - 1;

  const ex = list[i];

  exName.innerText = ex.name;
  exDesc.innerText = ex.description || "";

  doBtn.innerText = (ex.unit === "freq")
    ? `Do this exercise ${ex.value} times`
    : `Do this for ${ex.value} min`;

  stepsGrid.innerHTML = "";
  (ex.steps || []).forEach((s, idx) => {
    const div = document.createElement("div");
    div.className = "step-box";
    div.innerHTML = `<div class="step-number">${idx + 1}</div>${s}`;
    stepsGrid.appendChild(div);
  });

  prevBtn.disabled = false;
  nextBtn.disabled = false;
  skipBtn.disabled = false;

  updateProgress();
}

// ✅ skip missing phases, no useless modal
function gotoNextAvailablePhaseOrFinish() {
  let nextIdx = phaseIndex + 1;

  while (nextIdx < phaseOrder.length) {
    const candidate = phaseOrder[nextIdx];

    if (candidate === "meditation") {
      if (Array.isArray(MEDITATION_LIST) && MEDITATION_LIST.length) {
        phaseIndex = nextIdx;
        phase = candidate;
        i = 0;
        renderExercise();
        return;
      }
    } else {
      const list = listForPhase(candidate);
      if (list && list.length > 0) {
        phaseIndex = nextIdx;
        phase = candidate;
        i = 0;
        renderExercise();
        return;
      }
    }
    nextIdx++;
  }

  // no phases left -> end
  endSessionNow();
}

function endSessionNow() {
  // capture live time BEFORE clearing timer
  const effective = getEffectiveMedSpentSec();

  if (medTimer) {
    clearInterval(medTimer);
    medTimer = null;
  }

  // freeze totals so report always has correct value
  totalMedSpentSec = effective;
  medSpentSec = 0;

  updateProgress();
  saveReportAndGoToReport(); // don't pass progress anymore
}


// -------------------- BUTTONS --------------------
nextBtn.onclick = () => {
  if (phase === "meditation") return;

  const list = listForPhase(phase);

  // ✅ mark current as completed
  if (phase === "physical") physicalStatus[i] = "completed";
  if (phase === "yoga") yogaStatus[i] = "completed";
  updateProgress();

  i++;

  if (i >= list.length) {
    // phase finished -> show modal if something else remains, else finish
    const nextPhase = phaseOrder[phaseIndex + 1];

    const currentProgress = parseInt(progressText.innerText.replace("%", "")) || 0;

    if (nextPhase) {
      openModal(
        `${labelForPhase(phase)} Phase Completed 🎉`,
        `Current progress: ${currentProgress}%`,
        `Continue to next phase?`,
        true,
        false
      );
    } else {
      openModal(
        `Session Completed 🎉`,
        `Final progress: ${currentProgress}%`,
        `You can now view your session report.`,
        false,
        true
      );
    }
    return;
  }

  renderExercise();
};

skipBtn.onclick = () => {
  if (phase === "meditation") {
    if (!confirm("Do you want to skip this meditation?")) return;

    // ✅ Mark current meditation as skipped
    meditationStatus[medIndex] = "skipped";
    medIndex++;

    // ✅ Add spent seconds before clearing timer
    if (medTimer) {
      totalMedSpentSec += medSpentSec;
      clearInterval(medTimer);
      medTimer = null;
    }

    // ✅ Spec: report must appear when meditation is skipped
    endSessionNow();
    return;
  }


  // ✅ skip limit based on status arrays (accurate even after Previous)
  recalcCounts();
  const currentSkipped = skippedPhysical + skippedYoga;

  if (totalSkippable > 0 && currentSkipped >= maxSkips) {
    alert(`Skip limit reached! You can skip at most ${maxSkips} exercises (Physical + Yoga combined).`);
    return;
  }

  const list = listForPhase(phase);

  // ✅ mark current as skipped
  if (phase === "physical") physicalStatus[i] = "skipped";
  if (phase === "yoga") yogaStatus[i] = "skipped";
  updateProgress();

  i++;

  if (i >= list.length) {
    const nextPhase = phaseOrder[phaseIndex + 1];
    const currentProgress = parseInt(progressText.innerText.replace("%", "")) || 0;

    if (nextPhase) {
      openModal(
        `${labelForPhase(phase)} Phase Completed 🎉`,
        `Current progress: ${currentProgress}%`,
        `Continue to next phase?`,
        true,
        false
      );
    } else {
      openModal(
        `Session Completed 🎉`,
        `Final progress: ${currentProgress}%`,
        `You can now view your session report.`,
        false,
        true
      );
    }
    return;
  }

  renderExercise();
};

prevBtn.onclick = () => {
  if (phase === "meditation") return;

  if (i > 0) {
    i--;
    renderExercise();
  } else {
    if (confirm("You are on the first exercise. Do you want to end the session?")) {
      endSessionNow();
    }
  }
};

endBtn.onclick = () => {
  if (confirm("Do you want to end the session now?")) {
    endSessionNow();
  }
};


// -------------------- MODAL BUTTONS --------------------
modalBackBtn.onclick = () => closeModal();

modalEndBtn.onclick = () => {
  closeModal();
  endSessionNow();
};

modalNextPhaseBtn.onclick = () => {
  closeModal();
  // move to next phase, but skip missing ones
  gotoNextAvailablePhaseOrFinish();
};

modalFinishBtn.onclick = () => {
  closeModal();
  endSessionNow();
};


// -------------------- MEDITATION --------------------
function renderMeditation() {
  // ✅ rely only on list length (HAS_MEDITATION can be wrong)
  if (!MEDITATION_LIST || MEDITATION_LIST.length === 0) {
    endSessionNow();
    return;
  }

  // Set up meditation list if not already done
  if (medList.length === 0) {
    medList = MEDITATION_LIST;
    medIndex = 0;
  }

  // Clamp index
  if (medIndex < 0) medIndex = 0;
  if (medIndex >= medList.length) {
    // All meditations done, move to next phase
    gotoNextAvailablePhaseOrFinish();
    return;
  }

  const currentMed = medList[medIndex];

  exName.innerText = currentMed.name;
  exDesc.innerText = currentMed.description || "";

  doBtn.innerText = `Meditate for ${getMeditationMinutes(currentMed)} min`;

  stepsGrid.innerHTML = "";
  (currentMed.steps || []).forEach((s, idx) => {
    const div = document.createElement("div");
    div.className = "step-box";
    div.innerHTML = `<div class="step-number">${idx + 1}</div>${s}`;
    stepsGrid.appendChild(div);
  });

  const plannedMinutes = getMeditationMinutes(currentMed);
  const timerRow = document.createElement("div");
  
  timerRow.className = "step-box";
  timerRow.style.gridColumn = "span 5";
  timerRow.innerHTML = `
    <div class="step-number" id="medTimerCountdown">Starting...</div>
    <div><strong>Planned:</strong> ${plannedMinutes} minutes</div>
    <div class="small-note mb-0" id="medProgress">Meditation ${medIndex + 1} of ${medList.length}</div>
    <div class="text-muted small">Next is disabled during meditation.</div>
  `;
  stepsGrid.appendChild(timerRow);

  nextBtn.disabled = true;
  prevBtn.disabled = true;

  if (plannedMinutes <= 0) {
    alert("Meditation minutes not set in your plan.");
    meditationStatus[medIndex] = "skipped";
    medIndex++;
    gotoNextAvailablePhaseOrFinish();
    return;
  }

  // ✅ IMPORTANT: only reset/start timer if it isn't already running
  if (!medTimer) {
    medSpentSec = 0;
    medTotalSec = plannedMinutes * 60;
    startMeditationTimer();
  }

  updateProgress();
}

function startMeditationTimer() {
  if (medTimer) return;

  let timerEl = document.getElementById("medTimerCountdown");
  if (!timerEl) return;

  medTimer = setInterval(() => {
    medSpentSec++;

    const remaining = Math.max(medTotalSec - medSpentSec, 0);
    const mm = String(Math.floor(remaining / 60)).padStart(2, "0");
    const ss = String(remaining % 60).padStart(2, "0");
    timerEl.innerText = `${mm}:${ss} remaining`;

    updateProgress();

    if (medSpentSec >= medTotalSec) {
      clearInterval(medTimer);
      medTimer = null;

      // ✅ add full spent time for this meditation item
      totalMedSpentSec += medSpentSec;

      // ✅ Mark current meditation as completed
      meditationStatus[medIndex] = "completed";
      medIndex++;

      if (medIndex < medList.length) {
        renderMeditation();
      } else {
        // ✅ spec: report must appear when meditation completes
        endSessionNow();
      }
    }
  }, 1000);
}


// -------------------- REPORT GENERATION --------------------
function saveReportAndGoToReport() {
  // final frozen meditation seconds
  const effectiveMedSpentSec = totalMedSpentSec;

  // elapsed time
  const elapsedMinutes = Math.round((Date.now() - sessionStartTime) / 60000);

  // ratios
  const physicalRatio = PHYSICAL.length ? (completedPhysical / PHYSICAL.length) : 0;
  const yogaRatio = YOGA.length ? (completedYoga / YOGA.length) : 0;
  const medRatio = totalMedPlannedSec > 0
    ? Math.min(effectiveMedSpentSec / totalMedPlannedSec, 1)
    : 0;

  // weighted progress
  const progress =
    (PHYSICAL.length ? physicalRatio * CATEGORY_WEIGHT : 0) +
    (YOGA.length ? yogaRatio * CATEGORY_WEIGHT : 0) +
    (MEDITATION_LIST.length ? medRatio * CATEGORY_WEIGHT : 0);

  const finalProgress = Math.min(progress, 100);

  // points follow same distribution
  const points =
    physicalRatio * CATEGORY_POINTS +
    yogaRatio * CATEGORY_POINTS +
    medRatio * CATEGORY_POINTS;

  const finalPoints = Math.min(Math.round(points), 100);

  // meditation minutes (IMPORTANT: keep decimal so 0.5 shows)
  const totalPlannedMin = (MEDITATION_LIST || []).reduce((sum, m) => sum + getMeditationMinutes(m), 0);
  const medSpentMin = totalMedPlannedSec > 0 ? +(effectiveMedSpentSec / 60).toFixed(1) : 0;

  let medStatus = "not_planned";
  if (MEDITATION_LIST.length) {
    medStatus = medRatio >= 1 ? "completed" : (medRatio > 0 ? "partial" : "skipped");
  }

  const report = {
    progress: +finalProgress.toFixed(1),
    points: finalPoints,
    time_minutes: elapsedMinutes,

    physical: PHYSICAL.map((x, idx) => ({
      name: x.name, value: x.value, unit: x.unit,
      status: physicalStatus[idx] || "pending",
    })),

    yoga: YOGA.map((x, idx) => ({
      name: x.name, value: x.value, unit: x.unit,
      status: yogaStatus[idx] || "pending",
    })),

    meditation_items: (MEDITATION_LIST || []).map((x, idx) => ({
      name: x.name, value: x.value, unit: x.unit,
      status: meditationStatus[idx] || "pending",
    })),

    meditation: {
      planned_minutes: totalPlannedMin,
      spent_minutes: medSpentMin,
      status: medStatus,
    },
  };

  sessionStorage.setItem("sessionReport", JSON.stringify(report));
  window.location.href = SESSION_REPORT_URL;
}

// ✅ Block navbar navigation during active session
document.querySelectorAll("a.session-nav-link").forEach(a => {
  const href = a.getAttribute("href");
  if (!href || href.startsWith("#") || href.startsWith("javascript:")) return;

  a.addEventListener("click", (e) => {
    e.preventDefault();

    const ok = confirm("A session is active. Do you want to end the session?");
    if (!ok) return;

    endSessionNow();
  });
});


// -------------------- INIT --------------------
renderExercise();
