// ============================================
// Dashboard JavaScript - ExpTrack
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // DOM Elements
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.getElementById('sidebar');
    const sidebarClose = document.getElementById('sidebarClose');
    const mobileOverlay = document.getElementById('mobileOverlay');
    const userProfile = document.getElementById('userProfile');
    const userDropdown = document.getElementById('userDropdown');
    
    // ============================================
    // Mobile Sidebar Toggle
    // ============================================
    function openSidebar() {
        sidebar.classList.add('active');
        mobileOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    function closeSidebar() {
        sidebar.classList.remove('active');
        mobileOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', openSidebar);
    }
    
    if (sidebarClose) {
        sidebarClose.addEventListener('click', closeSidebar);
    }
    
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', function() {
            closeSidebar();
            closeUserDropdown();
        });
    }
    
    // ============================================
    // User Profile Dropdown
    // ============================================
    function openUserDropdown() {
        userProfile.classList.add('active');
        userDropdown.classList.add('active');
    }
    
    function closeUserDropdown() {
        userProfile.classList.remove('active');
        userDropdown.classList.remove('active');
    }
    
    function toggleUserDropdown() {
        if (userDropdown.classList.contains('active')) {
            closeUserDropdown();
        } else {
            openUserDropdown();
        }
    }
    
    if (userProfile) {
        userProfile.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleUserDropdown();
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (userDropdown && !userDropdown.contains(e.target) && !userProfile.contains(e.target)) {
            closeUserDropdown();
        }
    });
    
    // ============================================
    // Keyboard Navigation
    // ============================================
    document.addEventListener('keydown', function(e) {
        // Close on Escape key
        if (e.key === 'Escape') {
            closeSidebar();
            closeUserDropdown();
        }
    });
    
    // ============================================
    // Window Resize Handler
    // ============================================
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Close sidebar on desktop
            if (window.innerWidth > 1024) {
                closeSidebar();
            }
        }, 250);
    });
    
    // ============================================
    // Animate Progress Bars on Load
    // ============================================
    const progressBars = document.querySelectorAll('.progress-fill');
    
    function animateProgressBars() {
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0';
            setTimeout(() => {
                bar.style.width = width;
            }, 100);
        });
    }
    
    // Animate on page load
    animateProgressBars();
    
    // ============================================
    // Touch Swipe Support for Sidebar
    // ============================================
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
        
        // Swipe right to open sidebar (from left edge)
        if (swipeDistance > swipeThreshold && touchStartX < 30 && !sidebar.classList.contains('active')) {
            openSidebar();
        }
        
        // Swipe left to close sidebar
        if (swipeDistance < -swipeThreshold && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    }
    
    // ============================================
    // Active Sidebar Link Highlight
    // ============================================
    const sidebarLinks = document.querySelectorAll('.sidebar-link:not(.sidebar-logout)');
    const currentPath = window.location.pathname;
    
    sidebarLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
});