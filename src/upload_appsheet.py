#!/usr/bin/env python3
"""Upload NGO ranking data to AppSheet spreadsheet (yearly job)."""

import logging
from pathlib import Path
from glob import glob
from os import environ
import pandas as pd
from uploaders.google_sheet import upload_appsheet

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RANKED_FNAME = environ.get("RANKED_NGO_FNAME", "RankedNGOResult")


def run_upload_appsheet() -> None:
    """Upload ranked NGO data to AppSheet."""
    ranked_dfs = [pd.read_csv(f) for f in sorted(glob(str(DATA_DIR / f"{RANKED_FNAME}_*.csv")))]
    
    if not ranked_dfs:
        logger.error("No ranked data found!")
        return
    
    general_info = pd.read_csv(DATA_DIR / "NgoGeneralInfo.csv")
    upload_appsheet(general_info, ranked_dfs)
    logger.info("AppSheet upload completed!")


if __name__ == "__main__":
    run_upload_appsheet()
