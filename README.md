# CFI MIDOT — Israeli NGO Financial Ranking

A tool for analyzing and ranking Israeli NGOs based on their financial reports.

## Overview

CFI MIDOT scrapes financial data from [GuideStar Israel](https://www.guidestar.org.il/) and government sources, calculates financial health rankings, and publishes results to Google Sheets.

### Pipeline Stages

| Stage | Description |
|-------|-------------|
| **Scrape** | Downloads registered NGO IDs from data.gov.il and scrapes financial reports |
| **Rank** | Calculates rankings based on growth, balance, and income stability |
| **Upload** | Publishes ranked results to Google Sheets (weekly) |
| **Upload AppSheet** | Publishes rankings to AppSheet (yearly, 2 years prior) |
| **Proper Management Check** | Compares current proper management status to a published CSV and emails changes |

### Published Results

The ranking data is published to:

📊 **[NGOs Ranking - מדד האיתנות הפיננסית (Google Sheets)](https://docs.google.com/spreadsheets/d/1eI2uTWCuE24f6SXdHyVQG09iJbOkymXHSTJnA6M6jHU/edit?usp=sharing)** — Updated weekly

📱 **[NGOs Ranking - מדד האיתנות הפיננסית (AppSheet)](https://midot.org.il/ngos-ranking)** — Updated yearly

---

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)
- Google Cloud service account with Sheets API access

### Installation

```bash
# Clone the repository
git clone https://github.com/itchenak/CFI_MIDOT.git
cd CFI_MIDOT

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Configuration

Set the following environment variables (or create a `.env` file):

```bash
# File naming
export RANKED_NGO_FNAME="RankedNGOResult"

# Google Sheets IDs
export PUBLIC_SPREADSHEET_ID="your_spreadsheet_id"

# Google credentials (JSON string)
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'

# Proper management change notifications (Gmail SMTP)
export GMAIL_SMTP_USER="you@gmail.com"
export GMAIL_SMTP_PASSWORD="your_app_password"
export EMAIL_FROM="you@gmail.com"
export EMAIL_TO="recipient@example.com"
export REMOTE_PROPER_MANAGEMENT_URL="https://raw.githubusercontent.com/itchenak/CFI_MIDOT/refs/heads/main/data/NgoProperManagement.csv"
```

---

## Usage

### Run Individual Stages

```bash
# Navigate to src directory
cd src

# Scrape NGO data
python scrape.py

# Rank NGOs
python rank.py

# Upload to Google Sheets
python upload.py

# Upload to AppSheet (yearly job)
python upload_appsheet.py

# Proper management status check + email notification
python check_proper_management.py
```

### Using CLI Commands (after `pip install -e .`)

```bash
cfi-scrape           # Run scraping
cfi-rank             # Run ranking
cfi-upload           # Run upload
cfi-upload-appsheet  # Run AppSheet upload
```

---

## Docker

### Build and Run

```bash
# Build image
docker build -t cfi-midot .

# Run full pipeline
docker run --env-file .env -v $(pwd)/data:/app/data cfi-midot

# Run individual stages
docker run --env-file .env -v $(pwd)/data:/app/data cfi-midot python scrape.py
docker run --env-file .env -v $(pwd)/data:/app/data cfi-midot python rank.py
docker run --env-file .env -v $(pwd)/data:/app/data cfi-midot python upload.py
```

### Docker Compose

```bash
# Run specific service
docker-compose up scrape
docker-compose up rank
docker-compose up upload
docker-compose up upload-appsheet

# Or run all stages sequentially
docker-compose up scrape && docker-compose up rank && docker-compose up upload
```

---

## GitHub Actions CI/CD

The repository includes GitHub Actions workflows:

### Main Pipeline (`.github/workflows/ngo-ranking-pipeline.yml`)

Runs weekly and on push:

1. **Build** — Creates Docker image
2. **Scrape** — Downloads and scrapes NGO data
3. **Rank** — Calculates financial rankings
4. **Upload** — Publishes to Google Sheets

### Proper Management Notifications

Run `python src/check_proper_management.py` after scraping. It compares the local
`data/NgoProperManagement.csv` to the CSV at `REMOTE_PROPER_MANAGEMENT_URL` and
emails any gained/lost proper management changes via Gmail SMTP.

### AppSheet Upload (`.github/workflows/appsheet-yearly-upload.yml`)

Runs yearly on January 1st — uploads rankings (2 years prior) to AppSheet.

### Required Secrets

Add these to your repository settings (Settings → Secrets → Actions):

| Secret | Description |
|--------|-------------|
| `RANKED_NGO_FNAME` | Output filename for rankings |
| `PUBLIC_SPREADSHEET_ID` | Target Google Sheet ID |
| `APPSHEET_SPREADSHEET_ID` | AppSheet Google Sheet ID |
| `GOOGLE_CREDENTIALS_JSON` | Service account JSON |
| `GMAIL_SMTP_USER` | Gmail address used for SMTP |
| `GMAIL_SMTP_PASSWORD` | Gmail app password for SMTP |
| `EMAIL_FROM` | Sender email address |
| `EMAIL_TO` | Recipient email address(es) |
| `REMOTE_PROPER_MANAGEMENT_URL` | URL to the published proper management CSV |

---

## Project Structure

```
CFI_MIDOT/
├── src/
│   ├── scrape.py              # Stage 1: Data collection
│   ├── rank.py                # Stage 2: Ranking calculation
│   ├── upload.py              # Stage 3: Google Sheets upload
│   ├── upload_appsheet.py     # Stage 4: AppSheet upload
│   ├── check_proper_management.py # Proper management change notifications
│   ├── scrapers/              # Scrapy spiders and API clients
│   ├── ranking/               # Ranking algorithms
│   └── uploaders/             # Google Sheets integration
├── data/                      # Input/output CSV files
├── .github/workflows/         # CI/CD pipelines
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── setup.py
```

---

## Ranking Methodology

NGOs are scored on three financial metrics:

| Metric | Weight | Description |
|--------|--------|-------------|
| **Growth** | 40% | Year-over-year turnover growth |
| **Balance** | 40% | Annual surplus/deficit ratio |
| **Stability** | 20% | Diversification of income sources |

Rankings are calculated per turnover category and compared against benchmarks.

---

## Data Sources

- **[data.gov.il](https://data.gov.il/dataset/moj-amutot)** — Official registry of Israeli NGOs
- **[GuideStar Israel](https://www.guidestar.org.il/)** — Detailed financial reports

---

## License

MIT License — see [LICENSE](LICENSE) for details.