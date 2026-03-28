/* ===== CATALOG PAGE JAVASCRIPT ===== */

let allChannelsData = null;

/**
 * Load catalog data from API
 */
async function loadCatalog() {
    try {
        const response = await fetch('/api/channels');
        if (!response.ok) throw new Error('Erreur API');
        allChannelsData = await response.json();
        renderCountries();
    } catch (error) {
        console.error('Erreur:', error);
        const container = document.getElementById('countriesContainer');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-500 text-center';
        errorDiv.textContent = 'Erreur de chargement des données';
        container.textContent = '';
        container.appendChild(errorDiv);
    }
}

/**
 * Render country cards based on search input
 */
function renderCountries() {
    if (!allChannelsData) return;

    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const container = document.getElementById('countriesContainer');
    container.textContent = '';

    const gridDiv = document.createElement('div');
    gridDiv.className = 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3';

    Object.keys(allChannelsData.regions).sort().forEach(region => {
        const data = allChannelsData.regions[region];
        if (searchTerm && !region.toLowerCase().includes(searchTerm)) return;

        const card = document.createElement('button');
        card.className = 'country-card';

        const regionName = document.createElement('div');
        regionName.className = 'font-sans font-bold';
        regionName.textContent = region;

        const channelCount = document.createElement('div');
        channelCount.className = 'text-xs';
        channelCount.style.color = 'var(--text-muted)';
        channelCount.style.marginTop = '0.25rem';
        channelCount.textContent = data.count + ' chaînes';

        card.appendChild(regionName);
        card.appendChild(channelCount);
        card.onclick = () => openChannelsModal(region);
        gridDiv.appendChild(card);
    });

    container.appendChild(gridDiv);
}

/**
 * Open channels modal for selected region
 */
function openChannelsModal(region) {
    if (!allChannelsData || !allChannelsData.regions[region]) return;

    const data = allChannelsData.regions[region];
    document.getElementById('modalCountryName').textContent = region;
    document.getElementById('modalChannelCount').textContent = data.count + ' chaînes disponibles';

    const channelsList = document.getElementById('modalChannelsList');
    channelsList.textContent = '';

    data.channels.forEach(channel => {
        const item = document.createElement('div');
        item.className = 'channel-item';
        item.textContent = channel.name || channel;
        channelsList.appendChild(item);
    });

    document.getElementById('channelsModal').classList.remove('hidden');
}

/**
 * Close channels modal
 */
function closeChannelsModal() {
    document.getElementById('channelsModal').classList.add('hidden');
}

/**
 * Initialize catalog page
 */
document.addEventListener('DOMContentLoaded', loadCatalog);

/**
 * Search input event listener
 */
document.getElementById('searchInput').addEventListener('input', renderCountries);

/**
 * Escape key handler for modal
 */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeChannelsModal();
    }
});
