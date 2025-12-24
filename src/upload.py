#!/usr/bin/env python3
"""
Upload NGO ranking data to Google Spreadsheets.

This module publishes the ranked NGO data to Google Sheets.
"""

import os
import logging
from pathlib import Path
from glob import glob
import pandas as pd
from uploaders.google_sheet import upload_spread_sheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

FINANCIAL_REPORT_FNAME = "NgoFinanceInfo"
RANKED_FNAME = os.environ.get("RANKED_NGO_FNAME", "RankedNGOResult")


def load_ranked_data() -> list[pd.DataFrame]:
    """Load all ranked NGO data from CSV files."""
    ranked_dfs = []
    ranked_files = sorted(glob(str(DATA_DIR / f"{RANKED_FNAME}_*.csv")))
    
    for ranked_file in ranked_files:
        logger.info(f"Loading ranked data from {ranked_file}")
        ranked_df = pd.read_csv(ranked_file)
        ranked_dfs.append(ranked_df)
    
    return ranked_dfs


def run_upload(ranked_dfs: list[pd.DataFrame] | None = None) -> None:
    """
    Main entry point for uploading ranked NGO data to Google Sheets.
    
    Args:
        ranked_dfs: Optional list of ranked DataFrames. If not provided,
                   will load from CSV files.
    """
    logger.info("Starting upload to Google Sheets...")
    logger.info(f"Data directory: {DATA_DIR}")
    
    # Load ranked data if not provided
    if ranked_dfs is None:
        ranked_dfs = load_ranked_data()
    
    if not ranked_dfs:
        logger.error("No ranked data found to upload!")
        return
    
    # Load general NGO info
    general_info_path = DATA_DIR / "NgoGeneralInfo.csv"
    logger.info(f"Loading general NGO info from {general_info_path}")
    ngo_general_info = pd.read_csv(general_info_path)
    
    # Upload to Google Sheets
    logger.info("Uploading to Google Sheets...")
    upload_spread_sheet(ngo_general_info, ranked_dfs)
    
    logger.info("Upload completed successfully!")


if __name__ == "__main__":
    run_upload()
