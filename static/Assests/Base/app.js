// Initialize Lucide Icons
lucide.createIcons();

// DOM Elements
const mobileToggle = document.getElementById('mobileToggle');
const navLinks = document.getElementById('navLinks');
const navCloseBtn = document.getElementById('navCloseBtn');
const mobileOverlay = document.getElementById('mobileOverlay');
const body = document.body;

// Preloader
window.addEventListener('load', function() {
    const preloader = document.getElementById('preloader');
    
    setTimeout(function() {
        preloader.classList.add('fade-out');
        body.classList.remove('loading');
    }, 2000);
});

// Mobile Navigation Toggle
function openMobileNav() {
    navLinks.classList.add('active');
    mobileOverlay.classList.add('active');
    mobileToggle.classList.add('active');
    body.classList.add('nav-open');
}

function closeMobileNav() {
    navLinks.classList.remove('active');
    mobileOverlay.classList.remove('active');
    mobileToggle.classList.remove('active');
    body.classList.remove('nav-open');
}

// Toggle button click
mobileToggle.addEventListener('click', function() {
    if (navLinks.classList.contains('active')) {
        closeMobileNav();
    } else {
        openMobileNav();
    }
});

// Close button click
navCloseBtn.addEventListener('click', closeMobileNav);

// Overlay click
mobileOverlay.addEventListener('click', closeMobileNav);

// Close nav when clicking on a nav link
const navLinkItems = document.querySelectorAll('.nav-link');
navLinkItems.forEach(link => {
    link.addEventListener('click', function() {
        if (window.innerWidth <= 768) {
            closeMobileNav();
        }
    });
});

// Close nav on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && navLinks.classList.contains('active')) {
        closeMobileNav();
    }
});

// Scroll Progress Bar
window.addEventListener('scroll', function() {
    const scrollProgress = document.getElementById('scrollProgress');
    const scrollTop = document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const progress = (scrollTop / scrollHeight) * 100;
    scrollProgress.style.width = progress + '%';
});

// Smooth Scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId !== '#') {
            const target = document.querySelector(targetId);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    });
});

// Dynamic Year for Copyright
document.getElementById('footerCopyright').innerHTML = '© ' + new Date().getFullYear() + ' ExpTrack. All rights reserved.';

// Animate progress bars on scroll
const progressBars = document.querySelectorAll('.progress-fill');
const observerOptions = { threshold: 0.5 };

const progressObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const progress = entry.target.style.getPropertyValue('--progress');
            entry.target.style.transform = `scaleX(${parseFloat(progress) / 100})`;
        }
    });
}, observerOptions);

progressBars.forEach(bar => {
    progressObserver.observe(bar);
});

// Repeat transaction notifications
function repeatTransactionAnimations() {
    const notifications = document.querySelectorAll('.transaction-notification');
    notifications.forEach(notification => {
        notification.style.animation = 'none';
        notification.offsetHeight; // Trigger reflow
        notification.style.animation = null;
    });
}

setInterval(repeatTransactionAnimations, 6000);

// Fade In Images on Scroll
const fadeInImages = document.querySelectorAll('.fade-in-image');

const fadeInObserverOptions = {
    threshold: 0.3,
    rootMargin: '0px 0px -50px 0px'
};

const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in-visible');
        } else {
            entry.target.classList.remove('fade-in-visible');
        }
    });
}, fadeInObserverOptions);

fadeInImages.forEach(image => {
    fadeInObserver.observe(image);
});

// 3D Dashboard Mouse Effect
const dashboardWidget = document.querySelector('.dashboard-widget');
const dashboardWrapper = document.querySelector('.dashboard-wrapper');

if (dashboardWrapper && dashboardWidget) {
    dashboardWrapper.addEventListener('mousemove', (e) => {
        const rect = dashboardWrapper.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        dashboardWidget.style.transform = `rotateY(${rotateY - 8}deg) rotateX(${rotateX + 5}deg) translateZ(20px)`;
    });

    dashboardWrapper.addEventListener('mouseleave', () => {
        dashboardWidget.style.transform = 'rotateY(-8deg) rotateX(5deg)';
    });
}

// Re-initialize Lucide icons after DOM updates (for dynamically added content)
function reinitializeLucide() {
    lucide.createIcons();
}

// Handle window resize
let resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
        // Close mobile nav if window is resized to desktop
        if (window.innerWidth > 768) {
            closeMobileNav();
        }
    }, 250);
});

// Touch support for mobile devices
let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
}, false);

document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}, false);

function handleSwipe() {
    const swipeThreshold = 50;
    const swipeDistance = touchEndX - touchStartX;
    
    // Swipe right to open nav (only if starting from left edge)
    if (swipeDistance > swipeThreshold && touchStartX < 30 && !navLinks.classList.contains('active')) {
        openMobileNav();
    }
    
    // Swipe left to close nav
    if (swipeDistance < -swipeThreshold && navLinks.classList.contains('active')) {
        closeMobileNav();
    }
}