// ==================== NAVBAR FUNCTIONALITY ====================

document.addEventListener('DOMContentLoaded', function () {
    // Mobile menu toggle
    const navbarToggle = document.getElementById('navbarToggle');
    const navbarLinks = document.getElementById('navbarLinks');

    if (navbarToggle) {
        navbarToggle.addEventListener('click', function () {
            this.classList.toggle('active');
            navbarLinks.classList.toggle('active');
        });
    }

    // Mobile dropdown toggle
    const navDropdowns = document.querySelectorAll('.nav-dropdown');

    if (window.innerWidth <= 992) {
        navDropdowns.forEach(dropdown => {
            const link = dropdown.querySelector('.nav-secondary-link');
            link.addEventListener('click', function (e) {
                e.preventDefault();
                dropdown.classList.toggle('active');
            });
        });
    }

    // Close mobile menu when clicking outside
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.navbar-custom')) {
            if (navbarToggle && navbarToggle.classList.contains('active')) {
                navbarToggle.classList.remove('active');
                navbarLinks.classList.remove('active');
            }
        }
    });

    // Highlight active page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link-custom, .nav-secondary-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.style.background = 'rgba(255, 255, 255, 0.3)';
            link.style.fontWeight = '700';
        }
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                document.querySelector(href).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Navbar scroll effect
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar-custom');

    window.addEventListener('scroll', function () {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            navbar.style.boxShadow = '0 6px 30px rgba(0, 0, 0, 0.2)';
        } else {
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
        }

        lastScroll = currentScroll;
    });
});
