// ==================== MOTIVATIONAL QUOTES ====================
const quotes = [
    { text: "The only bad workout is the one that didn't happen.", author: "Unknown" },
    { text: "Your body can stand almost anything. It's your mind you have to convince.", author: "Unknown" },
    { text: "Take care of your body. It's the only place you have to live.", author: "Jim Rohn" },
    { text: "Fitness is not about being better than someone else. It's about being better than you used to be.", author: "Khloe Kardashian" },
    { text: "The groundwork for all happiness is good health.", author: "Leigh Hunt" },
    { text: "A healthy outside starts from the inside.", author: "Robert Urich" },
    { text: "Success is the sum of small efforts repeated day in and day out.", author: "Robert Collier" },
    { text: "Don't wish for it, work for it.", author: "Unknown" },
    { text: "The difference between try and triumph is a little umph.", author: "Unknown" },
    { text: "Strive for progress, not perfection.", author: "Unknown" }
];

// Display random quote
function displayRandomQuote() {
    const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
    const quoteText = document.getElementById('motivationalQuote');
    const quoteAuthor = document.getElementById('quoteAuthor');

    if (quoteText && quoteAuthor) {
        quoteText.textContent = `"${randomQuote.text}"`;
        quoteAuthor.textContent = `— ${randomQuote.author}`;
    }
}

// ==================== WORKOUT CARD INTERACTIONS ====================
function initWorkoutCards() {
    const workoutCards = document.querySelectorAll('.workout-card');

    workoutCards.forEach(card => {
        card.addEventListener('click', function () {
            const workoutName = this.querySelector('.workout-name').textContent;
            showWorkoutInfo(workoutName);
        });
    });
}

function showWorkoutInfo(workoutName) {
    // Add animation effect
    const card = event.currentTarget;
    card.style.transform = 'scale(0.95)';
    setTimeout(() => {
        card.style.transform = '';
    }, 200);

    console.log(`Clicked on: ${workoutName}`);
    // You can add modal or redirect logic here
}

// ==================== EXERCISE CARD BUTTONS ====================
function initExerciseButtons() {
    const exerciseButtons = document.querySelectorAll('.btn-exercise');

    exerciseButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const exerciseName = this.closest('.exercise-card').querySelector('.exercise-name').textContent;
            showExerciseDetails(exerciseName);
        });
    });
}

function showExerciseDetails(exerciseName) {
    // Add ripple effect
    const button = event.currentTarget;
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
        button.style.transform = '';
    }, 200);

    console.log(`View details for: ${exerciseName}`);
    // You can add modal or redirect logic here
}

// ==================== CHALLENGE BUTTON ====================
function initChallengeButton() {
    const challengeBtn = document.querySelector('.btn-challenge');

    if (challengeBtn) {
        challengeBtn.addEventListener('click', function () {
            acceptChallenge();
        });
    }
}

function acceptChallenge() {
    const button = event.currentTarget;
    const originalText = button.textContent;

    // Visual feedback
    button.textContent = 'Challenge Accepted! 🎉';
    button.style.background = '#38ef7d';
    button.style.color = 'white';

    setTimeout(() => {
        button.textContent = originalText;
        button.style.background = '';
        button.style.color = '';
    }, 2000);

    console.log('Challenge accepted!');
    // You can add logic to save challenge acceptance
}

// ==================== YOGA SESSION BUTTONS ====================
function initYogaButtons() {
    const yogaButtons = document.querySelectorAll('.btn-yoga');

    yogaButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.stopPropagation();
            const yogaName = this.closest('.yoga-card').querySelector('.yoga-name').textContent;
            startYogaSession(yogaName);
        });
    });
}

function startYogaSession(yogaName) {
    console.log(`Starting yoga session: ${yogaName}`);
    // You can add redirect or modal logic here
}

// ==================== SCROLL ANIMATIONS ====================
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all sections
    const sections = document.querySelectorAll('.workout-section, .challenge-section, .quote-section');
    sections.forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(section);
    });
}

// ==================== PROGRESS BAR ANIMATION ====================
function animateProgressBar() {
    const progressFill = document.querySelector('.progress-fill');

    if (progressFill) {
        const targetWidth = progressFill.style.width;
        progressFill.style.width = '0%';

        setTimeout(() => {
            progressFill.style.width = targetWidth;
        }, 500);
    }
}

// ==================== STAT CARDS COUNTER ANIMATION ====================
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

// ==================== HOVER EFFECTS ====================
function initHoverEffects() {
    // Add subtle tilt effect on workout cards
    const cards = document.querySelectorAll('.workout-card, .exercise-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transition = 'all 0.3s ease';
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = '';
        });
    });
}

// ==================== INITIALIZE ALL FEATURES ====================
document.addEventListener('DOMContentLoaded', function () {
    // Display random motivational quote
    displayRandomQuote();

    // Initialize interactive elements
    initWorkoutCards();
    initExerciseButtons();
    initChallengeButton();
    initYogaButtons();

    // Initialize animations
    initScrollAnimations();
    animateProgressBar();
    animateStatCounters();
    initHoverEffects();

    console.log('HealthyU Home Page Initialized! 💪');
});

// ==================== UTILITY FUNCTIONS ====================
// Refresh quote every 30 seconds
setInterval(displayRandomQuote, 30000);

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});
