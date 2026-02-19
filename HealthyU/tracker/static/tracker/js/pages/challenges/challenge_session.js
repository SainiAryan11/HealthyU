(function () {
  const exName = document.getElementById("exName");
  const exDesc = document.getElementById("exDesc");
  const stepsGrid = document.getElementById("stepsGrid");
  const progressText = document.getElementById("progressText");
  const rewardPoints = document.getElementById("rewardPoints");

  const finishBtn = document.getElementById("finishBtn");
  const endBtn = document.getElementById("endBtn");

  function safeText(v) {
    if (v === null || v === undefined) return "";
    return String(v);
  }

  function render() {
    exName.innerText = safeText(CHALLENGE.name || "Challenge");
    exDesc.innerText = safeText(CHALLENGE.description || "");

    rewardPoints.innerText = safeText(CHALLENGE.reward ?? 50);

    const steps = Array.isArray(CHALLENGE.steps) ? CHALLENGE.steps : [];
    stepsGrid.innerHTML = "";

    if (!steps.length) {
      const div = document.createElement("div");
      div.className = "step-box";
      div.innerHTML = `
        <div class="step-num">1</div>
        <div class="step-text">Follow proper form and complete the exercise safely.</div>
      `;
      stepsGrid.appendChild(div);
      progressText.innerText = "0%";
      return;
    }

    steps.forEach((s, idx) => {
      const box = document.createElement("div");
      box.className = "step-box";
      box.innerHTML = `
        <div class="step-num">${idx + 1}</div>
        <div class="step-text">${safeText(s)}</div>
      `;
      stepsGrid.appendChild(box);
    });

    progressText.innerText = "0%";
  }

  finishBtn.addEventListener("click", () => {
    // Logged-in users: complete + reward.
    // Guests: will be redirected to login because COMPLETE_URL hits login_required view.
    window.location.href = COMPLETE_URL;
  });

  endBtn.addEventListener("click", () => {
    window.location.href = END_URL;
  });

  render();
})();
