# 🎯 CypherLens (Real-Time Web Search Simplifier & Price Radar)

**CypherLens** is a lightweight, 100% free search simplifier and price radar. It takes natural language prompts and instantly scouts products, flights, tech deals, and Amazon items, stripping away SEO blog spam and presenting clean, clickable cards with real-time prices and direct links.

---

## ⚡ Key Capabilities

- 💰 **100% Free & Zero API Keys**: No OpenAI keys, SerpAPI, or subscription fees required.
- 📦 **Amazon & Shopping Lens**: Instant prices, star ratings, Prime tags, and clean direct product links.
- ✈️ **Flight Radar**: Parses routes, dates, and builds 1-click **Google Flights**, **Skyscanner**, and **Kayak** comparison matrix links with live fare estimates.
- 💻 **Tech & Hardware Lens**: Parses GPUs (e.g. RTX 4060/4070/4080), RAM, SSD, and budget limits across retailers (Amazon, Best Buy, Newegg, B&H).
- 🌐 **Ad-Free Web Scout**: Strips sponsored ads and delivers direct, actionable intelligence.
- 🖥️ **Two Sleek Modes**:
  1. **Terminal TUI Mode**: Interactive, modern CLI with **native clickable hyperlinks** (`Ctrl/Cmd + Click`).
  2. **Web Radar UI**: 1-click modern dashboard with category filters and pinned deal watchlists.

---

## 🚀 Quick Start & Installation

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/Pranav-14/cypherlens.git
cd cypherlens

# Install dependencies
pip install -r requirements.txt

# (Optional) Install CLI globally in editable mode
pip install -e .
```

---

## 💻 CLI Usage

### Interactive Terminal Mode (REPL)
Simply run without arguments to enter the CypherLens interactive search terminal:
```bash
python -m cypherlens.cli
# or if installed via pip:
cypherlens
```

### Direct Search Prompts
```bash
# Tech & Laptops
cypherlens "RTX 4060 laptop under 1000"

# Flights & Travel
cypherlens "flights from NYC to Tokyo next month"

# Amazon Products & Deals
cypherlens "Sony WH-1000XM5 headphones on amazon"

# Force Specific Category Lens
cypherlens --category flight "SFO to London"
cypherlens --category amazon "Mechanical keyboard under 50"

# Export Results to Markdown or JSON
cypherlens "best 4k OLED monitors" --export monitors.md
cypherlens "MacBook M3 Air deals" --json-output
```

---

## 🌐 Web Radar UI Mode

Launch the local Web Dashboard with a single flag:

```bash
cypherlens --web
# or
python -m cypherlens.cli --web
```
This automatically opens **`http://localhost:8000`** in your browser.

---

## 📂 Project Architecture

```
cypherlens/
├── cypherlens/
│   ├── __init__.py
│   ├── cli.py                  # Rich terminal UI with clickable URLs & REPL
│   ├── web_app.py              # FastAPI server & endpoints
│   ├── static/                 # Modern web UI (HTML5, CSS3, JS)
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   └── engines/                # Modular intelligence lenses
│       ├── base.py             # Data models (SearchResultItem, LensResponse)
│       ├── query_parser.py     # Intent classification & regex entity extraction
│       ├── search_client.py    # Resilient zero-cost search engine
│       ├── amazon_lens.py      # Amazon direct price & link parser
│       ├── flight_lens.py      # Route intelligence & Google Flights deep matrix
│       ├── tech_lens.py        # Hardware specs & deal aggregator
│       ├── general_lens.py     # General web simplifier
│       └── orchestrator.py     # Central intelligence dispatcher
├── pyproject.toml              # Pip build & CLI entrypoints
├── requirements.txt            # Dependency list
├── .gitignore
└── README.md
```

---

## 🛡️ License

MIT License. Free for personal, non-commercial, and open-source use.
