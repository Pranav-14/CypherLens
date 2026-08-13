/**
 * CypherLens Web Radar Client Application with Precision Parameters and Regional Routing
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const searchForm = document.getElementById("searchForm");
    const queryInput = document.getElementById("queryInput");
    const categoryPills = document.querySelectorAll(".pill");
    const promptChips = document.querySelectorAll(".prompt-chip");
    const regionSelect = document.getElementById("regionSelect");
    
    const statusSection = document.getElementById("statusSection");
    const metaTarget = document.getElementById("metaTarget");
    const metaLens = document.getElementById("metaLens");
    const metaRegion = document.getElementById("metaRegion");
    const metaNodes = document.getElementById("metaNodes");
    const metaLatency = document.getElementById("metaLatency");

    const deepRadarSection = document.getElementById("deepRadarSection");
    const deepRadarContainer = document.getElementById("deepRadarContainer");

    const loadingContainer = document.getElementById("loadingContainer");
    const resultsGrid = document.getElementById("resultsGrid");
    const initialState = document.getElementById("initialState");

    // Watchlist Elements
    const toggleWatchlistBtn = document.getElementById("toggleWatchlistBtn");
    const closeDrawerBtn = document.getElementById("closeDrawerBtn");
    const clearWatchlistBtn = document.getElementById("clearWatchlistBtn");
    const watchlistDrawer = document.getElementById("watchlistDrawer");
    const drawerOverlay = document.getElementById("drawerOverlay");
    const watchlistItemsContainer = document.getElementById("watchlistItems");
    const watchlistCountBadge = document.getElementById("watchlistCount");
    const drawerCount = document.getElementById("drawerCount");

    let currentCategory = "auto";
    let currentRegion = localStorage.getItem("cypherlens_region") || "de";
    let watchlist = JSON.parse(localStorage.getItem("cypherlens_watchlist") || "[]");

    // Initialize Region Select value
    if (regionSelect) {
        regionSelect.value = currentRegion;
        regionSelect.addEventListener("change", (e) => {
            currentRegion = e.target.value;
            localStorage.setItem("cypherlens_region", currentRegion);
            if (queryInput.value.trim()) {
                performSearch(queryInput.value.trim());
            }
        });
    }

    // Update Watchlist UI on load
    updateWatchlistUI();

    // Category Pill Click
    categoryPills.forEach(pill => {
        pill.addEventListener("click", () => {
            categoryPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            currentCategory = pill.getAttribute("data-category");
            if (queryInput.value.trim()) {
                performSearch(queryInput.value.trim());
            }
        });
    });

    // Preset Prompt Chips Click
    promptChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const promptText = chip.getAttribute("data-query");
            queryInput.value = promptText;
            performSearch(promptText);
        });
    });

    // Search Form Submit
    searchForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const q = queryInput.value.trim();
        if (q) {
            performSearch(q);
        }
    });

    // Keyboard shortcut: '/' focuses search
    window.addEventListener("keydown", (e) => {
        if (e.key === "/" && document.activeElement !== queryInput) {
            e.preventDefault();
            queryInput.focus();
        }
    });

    // Main Search Action
    async function performSearch(query) {
        // UI transitions
        initialState.style.display = "none";
        resultsGrid.innerHTML = "";
        deepRadarContainer.innerHTML = "";
        deepRadarSection.style.display = "none";
        statusSection.style.display = "none";
        loadingContainer.style.display = "block";

        try {
            const url = `/api/search?q=${encodeURIComponent(query)}&category=${encodeURIComponent(currentCategory)}&region=${encodeURIComponent(currentRegion)}&max_results=8`;
            const response = await fetch(url);
            const data = await response.json();

            loadingContainer.style.display = "none";

            if (!response.ok) {
                showError(data.message || "Failed to scout web intelligence nodes.");
                return;
            }

            renderResults(data);
        } catch (err) {
            loadingContainer.style.display = "none";
            showError("Network connection error. Is the CypherLens server running?");
        }
    }

    function renderResults(data) {
        // Render Meta Info
        statusSection.style.display = "block";
        metaTarget.textContent = `"${data.query}"`;
        metaLens.textContent = (data.detected_category || "GENERAL").toUpperCase();
        metaRegion.textContent = data.region_name || "Germany & EU";
        metaNodes.textContent = `${data.items ? data.items.length : 0} Nodes`;
        metaLatency.textContent = `${data.execution_time_ms}ms`;

        // Render Deep Radar Quick Hubs (Pre-Filled Links)
        if (data.deep_links && data.deep_links.length > 0) {
            deepRadarSection.style.display = "block";
            deepRadarContainer.innerHTML = data.deep_links.map(link => `
                <a href="${link.url}" target="_blank" rel="noopener noreferrer" class="radar-hub-card">
                    <div class="hub-info">
                        <h4>${escapeHtml(link.title)}</h4>
                        <span class="hub-badge">${escapeHtml(link.badge || "Pre-Filled Matrix")}</span>
                    </div>
                    <span class="hub-arrow">↗</span>
                </a>
            `).join("");
        }

        // Render Cards
        if (!data.items || data.items.length === 0) {
            resultsGrid.innerHTML = `
                <div class="empty-state" style="grid-column: 1 / -1;">
                    <div class="empty-icon">⚠️</div>
                    <h3>No intelligence nodes matched this search</h3>
                    <p>Try refining your query or switching categories/regions above.</p>
                </div>
            `;
            return;
        }

        resultsGrid.innerHTML = data.items.map((item, idx) => {
            const isPinned = watchlist.some(w => w.url === item.url);
            const specsHtml = item.specs && item.specs.length > 0
                ? `<div class="card-specs">${item.specs.map(s => `<span class="spec-chip">${escapeHtml(s)}</span>`).join("")}</div>`
                : "";

            return `
                <article class="intel-card" data-idx="${idx}">
                    <div>
                        <div class="card-top">
                            <span class="source-badge">${escapeHtml(item.source)}</span>
                            <span class="deal-badge">${escapeHtml(item.badge || "Verified Node")}</span>
                        </div>
                        <h3 class="card-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h3>
                        <p class="card-snippet">${escapeHtml(item.snippet || "Direct intelligence record.")}</p>
                        ${specsHtml}
                    </div>

                    <div>
                        <div class="card-pricing-row">
                            <div class="price-tag">${item.price ? escapeHtml(item.price) : '<span style="font-size:14px;color:var(--text-dim);">Live Fares</span>'}</div>
                            ${item.rating ? `<div class="rating-tag">${escapeHtml(item.rating)}</div>` : ''}
                        </div>

                        <div class="card-actions">
                            <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn-card-action">
                                Open Deal / Route ↗
                            </a>
                            <button class="btn-pin ${isPinned ? 'pinned' : ''}" title="Pin to Watchlist" onclick="togglePin(${idx})">
                                ${isPinned ? '★ Pinned' : '📌 Pin'}
                            </button>
                        </div>
                    </div>
                </article>
            `;
        }).join("");

        // Store last items globally for pinning
        window.lastScoutItems = data.items;
    }

    function showError(msg) {
        resultsGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1; border-color: rgba(239, 68, 68, 0.4);">
                <div class="empty-icon">⚠️</div>
                <h3 style="color: #f87171;">Scout Operation Interrupted</h3>
                <p>${escapeHtml(msg)}</p>
            </div>
        `;
    }

    // Watchlist Management
    window.togglePin = function(idx) {
        if (!window.lastScoutItems || !window.lastScoutItems[idx]) return;
        const item = window.lastScoutItems[idx];
        const existingIdx = watchlist.findIndex(w => w.url === item.url);

        if (existingIdx >= 0) {
            watchlist.splice(existingIdx, 1);
        } else {
            watchlist.push({
                title: item.title,
                url: item.url,
                price: item.price,
                source: item.source,
                timestamp: new Date().toLocaleTimeString()
            });
        }

        localStorage.setItem("cypherlens_watchlist", JSON.stringify(watchlist));
        updateWatchlistUI();
        
        // Update pin button styling
        const pinBtn = document.querySelectorAll(".intel-card")[idx]?.querySelector(".btn-pin");
        if (pinBtn) {
            const isPinned = watchlist.some(w => w.url === item.url);
            pinBtn.className = `btn-pin ${isPinned ? 'pinned' : ''}`;
            pinBtn.innerHTML = isPinned ? '★ Pinned' : '📌 Pin';
        }
    };

    window.removePinnedItem = function(url) {
        watchlist = watchlist.filter(w => w.url !== url);
        localStorage.setItem("cypherlens_watchlist", JSON.stringify(watchlist));
        updateWatchlistUI();
    };

    function updateWatchlistUI() {
        const count = watchlist.length;
        watchlistCountBadge.textContent = count;
        drawerCount.textContent = count;

        if (count === 0) {
            watchlistItemsContainer.innerHTML = '<p class="empty-drawer-msg">No items pinned yet. Click 📌 on any search card to save it here for comparison.</p>';
            return;
        }

        watchlistItemsContainer.innerHTML = watchlist.map(item => `
            <div class="pinned-item-card">
                <h5>${escapeHtml(item.title)}</h5>
                <div class="pinned-item-row">
                    <span style="color: var(--emerald-green); font-weight:700; font-family:var(--font-mono); font-size:13px;">${item.price || 'Deal'}</span>
                    <span style="font-size:11px; color:var(--text-dim);">[${escapeHtml(item.source)}]</span>
                </div>
                <div style="display:flex; gap:8px; margin-top:8px;">
                    <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="btn-card-action" style="padding:4px 8px; font-size:11px;">View ↗</a>
                    <button class="btn-pin" style="padding:4px 8px; font-size:11px;" onclick="removePinnedItem('${escapeHtml(item.url)}')">Remove</button>
                </div>
            </div>
        `).join("");
    }

    // Drawer Toggles
    toggleWatchlistBtn.addEventListener("click", () => {
        watchlistDrawer.classList.add("open");
        drawerOverlay.classList.add("open");
    });

    closeDrawerBtn.addEventListener("click", () => {
        watchlistDrawer.classList.remove("open");
        drawerOverlay.classList.remove("open");
    });

    drawerOverlay.addEventListener("click", () => {
        watchlistDrawer.classList.remove("open");
        drawerOverlay.classList.remove("open");
    });

    clearWatchlistBtn.addEventListener("click", () => {
        watchlist = [];
        localStorage.removeItem("cypherlens_watchlist");
        updateWatchlistUI();
    });

    function escapeHtml(text) {
        if (!text) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
