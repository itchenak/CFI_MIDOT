# CFI MIDOT — Israeli NGO Financial Ranking

A tool for analyzing and ranking Israeli NGOs based on their financial reports.

## Overview

CFI MIDOT scrapes financial data from [GuideStar Israel](https://www.guidestar.org.il/) and government sources, calculates financial health rankings, and publishes results to Google Sheets.

### Pipeline Stages

| Stage | Description |
|-------|-------------|
| **Scrape** | Downloads registered NGO IDs from data.gov.il and scrapes financial reports |
| **Rank** | Calculates rankings based on growth, balance, and income stability |
| **Upload** | Publishes ranked results to Google Sheets |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (optional)
- Google Cloud service account with Sheets API access

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/CFI_MIDOT.git
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
```

### Using CLI Commands (after `pip install -e .`)

```bash
cfi-scrape   # Run scraping
cfi-rank     # Run ranking
cfi-upload   # Run upload
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

# Run full pipeline
docker-compose up pipeline
```

---

## GitHub Actions CI/CD

The repository includes a GitHub Actions workflow (`.github/workflows/ngo-ranking-pipeline.yml`) that runs:

1. **Build** — Creates Docker image
2. **Scrape** — Downloads and scrapes NGO data
3. **Rank** — Calculates financial rankings
4. **Upload** — Publishes to Google Sheets

### Required Secrets

Add these to your repository settings (Settings → Secrets → Actions):

| Secret | Description |
|--------|-------------|
| `RANKED_NGO_FNAME` | Output filename for rankings |
| `PUBLIC_SPREADSHEET_ID` | Target Google Sheet ID |
| `GOOGLE_CREDENTIALS_JSON` | Service account JSON |

---

## Project Structure

```
CFI_MIDOT/
├── src/
│   ├── scrape.py              # Stage 1: Data collection
│   ├── rank.py                # Stage 2: Ranking calculation
│   ├── upload.py              # Stage 3: Google Sheets upload
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