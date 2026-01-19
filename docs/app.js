// Configuration
const DATA_URL = 'price_drops.json';
const REFRESH_INTERVAL = 300000; // 5 minutes in milliseconds

let priceData = null;
let countdownTimer = null;
let refreshTimer = null;
let currentSort = 'percentage';

// Fetch price drop data
async function fetchPriceData() {
    try {
        console.log('Fetching price data from:', DATA_URL);
        
        const response = await fetch(DATA_URL + '?t=' + Date.now(), {
            cache: 'no-store'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        priceData = await response.json();
        console.log('Price data loaded:', priceData);
        
        displayData();
        startCountdown();
        
    } catch (error) {
        console.error('Error fetching data:', error);
        document.getElementById('priceDrops').innerHTML = `
            <div class="error">
                <h2>❌ Error Loading Data</h2>
                <p>${error.message}</p>
                <p style="margin-top: 10px; font-size: 0.9em;">
                    Data will be automatically retried in 5 minutes
                </p>
            </div>
        `;
    }
}

// Display the price data
function displayData() {
    if (!priceData) return;
    
    // Update stats
    document.getElementById('totalDrops').textContent = priceData.total_drops.toLocaleString();
    document.getElementById('sitesTracked').textContent = priceData.site_stats.length;
    
    const topDrop = priceData.drops.length > 0 ? priceData.drops[0].percentage : 0;
    document.getElementById('topDrop').textContent = topDrop.toFixed(1) + '%';
    
    // Update last update time
    const updateTime = new Date(priceData.generated_at);
    document.getElementById('lastUpdate').textContent = 
        `Last updated: ${updateTime.toLocaleString()}`;
    
    // Display drops
    renderDrops(priceData.drops);
}

// Render price drops
function renderDrops(drops) {
    const container = document.getElementById('priceDrops');
    
    if (drops.length === 0) {
        container.innerHTML = '<p class="loading">No price drops found</p>';
        return;
    }
    
    const html = drops.map(drop => {
        const badge = drop.percentage >= 50 ? '🔥' : drop.percentage >= 30 ? '📉' : '💰';
        
        let priceHtml = '';
        if (drop.old_price && drop.new_price) {
            const savings = (parseFloat(drop.old_price) - parseFloat(drop.new_price)).toFixed(2);
            priceHtml = `
                <div class="drop-price">
                    <span class="old">£${drop.old_price}</span> → 
                    <span class="new">£${drop.new_price}</span>
                    (Save £${savings})
                </div>
            `;
        }
        
        let linkHtml = '';
        if (drop.url) {
            linkHtml = `<a href="${drop.url}" class="drop-link" target="_blank" rel="noopener noreferrer">View Product →</a>`;
        }
        
        return `
            <div class="drop-item">
                <div class="drop-header">
                    <span class="drop-badge">${badge}</span>
                    <span class="drop-percentage">${drop.percentage.toFixed(1)}%</span>
                    <span class="drop-site">${escapeHtml(drop.site)}</span>
                </div>
                <div class="drop-product">${escapeHtml(drop.product)}</div>
                ${priceHtml}
                ${linkHtml}
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// Helper to escape HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Search functionality
document.getElementById('searchBox').addEventListener('input', (e) => {
    if (!priceData) return;
    
    const query = e.target.textContent.toLowerCase();
    const filtered = priceData.drops.filter(drop => 
        drop.product.toLowerCase().includes(query) ||
        drop.site.toLowerCase().includes(query)
    );
    
    renderDrops(filtered);
});

// Custom select functionality
const selectElement = document.getElementById('sortSelect');
const trigger = selectElement.querySelector('.select-trigger');
const options = selectElement.querySelectorAll('.option');

trigger.addEventListener('click', () => {
    selectElement.classList.toggle('active');
});

document.addEventListener('click', (e) => {
    if (!selectElement.contains(e.target)) {
        selectElement.classList.remove('active');
    }
});

options.forEach(option => {
    option.addEventListener('click', () => {
        const value = option.getAttribute('data-value');
        const text = option.textContent;
        
        trigger.querySelector('span').textContent = text;
        
        options.forEach(opt => opt.classList.remove('selected'));
        option.classList.add('selected');
        
        selectElement.classList.remove('active');
        
        if (!priceData) return;
        
        currentSort = value;
        let sorted = [...priceData.drops];
        
        if (value === 'percentage') {
            sorted.sort((a, b) => b.percentage - a.percentage);
        } else if (value === 'savings') {
            sorted.sort((a, b) => {
                const savingsA = a.old_price && a.new_price ? 
                    parseFloat(a.old_price) - parseFloat(a.new_price) : 0;
                const savingsB = b.old_price && b.new_price ? 
                    parseFloat(b.old_price) - parseFloat(b.new_price) : 0;
                return savingsB - savingsA;
            });
        } else if (value === 'site') {
            sorted.sort((a, b) => a.site.localeCompare(b.site));
        }
        
        renderDrops(sorted);
    });
});

// Countdown timer
function startCountdown() {
    let timeLeft = REFRESH_INTERVAL / 1000;
    
    if (countdownTimer) clearInterval(countdownTimer);
    
    countdownTimer = setInterval(() => {
        timeLeft--;
        
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        
        document.getElementById('countdown').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearInterval(countdownTimer);
        }
    }, 1000);
}

// Auto-refresh
function scheduleRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    
    refreshTimer = setInterval(() => {
        console.log('Auto-refreshing data...');
        fetchPriceData();
    }, REFRESH_INTERVAL);
}

// Initial load
fetchPriceData();
scheduleRefresh();

// Inject script into page
const scriptTag = document.createElement('script');
scriptTag.textContent = document.currentScript.textContent;
document.getElementById('app-script').appendChild(scriptTag);
