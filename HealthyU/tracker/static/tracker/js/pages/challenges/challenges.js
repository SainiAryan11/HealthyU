// ==================== CHALLENGES PAGE FUNCTIONALITY ====================

document.addEventListener('DOMContentLoaded', function () {
    // Animate challenge cards on load
    animateChallengeCards();

    // Add click handlers to challenge buttons
    initChallengeButtons();

    // Animate stats counters
    animateStatCounters();
});

function animateChallengeCards() {
    const cards = document.querySelectorAll('.challenge-card');

    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';

        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initChallengeButtons() {
    const challengeButtons = document.querySelectorAll('.challenge-btn:not(.completed-btn)');

    challengeButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            // Add visual feedback
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 200);
        });
    });
}

function animateStatCounters() {
    const statValues = document.querySelectorAll('.stat-value');

    statValues.forEach(stat => {
        const target = parseInt(stat.textContent) || 0;
        const duration = 1500;
        const increment = target / (duration / 16);
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                stat.textContent = target;
                clearInterval(timer);
            } else {
                stat.textContent = Math.floor(current);
            }
        }, 16);
    });
}


function celebrateCompletion() {
    // You can add a confetti library here for celebration effect
    console.log('Challenge completed! 🎉');
}
