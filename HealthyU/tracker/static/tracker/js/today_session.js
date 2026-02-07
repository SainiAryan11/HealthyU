let currentIndex = 0;
let completed = 0;
let skipped = 0;

const total = exercises.length;

const nameEl = document.getElementById("exerciseName");
const catEl = document.getElementById("exerciseCategory");
const valueEl = document.getElementById("exerciseValue");
const progressEl = document.getElementById("progressText");

function renderExercise() {
    const ex = exercises[currentIndex];

    nameEl.innerText = ex.name;
    catEl.innerText = ex.category;

    if (ex.unit === "freq") {
        valueEl.innerText = `Do ${ex.value} times`;
    } else {
        valueEl.innerText = `For ${ex.value} minutes`;
    }

    updateProgress();
}

function updateProgress() {
    const progress = Math.floor((completed / total) * 50);
    progressEl.innerText = `${progress}%`;
}

document.getElementById("nextBtn").onclick = () => {
    completed++;
    currentIndex++;

    if (currentIndex >= total) {
        alert("Physical exercises completed!");
        window.location.href = "/profile/";
        return;
    }

    renderExercise();
};

document.getElementById("skipBtn").onclick = () => {
    skipped++;
    currentIndex++;

    if (currentIndex >= total) {
        alert("Physical exercises completed!");
        window.location.href = "/profile/";
        return;
    }

    renderExercise();
};

document.getElementById("endBtn").onclick = () => {
    if (confirm("Do you want to end the session?")) {
        window.location.href = "/profile/";
    }
};

renderExercise();
