/* ===== GLOBAL VARIABLES ===== */
const config = {
    animationDuration: 300,
    scrollThreshold: 0.1,
    debounceDelay: 150
};

/* ===== SCROLL REVEAL OBSERVER ===== */
const observerOptions = {
    threshold: config.scrollThreshold,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

/* ===== INITIALIZATION ===== */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize scroll reveal
    initScrollReveal();

    // Initialize navbar
    initNavbar();

    // Initialize channel filters if on channel list page
    if (document.querySelector('.filter-btn')) {
        initChannelFilters();
    }

    // Initialize channel cards
    initChannelCards();

    // Initialize smooth scroll links
    initSmoothScroll();

    // Initialize form handling
    initForms();

    // Initialize accessibility
    initAccessibility();

    // Add page load animation
    document.body.style.opacity = '1';
});

/* ===== SCROLL REVEAL INITIALIZATION ===== */
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal');

    revealElements.forEach((element, index) => {
        // Stagger animation delays
        const delay = index * 100;
        element.style.animationDelay = `${delay}ms`;
        observer.observe(element);
    });

    // Check visible elements after a brief delay for layout calculation
    setTimeout(() => {
        revealElements.forEach((element) => {
            const rect = element.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) {
                // Element is visible in viewport, add visible class
                element.classList.add('visible');
                observer.unobserve(element);
            }
        });
    }, 100);
}

/* ===== NAVBAR FUNCTIONALITY ===== */
function initNavbar() {
    const navbar = document.querySelector('nav');
    let lastScrollY = 0;
    let isScrolling = false;

    window.addEventListener('scroll', debounce(() => {
        const scrollY = window.pageYOffset;

        // Update navbar background based on scroll
        if (scrollY > 50) {
            navbar.classList.add('scrolled');
            navbar.style.background = 'rgba(0, 0, 0, 0.6)';
            navbar.style.backdropFilter = 'blur(20px)';
            navbar.style.boxShadow = '0 10px 40px rgba(168, 85, 247, 0.1)';
        } else {
            navbar.classList.remove('scrolled');
            navbar.style.background = 'rgba(15, 23, 42, 0.7)';
            navbar.style.backdropFilter = 'blur(12px)';
            navbar.style.boxShadow = 'none';
        }

        lastScrollY = scrollY;
    }, config.debounceDelay));

    // Mobile menu toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', navMenu.classList.contains('active'));
        });

        // Close menu when link is clicked
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            });
        });
    }
}

/* ===== CHANNEL FILTER FUNCTIONALITY ===== */
function initChannelFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const channelCards = document.querySelectorAll('.channel-card');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active button
            filterButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.setAttribute('aria-pressed', 'false');
            });
            this.classList.add('active');
            this.setAttribute('aria-pressed', 'true');

            // Filter channels
            const filterValue = this.getAttribute('data-filter');
            filterChannels(filterValue, channelCards);
        });
    });
}

function filterChannels(filter, channelCards) {
    let visibleCount = 0;

    channelCards.forEach((card, index) => {
        const category = card.getAttribute('data-category');
        const shouldShow = filter === 'all' || category === filter;

        if (shouldShow) {
            setTimeout(() => {
                card.style.display = 'block';
                card.offsetHeight; // Trigger reflow
                card.style.opacity = '1';
                card.style.transform = 'scale(1)';
            }, index * 30);
            visibleCount++;
        } else {
            card.style.opacity = '0';
            card.style.transform = 'scale(0.8)';
            setTimeout(() => {
                card.style.display = 'none';
            }, 300);
        }
    });

    // Announce to screen readers
    announceToScreenReader(`${visibleCount} chaînes trouvées`);
}

/* ===== CHANNEL CARDS INTERACTION ===== */
function initChannelCards() {
    const channelCards = document.querySelectorAll('.channel-card');

    channelCards.forEach(card => {
        // Click to open modal
        card.addEventListener('click', function() {
            const channelName = this.getAttribute('data-channel');
            if (channelName) {
                openChannelModal(channelName);
            }
        });

        // Keyboard accessibility
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const channelName = this.getAttribute('data-channel');
                if (channelName) {
                    openChannelModal(channelName);
                }
            }
        });

        // Hover animations with performance optimization
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-16px) scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

/* ===== CHANNEL MODAL ===== */
function openChannelModal(channelName) {
    let modal = document.getElementById('channelModal');

    if (!modal) {
        // Create modal if it doesn't exist
        const modalHTML = `
            <div id="channelModal" class="modal" role="dialog" aria-labelledby="channelModalTitle" aria-hidden="true">
                <div class="modal-content">
                    <button class="modal-close" aria-label="Fermer">&times;</button>
                    <h2 id="channelModalTitle" class="text-2xl font-bold mb-4">${channelName}</h2>
                    <p class="text-gray-300 mb-6">Regarder en direct: <strong>${channelName}</strong></p>
                    <button class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg font-bold hover:shadow-lg transition-all" onclick="window.location.href='./channel-list.html'">
                        Retourner aux chaînes
                    </button>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('channelModal');
    }
    modal.classList.add('active');
    modal.setAttribute('aria-hidden', 'false');

    // Focus management
    const closeBtn = modal.querySelector('.modal-close');
    closeBtn.focus();

    // Close button
    closeBtn.addEventListener('click', closeChannelModal);

    // Close on escape key
    document.addEventListener('keydown', handleModalEscape);

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeChannelModal();
        }
    });
}

function closeChannelModal() {
    const modal = document.getElementById('channelModal');
    if (modal) {
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
    }
    document.removeEventListener('keydown', handleModalEscape);
}

function handleModalEscape(e) {
    if (e.key === 'Escape') {
        closeChannelModal();
    }
}

/* ===== SUBSCRIPTION BUTTONS ===== */
function initSubscriptionButtons() {
    const subscribeButtons = document.querySelectorAll('[data-plan]');

    subscribeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const planName = this.getAttribute('data-plan');
            openSubscriptionModal(planName);
        });

        // Keyboard accessibility
        button.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                button.click();
            }
        });
    });
}

function openSubscriptionModal(planName) {
    const modal = document.getElementById('subscriptionModal');
    if (modal) {
        modal.classList.add('active');
        const title = modal.querySelector('h2');
        if (title) title.textContent = `S'abonner à ${planName}`;

        // Focus management
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) closeBtn.focus();
    }
}

