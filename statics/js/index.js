/* ===== INDEX PAGE JAVASCRIPT ===== */

/**
 * Toggle mobile menu
 */
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('hidden');
}

/**
 * FAQ Accordion Toggle
 */
function toggleFaq(btn) {
    const answer = btn.nextElementSibling;
    const chevron = btn.querySelector('.faq-chevron');
    const isOpen = answer.classList.contains('open');

    // Close all
    document.querySelectorAll('.faq-answer').forEach(a => a.classList.remove('open'));
    document.querySelectorAll('.faq-chevron').forEach(c => c.classList.remove('rotated'));

    // Toggle current
    if (!isOpen) {
        answer.classList.add('open');
        chevron.classList.add('rotated');
    }
}

/**
 * Scroll Reveal (IntersectionObserver)
 */
function initReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px'
    });

    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Check elements already in viewport on load
 */
function checkVisibleOnLoad() {
    document.querySelectorAll('.reveal').forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.classList.add('visible');
        }
    });
}

/**
 * Navbar scroll effect
 */
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    const scrollY = window.scrollY;

    if (scrollY > 100) {
        navbar.style.background = 'rgba(10,8,6,0.95)';
    } else {
        navbar.style.background = 'rgba(10,8,6,0.85)';
    }
    lastScroll = scrollY;
});

/**
 * Pricing card selection
 */
function selectPricingPeriod(card) {
    // Remove highlight from all cards
    document.querySelectorAll('.pricing-card, .pricing-featured').forEach(c => {
        if (c.classList && c.classList.contains('pricing-card')) {
            c.style.borderColor = 'var(--border-gold)';
            c.style.boxShadow = 'none';
        }
    });

    // Highlight selected card
    if (card.classList.contains('pricing-card')) {
        card.style.borderColor = 'var(--gold)';
        card.style.boxShadow = '0 0 40px var(--glow-gold), 0 0 80px rgba(212,165,116,0.06)';
    }
}

/**
 * Initialize on DOM load
 */
document.addEventListener('DOMContentLoaded', () => {
    initReveal();
    checkVisibleOnLoad();
    // Set default period to 1 month
    const defaultPeriod = document.querySelector('[data-period="1m"]');
    if (defaultPeriod) {
        defaultPeriod.click();
    }
});
