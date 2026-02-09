#!/usr/bin/env python3
"""
Rank NGOs based on their financial data.

This module loads financial reports and calculates rankings for NGOs.
"""

import os
import logging
from pathlib import Path
import pandas as pd
from ranking.ranking_service import rank_ngos

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


def run_rank() -> list[pd.DataFrame]:
    """
    Main entry point for ranking NGOs.
    
    Returns:
        List of DataFrames containing ranked NGO data for each year.
    """
    logger.info("Starting NGO ranking process...")
    logger.info(f"Data directory: {DATA_DIR}")
    
    # Load yearly financial reports for each NGO
    financial_path = DATA_DIR / f"{FINANCIAL_REPORT_FNAME}.csv"
    logger.info(f"Loading financial data from {financial_path}")
    financial_df = pd.read_csv(financial_path)
    
    # Sort the financial reports by year and group by report_year
    financial_df = financial_df.sort_values(by="report_year", ascending=True).groupby(
        "report_year"
    )
    
    # Rank the NGOs for each year
    logger.info("Calculating NGO rankings...")
    ranked_dfs = rank_ngos(financial_df)
    
    # Save the ranks for each year to a separate csv file
    for ranked_df in ranked_dfs:
        year = ranked_df["report_year"].iloc[0]
        output_path = DATA_DIR / f"{RANKED_FNAME}_{year}.csv"
        ranked_df.to_csv(output_path, index=False)
        logger.info(f"Saved rankings for year {year} to {output_path}")
    
    logger.info("Ranking completed successfully!")
    return ranked_dfs


if __name__ == "__main__":
    run_rank()
