# SyncLM Portal — Serverless TechDocs & Competitive Intelligence for NotebookLM

> **SyncLM Portal** is a zero-infrastructure, 100% serverless technical documentation hub. Powered by a headless **GitHub Actions cron runner** and hosted on **GitHub Pages**, it compiles multi-vendor security documentation digests directly for **Google NotebookLM** ingestion (via your local `Google Drive for Desktop` mount) and provides 1-click clipboard bridges for **Work Agents** and **Corporate Gemini**.

---

## System Architecture

```
                    +--------------------------------------------+
                    |           GitHub Actions (Weekly)          |
                    |     cron: '0 4 * * 0' (Sundays 04:00 UTC)  |
                    +---------------------+----------------------+
                                          |
                      Runs scripts/build_portal.py (Python 3.11)
                                          |
                                          v
                    +---------------------+----------------------+
                    |       Static Documentation Artifacts       |
                    |    (public/data/*.md + bundle.json)        |
                    +---------------------+----------------------+
                                          |
                              Deploys via actions/deploy-pages
                                          |
                                          v
                    +---------------------+----------------------+
                    |     SyncLM Portal (GitHub Pages Site)      |
                    |         Bespoke Obsidian Web UI            |
                    +---------------------+----------------------+
                                          |
                 +------------------------+------------------------+
                 |                                                 |
                 v                                                 v
  +-------------------------------+              +-------------------------------+
  |   ⬇ Download .md (PIN Gated)  |              | 📋 Copy for Work Agent /      |
  | (Saves to ~/GoogleDrive/...)  |              | ✨ Copy Corporate Gemini      |
  +---------------+---------------+              +-------------------------------+
                  |
                  v
  +-------------------------------+
  |       Google NotebookLM       |
  |  (Automatic local file sync)  |
  +-------------------------------+
```

---

## Key Capabilities

### 1. Zero Infrastructure & Zero SecOps Friction
- **No Google Cloud Console Project**: Zero service accounts (`*@*.iam.gserviceaccount.com`), zero OAuth client IDs, zero DLP alarms.
- **Sanctioned Local Ingestion**: Downloaded `.md` files are saved directly into your enterprise-managed `Google Drive for Desktop` virtual volume (`~/GoogleDrive/My Drive/...`), making them immediately available for NotebookLM without touching restricted external APIs.

### 2. High-Density Obsidian Web Portal (No Tailwind)
- **Crafted Design System**: Built with pure semantic HTML5, native CSS Custom Properties, and zero framework bloat.
- **Obsidian Dark Palette**: Carbon backgrounds (`#08090D`, `#0F1118`), Palo Alto Networks electric amber (`#FF5B26`), and sync cyan (`#00F2FE`).
- **Precision Typography**: `Plus Jakarta Sans` for headers paired with `JetBrains Mono` for telemetry and word counts.
- **Instant Client-Side Filtering**: Real-time search across titles, descriptions, vendors, and tags with keyboard shortcut (`/` to focus).

### 3. Dual Clipboard Bridges
- **`📋 Copy for Work Agent`**: Copies raw normalized Markdown directly to your clipboard with toast confirmation.
- **`✨ Copy Corporate Gemini Prompt`**: Wraps the documentation inside an enterprise Lead Security Architect prompt, ready to paste into Corporate Gemini or Claude for immediate technical analysis.

### 4. Client-Side Security PIN Gate
- Download triggers prompt for a 4-to-8 digit numeric Security PIN.
- Verified in-browser via Web Cryptography API (`crypto.subtle.digest('SHA-256', ...)`).
- Session authorization is cached in `sessionStorage` so you only need to enter the PIN once per session.
- **Default PIN**: `2026` (SHA-256: `158a323a7ba44870f23d96f1516dd70aa48e9a72db4ebb026b0a89e212a208ab`).

---

## How to Customize Your Security PIN

To generate a new hash for your desired PIN:

```bash
python3 -c "import hashlib; pin='YOUR_NEW_PIN'; print(hashlib.sha256(pin.encode()).hexdigest())"
```

Copy the 64-character output and replace `ACCESS_PIN_HASH` in `public/index.html`:

```javascript
const ACCESS_PIN_HASH = "your_computed_sha256_hash_here";
```

The plaintext PIN is never committed to Git.

---

## Directory Layout

```text
synclm-portal/
├── .github/workflows/
│   └── publish_digests.yml       # Headless weekly cron & GitHub Pages deployer
├── config/
│   └── sources.json              # Canonical multi-vendor target taxonomy
├── scripts/
│   └── build_portal.py           # Ingestion, normalization, & bundle generator
├── public/
│   ├── data/
│   │   ├── .gitkeep              # Data directory placeholder
│   │   ├── *.md                  # Individual generated Markdown digests
│   │   └── bundle.json           # Compiled catalog & full markdown bodies
│   └── index.html                # Bespoke obsidian web portal
├── requirements.txt              # Minimal build dependencies
├── .gitignore                    # Git exclusions
└── README.md                     # Documentation
```

---

## Running Locally

To build the digests and preview the static portal locally:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Scrape and generate digests
python scripts/build_portal.py

# 3. Serve the portal locally
python3 -m http.server 8080 --directory public
```

Open **`http://localhost:8080`** in your browser. (Default PIN: `2026`).

---

## GitHub Pages Deployment

1. Push this repository to GitHub.
2. Go to **Settings** > **Pages**.
3. Under **Build and deployment**, set **Source** to **GitHub Actions**.
4. The workflow in `.github/workflows/publish_digests.yml` will automatically build and publish the portal every Sunday at 04:00 UTC, or whenever you click **Run workflow** in the Actions tab.