function closeSubscriptionModal() {
    const modal = document.getElementById('subscriptionModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/* ===== FORM HANDLING ===== */
function initForms() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Get form data
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);

            // Validate
            if (!data.email || !validateEmail(data.email)) {
                showNotification('Veuillez entrer une adresse email valide', 'error');
                return;
            }

            // Simulate submission
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            const originalHTML = submitBtn.innerHTML;

            submitBtn.innerHTML = '<span class="loading"></span> Traitement...';
            submitBtn.disabled = true;

            // Simulate API call
            setTimeout(() => {
                showNotification('Inscription réussie! Vérifiez votre email.', 'success');
                form.reset();
                submitBtn.innerHTML = originalHTML;
                submitBtn.disabled = false;
            }, 1500);
        });
    });
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/* ===== NOTIFICATIONS ===== */
function showNotification(message, type = 'info') {
    // Create notification container if it doesn't exist
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2000;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    const notification = document.createElement('div');
    const bgColor = type === 'success' ? 'rgba(34, 197, 94, 0.9)' :
                    type === 'error' ? 'rgba(239, 68, 68, 0.9)' :
                    'rgba(59, 130, 246, 0.9)';

    notification.style.cssText = `
        padding: 16px 24px;
        background: ${bgColor};
        color: white;
        border-radius: 12px;
        margin-bottom: 10px;
        animation: slideInFromRight 0.3s ease;
        font-weight: 500;
        max-width: 400px;
        word-wrap: break-word;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        pointer-events: auto;
    `;

    notification.textContent = message;
    notification.setAttribute('role', 'status');
    notification.setAttribute('aria-live', 'polite');

    container.appendChild(notification);

    // Auto remove after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideInFromRight 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

/* ===== SEARCH FUNCTIONALITY ===== */
function initSearch() {
    const searchInput = document.getElementById('searchInput');
    const channelCards = document.querySelectorAll('.channel-card');

    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            const searchTerm = this.value.toLowerCase();
            let visibleCount = 0;

            channelCards.forEach(card => {
                const channelName = card.getAttribute('data-channel').toLowerCase();

                if (channelName.includes(searchTerm)) {
                    card.style.display = 'block';
                    card.style.opacity = '1';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            // Show message if no results
            if (visibleCount === 0 && searchTerm.length > 0) {
                showNotification('Aucune chaîne trouvée', 'info');
            }
        }, config.debounceDelay));

        // Accessibility
        searchInput.setAttribute('aria-label', 'Rechercher une chaîne');
    }
}

/* ===== SMOOTH SCROLL LINKS ===== */
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');

            if (href === '#') {
                e.preventDefault();
                return;
            }

            const target = document.querySelector(href);

            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Announce to screen readers
                announceToScreenReader(`Navigation vers ${href.substring(1)}`);
            }
        });
    });
}

/* ===== LAZY LOADING ===== */
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        img.classList.add('loaded');
                    }
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px'
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
}

/* ===== ACCESSIBILITY FEATURES ===== */
function initAccessibility() {
    // Skip to main content
    const skipLink = document.createElement('a');
    skipLink.href = '#main';
    skipLink.textContent = 'Sauter au contenu principal';
    skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 0;
        background: #000;
        color: white;
        padding: 8px;
        z-index: 100;
    `;

    skipLink.addEventListener('focus', function() {
        this.style.top = '0';
    });

    skipLink.addEventListener('blur', function() {
        this.style.top = '-40px';
    });

    document.body.insertBefore(skipLink, document.body.firstChild);

    // Announce page load to screen readers
    announceToScreenReader('Page chargée. Appuyez sur la touche Tab pour commencer à naviguer.');
}

function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    setTimeout(() => announcement.remove(), 1000);
}

/* ===== UTILITY FUNCTIONS ===== */
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

function setUrlParam(param, value) {
    const url = new URL(window.location);
    url.searchParams.set(param, value);
    window.history.pushState({}, '', url);
}

/* ===== PAGE VISIBILITY ===== */
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Pause animations when page is hidden
        document.body.style.animationPlayState = 'paused';
    } else {
        // Resume animations when page is visible
        document.body.style.animationPlayState = 'running';
    }
});

/* ===== PERFORMANCE MONITORING ===== */
if (window.performance && window.performance.navigation.type === 1) {
    // Page was reloaded
    console.log('Page reloaded');
}

// Log Core Web Vitals when available
if ('web-vital' in window) {
    console.log('Web Vitals available');
}

/* ===== RESPONSIVE BEHAVIOR ===== */
let resizeTimeout;
window.addEventListener('resize', debounce(() => {
    // Handle responsive adjustments
    const width = window.innerWidth;
    const isMobile = width < 768;

    if (isMobile) {
        // Mobile-specific adjustments
        document.body.classList.add('mobile');
    } else {
        // Desktop-specific adjustments
        document.body.classList.remove('mobile');
    }
}, config.debounceDelay));

// Initial call
window.dispatchEvent(new Event('resize'));

/* ===== LOAD SEARCH AND SUBSCRIPTION WHEN NEEDED ===== */
setTimeout(() => {
    initSearch();
    initSubscriptionButtons();
}, 100);
