# SyncLM Studio — Interactive Web App & TechDocs Sync Pipeline for NotebookLM

> **SyncLM Studio** is a dual-purpose system designed for network security architects, sales engineers, and enterprise developers. It pairs an **interactive, bespoke React web console** with a **modular documentation scraping & ingestion pipeline** that syncs multi-vendor technical documentation directly into Google Docs for seamless ingestion into **Google NotebookLM**.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       SyncLM Studio Web Console       |
                      |   (React + Bespoke CSS Design System) |
                      +-------------------+-------------------+
                                          |
                        REST Endpoints & SSE Log Stream
                                          v
                      +-------------------+-------------------+
                      |      FastAPI Backend Controller       |
                      |          (Python 3.11+)               |
                      +-------------------+-------------------+
                                          |
                     +--------------------+--------------------+
                     |                                         |
                     v                                         v
        +----------------------------+            +----------------------------+
        |  Scraper & Extraction      |            |  Deduplication Engine      |
        |  (trafilatura + bs4 + md)  |            |  (SHA-256 in hashes.json)  |
        +-------------+--------------+            +-------------+--------------+
                      |                                         |
                      +--------------------+--------------------+
                                           |
                                           v
                             +-------------+--------------+
                             | Google Docs / Drive API    |
                             | (Batch Updates & Chunks)   |
                             +-------------+--------------+
                                           |
                                           v
                             +-------------+--------------+
                             |     Google NotebookLM      |
                             |  (50-Source Grounding)     |
                             +----------------------------+
```

---

## Key Features

### 1. Interactive Studio Configurator (No Tailwind, Pure Bespoke CSS)
- **High-Density Enterprise Console**: Designed with a cybersecurity palette inspired by Palo Alto Networks Strata Cloud Manager and Cortex XSIAM.
- **5 Technology Verticals**:
  - `sase`: Prisma Access, Cloud SWG, ZTNA, CASB
  - `browser`: Prisma Access Browser, Island Enterprise Browser, Chromium Isolation
  - `ngfw`: Next-Gen Firewall, PAN-OS SP3 architecture, VM-Series, CN-Series
  - `secops`: Cortex XDR, XSOAR, XSIAM Autonomous SOC
  - `cloud`: Prisma Cloud, CNAPP, CSPM, CWPP
- **Multi-Vendor & Competitive Landscape**:
  - Primary: **Palo Alto Networks (PANW Core)**
  - Competitors: **Zscaler**, **Netskope**, **Island**, **Cloudflare One**, **Fortinet**
- **Content Type Filters**: Architecture Guides, Release Notes & Known Issues, pan.dev & OpenAPI Specs, Competitive Battlecards.

### 2. NotebookLM Budget & Slot Estimator
- Dynamically estimates total word counts and token limits.
- Evaluates consolidated Google Doc target allocation against **NotebookLM's 50-source slot limit** and **500,000-word per source limit**.
- Real-time visual progress bars with green/amber/red status alerts.

### 3. Automated Ingestion & Normalization Engine
- **Primary Extraction**: High-fidelity boiler-plate stripping with `trafilatura`.
- **Fallback Extraction**: DOM cleanup and table extraction with `BeautifulSoup4` + `markdownify`.
- **Deduplication**: SHA-256 content hashing in `data/hashes.json` skips unchanged articles and saves Google Docs API quota.
- **Structured Grounding Headers**:
  ```markdown
  # [VENDOR: PANW] [TECH: SASE] Document Title
  - Source: <URL>
  - Synced: <TIMESTAMP>
  - Doc Type: <DOC_TYPE>
  ---
  ```

### 4. Google Docs API Batch Updates with Safety Chunking
- Service Account authentication (`GCP_SERVICE_ACCOUNT_JSON` or `GCP_SA_KEY_B64`).
- Reads current document length (`endIndex`).
- Clears stale content (`deleteContentRange: 1 to endIndex - 1`).
- Sequentially inserts structured Markdown in safe 45KB payload chunks.
- Supports offline **`--dry-run` simulation mode**.

### 5. Live CRT / ANSI Terminal Emulator
- Real-time Server-Sent Events (SSE) streaming at `/api/sync/stream`.
- Visual colored log level badges (`INFO`, `SUCCESS`, `WARN`, `ERROR`).
- Controls: Pause/resume autoscroll, download log file, clear screen.

### 6. GitHub Actions CI/CD Integration
- Weekly automated cron (`cron: '0 4 * * 1'`).
- Parameterized `workflow_dispatch` trigger supporting `technology`, `vendor`, `doc_type`, and `dry_run`.

---

## Quickstart

### 1. Launch Everything via `run.sh`
```bash
./run.sh
```
This automatically sets up the Python virtual environment, builds the frontend, and starts the FastAPI server at `http://localhost:8000`.

