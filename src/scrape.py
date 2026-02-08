#!/usr/bin/env python3
"""
Scrape NGO financial data from GuideStar and government APIs.

This module downloads registered NGO IDs and scrapes their financial information.
"""

import os
import logging
from pathlib import Path
from scrapers.api_interaction import download_registered_ngos_ids

logger = logging.getLogger(__name__)

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

FINANCIAL_REPORT_FNAME = "NgoFinanceInfo"


def scrape_ngo_finance(ngos_ids: list[int]) -> None:
    """Scrape financial data for the given NGO IDs using Scrapy."""
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
    from scrapers.cfi_midot_scrapy.spiders.guide_star_spider import GuideStarSpider

    process = CrawlerProcess(get_project_settings())
    process.crawl(GuideStarSpider, ngos_ids)
    process.start()


def run_scrape() -> None:
    """Main entry point for scraping NGO data."""
    logger.info("Starting NGO data scraping...")
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory: {DATA_DIR}")
    
    # Download latest registered NGOs from https://data.gov.il/dataset/moj-amutot
    logger.info("Downloading registered NGO IDs...")
    ngos_ids = download_registered_ngos_ids()
    logger.info(f"Found {len(ngos_ids)} registered NGOs")
    
    # Scrape NGO financial data
    logger.info("Scraping NGO financial data...")
    scrape_ngo_finance(ngos_ids)
    
    logger.info("Scraping completed successfully!")


if __name__ == "__main__":
    run_scrape()
