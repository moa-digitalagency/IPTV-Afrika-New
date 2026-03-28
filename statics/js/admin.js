/* ===== ADMIN DASHBOARD JAVASCRIPT ===== */

/**
 * Toggle mobile sidebar
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('visible');
        sidebar.classList.toggle('hidden');
    }
}

/**
 * Close sidebar on mobile when clicking a link
 */
function initSidebarLinks() {
    document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                toggleSidebar();
            }
            // Update active state
            document.querySelectorAll('.sidebar-link').forEach(l => {
                l.classList.remove('active');
            });
            link.classList.add('active');
        });
    });
}

/**
 * Mark current page link as active
 */
function initActiveLink() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

/**
 * Load cache status
 */
async function loadCacheStatus() {
    try {
        const response = await fetch('/app/api/cache/status');
        if (!response.ok) throw new Error('Failed to load cache status');

        const status = await response.json();
        updateCacheWidget(status);
    } catch (error) {
        console.error('Error loading cache status:', error);
    }
}

/**
 * Update cache status widget using safe DOM methods
 */
function updateCacheWidget(status) {
    const widget = document.getElementById('cacheWidget');
    if (!widget) return;

    // Clear widget
    while (widget.firstChild) {
        widget.removeChild(widget.firstChild);
    }

    // Create status section
    const statusDiv = document.createElement('div');
    statusDiv.className = 'cache-status';

    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'cache-indicator';

    const dotDiv = document.createElement('div');
    dotDiv.className = status.last_sync_status === 'error' ? 'cache-dot offline' : 'cache-dot';

    const labelDiv = document.createElement('div');
    const labelTitle = document.createElement('div');
    labelTitle.style.fontWeight = '600';
    labelTitle.textContent = 'Cache Status';

    const lastSync = status.last_sync ? new Date(status.last_sync) : null;
    const lastSyncText = lastSync
        ? `${lastSync.toLocaleString('fr-FR')} (${status.last_sync_duration_ms}ms)`
        : 'Never';

    const cacheTime = document.createElement('div');
    cacheTime.className = 'cache-time';
    cacheTime.textContent = `Last sync: ${lastSyncText}`;

    labelDiv.appendChild(labelTitle);
    labelDiv.appendChild(cacheTime);
    indicatorDiv.appendChild(dotDiv);
    indicatorDiv.appendChild(labelDiv);

    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'cache-actions';

    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'btn btn-sm';
    refreshBtn.textContent = '🔄 Refresh';
    refreshBtn.onclick = refreshCache;

    actionsDiv.appendChild(refreshBtn);
    statusDiv.appendChild(indicatorDiv);
    statusDiv.appendChild(actionsDiv);

    // Create stats grid
    const statsGrid = document.createElement('div');
    statsGrid.style.cssText = 'display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;';

    const stats_data = [
        { value: status.total_lines, label: 'Total Lines', color: 'var(--gold)' },
        { value: status.active_lines, label: 'Active', color: 'var(--success)' },
        { value: status.trial_lines, label: 'Trial', color: 'var(--warning)' },
        { value: status.total_packages, label: 'Packages', color: 'var(--gold-light)' }
    ];

    stats_data.forEach(stat => {
        const statDiv = document.createElement('div');
        statDiv.style.textAlign = 'center';

        const valueDiv = document.createElement('div');
        valueDiv.style.cssText = `font-size: 1.5rem; font-weight: 700; color: ${stat.color};`;
        valueDiv.textContent = stat.value;

        const labelDiv = document.createElement('div');
        labelDiv.style.cssText = 'font-size: 0.875rem; color: var(--text-muted);';
        labelDiv.textContent = stat.label;

        statDiv.appendChild(valueDiv);
        statDiv.appendChild(labelDiv);
        statsGrid.appendChild(statDiv);
    });

    widget.appendChild(statusDiv);
    widget.appendChild(statsGrid);
}

/**
 * Refresh cache manually
 */
async function refreshCache() {
    const button = event.target.closest('button');
    const originalText = button.textContent;

    try {
        button.disabled = true;
        button.textContent = '⏳ Syncing...';

        const response = await fetch('/app/api/cache/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Sync failed');
        }

        button.textContent = '✅ Synced';
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
            loadCacheStatus();
        }, 2000);

    } catch (error) {
        console.error('Sync error:', error);
        button.textContent = '❌ Error';
        setTimeout(() => {
            button.textContent = originalText;
            button.disabled = false;
        }, 2000);
    }
}

/**
 * Load dashboard statistics
 */
async function loadDashboardStats() {
    try {
        const response = await fetch('/app/api/stats/summary');
        if (!response.ok) throw new Error('Failed to load stats');

        const stats = await response.json();
        updateStatCards(stats);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Update stat cards with data
 */
function updateStatCards(stats) {
    // Update lines stat
    const linesCard = document.querySelector('[data-stat="lines"]');
    if (linesCard) {
        linesCard.querySelector('.stat-value').textContent = stats.lines.total;
        const changeEl = linesCard.querySelector('.stat-change');
        changeEl.textContent = `↑ ${stats.lines.active} active`;
        changeEl.classList.add('positive');
    }

    // Update users stat
    const usersCard = document.querySelector('[data-stat="users"]');
    if (usersCard) {
        usersCard.querySelector('.stat-value').textContent = stats.users.total;
    }

    // Update expired stat
    const expiredCard = document.querySelector('[data-stat="expired"]');
    if (expiredCard) {
        expiredCard.querySelector('.stat-value').textContent = stats.lines.expired;
        const changeEl = expiredCard.querySelector('.stat-change');
        changeEl.textContent = `⚠️ ${stats.lines.expired} expired`;
        changeEl.classList.add('negative');
    }

    // Update trial stat
    const trialCard = document.querySelector('[data-stat="trial"]');
    if (trialCard) {
        trialCard.querySelector('.stat-value').textContent = stats.lines.trial;
    }
}

/**
 * Get CSRF token from meta tag or cookie
 */
function getCsrfToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    if (token) return token.getAttribute('content');

    // Fallback to cookie
    const name = 'csrf_token=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length);
        }
    }
    return '';
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('fr-FR');
}

/**
 * Format number with thousand separators
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/**
 * Initialize sidebar visibility based on screen size
 */
function initSidebarVisibility() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;

    // On desktop (min-width: 769px), remove hidden class
    if (window.innerWidth >= 769) {
        sidebar.classList.remove('hidden');
        sidebar.classList.remove('visible');
    } else {
        // On mobile, ensure hidden class is present
        sidebar.classList.add('hidden');
        sidebar.classList.remove('visible');
    }
}

/**
 * Initialize admin page
 */
document.addEventListener('DOMContentLoaded', () => {
    initSidebarVisibility();
    initSidebarLinks();
    initActiveLink();
    loadCacheStatus();
    loadDashboardStats();

    // Reload stats every 30 seconds
    setInterval(loadDashboardStats, 30000);

    // Reload cache status every 2 minutes
    setInterval(loadCacheStatus, 120000);
});

/**
 * Handle window resize to adjust sidebar visibility
 */
window.addEventListener('resize', () => {
    initSidebarVisibility();
});

/**
 * Close sidebar when clicking outside on mobile
 */
document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.menu-toggle');

    if (sidebar && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
        if (window.innerWidth <= 768 && sidebar.classList.contains('visible')) {
            toggleSidebar();
        }
    }
});