### 2. Standalone CLI Ingestion
```bash
# Run dry-run simulation for SASE PANW docs
python scripts/run_sync.py --tech sase --vendor panw --dry-run

# Run full sync across all verticals
python scripts/run_sync.py --tech all --vendor all
```

### 3. Run Automated Tests
```bash
pytest
```
Runs 16 unit and integration tests covering sources filtering, budget calculation, content hashing, document normalizer, Google Docs chunking, and FastAPI endpoints.

---

## Configuring Google Cloud Credentials

To enable live writes to your target Google Docs:
1. Create a Service Account in the [Google Cloud Console](https://console.cloud.google.com/) with **Google Docs API** and **Google Drive API** enabled.
2. Download the JSON key file.
3. Configure your environment in `.env`:
   ```bash
   GOOGLE_APPLICATION_CREDENTIALS="path/to/service_account.json"
   ```
4. Verify your credentials using the included utility:
   ```bash
   python scripts/verify_credentials.py
   ```
5. Share each target Google Doc with the printed Service Account email as an **Editor**.

---

## Project Structure

```
panw-techdocs-crwlr/
├── .github/workflows/
│   └── sync-docs.yml              # Parameterized scheduled GitHub Action
├── app/                           # FastAPI Application & API Server
│   ├── main.py                    # REST API routes & SSE log streamer
│   ├── schemas.py                 # Pydantic schemas
│   └── config.py                  # Server configuration
├── engine/                        # Core Documentation & Sync Engine
│   ├── sources.py                 # Multi-vendor source catalog & budget math
│   ├── scraper.py                 # Trafilatura + BS4 fallback extractors
│   ├── normalizer.py              # Markdown cleaner & metadata header injector
│   ├── dedup.py                   # SHA-256 content hashing & cache store
│   ├── gdocs.py                   # Google Docs API batch update client
│   └── pipeline.py                # Pipeline orchestrator & event bus
├── frontend/                      # Bespoke React Dashboard (No Tailwind)
│   ├── src/
│   │   ├── styles/tokens.css      # Enterprise CSS tokens (PANW orange, slate)
│   │   ├── styles/main.css        # Modern layout, grids, cards, buttons
│   │   ├── styles/terminal.css    # Monospace CRT terminal emulator
│   │   ├── components/            # UI components (Selectors, Meters, Terminal)
│   │   ├── App.tsx                # Main dashboard coordinator
│   │   └── types/                 # TypeScript interfaces
│   └── dist/                      # Pre-built distribution bundle
├── data/
│   ├── doc_sources.json           # Catalog of enterprise documentation targets
│   ├── targets.json               # Google Doc IDs mapped to topics
│   └── hashes.json                # SHA-256 deduplication cache
├── scripts/
│   ├── run_sync.py                # CLI sync tool
│   └── verify_credentials.py      # GCP Service Account verification utility
├── tests/                         # Pytest test suite (16 tests)
├── requirements.txt               # Python dependencies
├── run.sh                         # Single-command launcher
└── pytest.ini                     # Pytest configuration
```

---

## License
MIT License.
