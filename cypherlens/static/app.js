/**
 * CypherLens 2.0 Conversational Web Client Application
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatFeed = document.getElementById("chatFeed");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const chatLoading = document.getElementById("chatLoading");
    const resetSessionBtn = document.getElementById("resetSessionBtn");
    
    const regionSelect = document.getElementById("regionSelect");
    const currencySelect = document.getElementById("currencySelect");
    const providerBadge = document.getElementById("providerBadge");

    // Modal Settings
    const openSettingsBtn = document.getElementById("openSettingsBtn");
    const closeSettingsBtn = document.getElementById("closeSettingsBtn");
    const settingsModal = document.getElementById("settingsModal");
    const aiProviderSelect = document.getElementById("aiProviderSelect");
    const apiKeyInput = document.getElementById("apiKeyInput");
    const modelInput = document.getElementById("modelInput");
    const saveConfigBtn = document.getElementById("saveConfigBtn");

    // Watchlist Elements
    const toggleWatchlistBtn = document.getElementById("toggleWatchlistBtn");
    const closeDrawerBtn = document.getElementById("closeDrawerBtn");
    const clearWatchlistBtn = document.getElementById("clearWatchlistBtn");
    const watchlistDrawer = document.getElementById("watchlistDrawer");
    const drawerOverlay = document.getElementById("drawerOverlay");
    const watchlistItemsContainer = document.getElementById("watchlistItems");
    const watchlistCountBadge = document.getElementById("watchlistCount");
    const drawerCount = document.getElementById("drawerCount");

    // Session State
    let sessionId = "session_" + Math.random().toString(36).substring(2, 9);
    let currentRegion = localStorage.getItem("cypherlens_region") || "de";
    let currentCurrency = localStorage.getItem("cypherlens_currency") || "EUR";
    let watchlist = JSON.parse(localStorage.getItem("cypherlens_watchlist") || "[]");

    // Initial controls state
    if (regionSelect) {
        regionSelect.value = currentRegion;
        regionSelect.addEventListener("change", (e) => {
            currentRegion = e.target.value;
            localStorage.setItem("cypherlens_region", currentRegion);
        });
    }

    if (currencySelect) {
        currencySelect.value = currentCurrency;
        currencySelect.addEventListener("change", (e) => {
            currentCurrency = e.target.value;
            localStorage.setItem("cypherlens_currency", currentCurrency);
        });
    }

    // Load AI Config Status
    loadConfig();
    updateWatchlistUI();

    // Prompt Chips in Initial Card
    document.querySelectorAll(".prompt-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const promptText = chip.getAttribute("data-prompt");
            if (promptText) {
                chatInput.value = promptText;
                sendMessage(promptText);
            }
        });
    });

    // Auto-resize textarea and handle Enter
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    // Submit Chat Form
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (text) {
            sendMessage(text);
        }
    });

    // Reset Conversation
    resetSessionBtn.addEventListener("click", async () => {
        try {
            await fetch("/api/chat/reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId })
            });
            chatFeed.innerHTML = `
                <div class="assistant-message glass-panel">
                    <div class="msg-header">
                        <span class="agent-badge">📡 CYPHERLENS RADAR ONLINE</span>
                        <span class="agent-time">New Session</span>
                    </div>
                    <div class="msg-body">
                        <p>Memory cleared. What product, flight route, or comparison would you like to scout next?</p>
                    </div>
                </div>
            `;
        } catch (err) {
            console.error(err);
        }
    });

    async function sendMessage(userText) {
        // Append user bubble
        appendUserMessage(userText);
        chatInput.value = "";
        chatLoading.style.display = "flex";
        scrollToBottom();

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userText,
                    session_id: sessionId,
                    region: currentRegion,
                    currency: currentCurrency
                })
            });

            chatLoading.style.display = "none";
            const data = await response.json();

            if (!response.ok) {
                appendAssistantMessage("⚠️ **Error**: " + (data.message || "Could not process message."));
                return;
            }

            appendAssistantResponse(data);
        } catch (err) {
            chatLoading.style.display = "none";
            appendAssistantMessage("⚠️ **Network Error**: Unable to reach CypherLens server.");
        }
    }

    function appendUserMessage(text) {
        const div = document.createElement("div");
        div.className = "user-message";
        div.textContent = text;
        chatFeed.appendChild(div);
        scrollToBottom();
    }

    function appendAssistantMessage(rawMarkdown) {
        const div = document.createElement("div");
        div.className = "assistant-message glass-panel";
        div.innerHTML = `
            <div class="msg-header">
                <span class="agent-badge">📡 CYPHERLENS</span>
                <span class="agent-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="msg-body">
                ${marked.parse(rawMarkdown)}
            </div>
        `;
        chatFeed.appendChild(div);
        scrollToBottom();
    }

    function appendAssistantResponse(data) {
        const div = document.createElement("div");
        div.className = "assistant-message glass-panel";
        const timeStr = new Date().toLocaleTimeString();

        const struct = data.structured_data || {};
        let extraHtml = "";

        // 1. Clarification Questions Pills
        if (data.type === "clarification" && struct.questions) {
            extraHtml += `
                <div class="clarify-card">
                    ${struct.questions.map(q => `
                        <div class="clarify-group">
                            <div class="clarify-label">${escapeHtml(q.label)}</div>
                            <div class="clarify-options">
                                ${q.options.map(opt => `
                                    <button class="btn-option-pill" onclick="sendQuickAnswer('${escapeHtml(opt)}')">${escapeHtml(opt)}</button>
                                `).join("")}
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;
        }

        // 2. Deep Pre-Filled Matrix Links
        if (struct.deep_links && struct.deep_links.length > 0) {
            extraHtml += `
                <div style="margin-top: 18px;">
                    <div style="font-size: 13px; font-weight: 700; color: var(--amber-glow); margin-bottom: 8px;">⚡ 1-Click Pre-Filled Direct Hubs:</div>
                    <div class="deep-radar-grid">
                        ${struct.deep_links.map(dl => `
                            <a href="${dl.url}" target="_blank" rel="noopener noreferrer" class="radar-hub-card" style="padding:10px 14px;">
                                <div class="hub-info">
                                    <h4 style="font-size:13px;">${escapeHtml(dl.title)}</h4>
                                    <span class="hub-badge">${escapeHtml(dl.badge || "Direct")}</span>
                                </div>
                                <span class="hub-arrow">↗</span>
                            </a>
                        `).join("")}
                    </div>
                </div>
            `;
        }

        div.innerHTML = `
            <div class="msg-header">
                <span class="agent-badge">📡 CYPHERLENS INTEL</span>
                <span class="agent-time">${timeStr}</span>
            </div>
            <div class="msg-body">
                ${marked.parse(data.content || "")}
                ${extraHtml}
            </div>
        `;

        chatFeed.appendChild(div);
        scrollToBottom();
    }

    // Global quick option click
    window.sendQuickAnswer = function(answerText) {
        chatInput.value = answerText;
        sendMessage(answerText);
    };

    function scrollToBottom() {
        chatFeed.scrollTop = chatFeed.scrollHeight;
    }

    // BYOK Config Modal
    async function loadConfig() {
        try {
            const r = await fetch("/api/config");
            if (r.ok) {
                const cfg = await r.json();
                aiProviderSelect.value = cfg.provider || "zero_key";
                if (cfg.has_api_key) {
                    providerBadge.textContent = `AI: ${cfg.provider.toUpperCase()} (Connected)`;
                    providerBadge.style.color = "var(--cyan-glow)";
                } else {
                    providerBadge.textContent = `AI: Zero-Key (Free)`;
                }
            }
        } catch (err) {
            console.error(err);
        }
    }

    openSettingsBtn.addEventListener("click", () => {
        settingsModal.style.display = "flex";
    });

    closeSettingsBtn.addEventListener("click", () => {
        settingsModal.style.display = "none";
    });

    settingsModal.addEventListener("click", (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = "none";
        }
    });

    saveConfigBtn.addEventListener("click", async () => {
        const provider = aiProviderSelect.value;
        const apiKey = apiKeyInput.value.trim();
        const model = modelInput.value.trim();

        try {
            const r = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    provider: provider,
                    api_key: apiKey,
                    model: model,
                    default_currency: currentCurrency,
                    default_region: currentRegion
                })
            });

            if (r.ok) {
                settingsModal.style.display = "none";
                apiKeyInput.value = "";
                loadConfig();
            }
        } catch (err) {
            alert("Failed to save settings.");
        }
    });

    // Watchlist Drawer
    function updateWatchlistUI() {
        const count = watchlist.length;
        watchlistCountBadge.textContent = count;
        drawerCount.textContent = count;

        if (count === 0) {
            watchlistItemsContainer.innerHTML = '<p class="empty-drawer-msg">No items pinned yet. Pinned products and comparisons will appear here.</p>';
            return;
        }

        watchlistItemsContainer.innerHTML = watchlist.map(item => `
            <div class="pinned-item-card">
                <h5>${escapeHtml(item.title)}</h5>
                <div class="pinned-item-row">
                    <span style="color: var(--emerald-green); font-weight:700; font-family:var(--font-mono); font-size:13px;">${item.price || 'Deal'}</span>
                    <span style="font-size:11px; color:var(--text-dim);">[${escapeHtml(item.source)}]</span>
                </div>
            </div>
        `).join("");
    }

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
