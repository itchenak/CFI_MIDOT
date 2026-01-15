"""
Track changes in NGO proper management certificate status.

Compares current scraped data against a previously published CSV
and sends email notifications via Gmail SMTP when changes are detected.
"""

import logging
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

PROPER_MANAGEMENT_FNAME = "NgoProperManagement.csv"
GUIDESTAR_ORG_URL = "https://www.guidestar.org.il/organization"

class ProperManagementChangeType(str, Enum):
    GAINED = "gained"
    LOST = "lost"


@dataclass
class ProperManagementChange:
    """Represents a change in an NGO's proper management status."""
    ngo_id: int
    ngo_name: str
    change_type: ProperManagementChangeType
    
    @property
    def guidestar_url(self) -> str:
        return f"{GUIDESTAR_ORG_URL}/{self.ngo_id}"


def load_proper_management_csv(filepath: Path) -> Optional[pd.DataFrame]:
    """Load proper management CSV file if it exists."""
    if not filepath.exists():
        logger.warning(f"File not found: {filepath}")
        return None
    
    return _normalize_proper_management_df(pd.read_csv(filepath))


def _normalize_proper_management_df(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column types for proper management dataset."""
    df["ngo_id"] = df["ngo_id"].astype(int)
    df["has_proper_management"] = df["has_proper_management"].astype(bool)
    return df

# return should be pd.data frame or raise exception
def load_remote_proper_management_csv(url: str) -> pd.DataFrame:
    """Load proper management CSV from remote URL."""
    try:
        df = pd.read_csv(url)
    except Exception as exc:
        logger.exception(
            "Failed to fetch remote proper management CSV from %s: %s", url, exc
        )
        raise exc
    return _normalize_proper_management_df(df)


def detect_changes(
    previous_df: Optional[pd.DataFrame],
    current_df: pd.DataFrame
) -> list[ProperManagementChange]:
    """
    Detect changes in proper management status between two datasets.
    
    Returns a list of ProperManagementChange objects representing NGOs
    that either gained or lost their proper management certificate.
    """
    if previous_df is None:
        logger.info("No previous data found. Skipping change detection.")
        return []
    
    # Merge on ngo_id to compare
    merged = current_df.merge(
        previous_df[["ngo_id", "has_proper_management"]],
        on="ngo_id",
        how="left",
        suffixes=("_current", "_previous")
    )
    
    changes = []
    
    for _, row in merged.iterrows():
        current_status = row["has_proper_management_current"]
        previous_status = row.get("has_proper_management_previous")
        
        # Skip if no previous data (new NGO)
        if pd.isna(previous_status):
            continue
        
        # Detect changes
        if current_status and not previous_status:
            changes.append(ProperManagementChange(
                ngo_id=int(row["ngo_id"]),
                ngo_name=row["ngo_name"],
                change_type=ProperManagementChangeType.GAINED
            ))
        elif not current_status and previous_status:
            changes.append(ProperManagementChange(
                ngo_id=int(row["ngo_id"]),
                ngo_name=row["ngo_name"],
                change_type=ProperManagementChangeType.LOST
            ))
    
    return changes


def build_email_html(changes: list[ProperManagementChange]) -> str:
    """Build HTML email content with change details."""
    gained = [c for c in changes if c.change_type == ProperManagementChangeType.GAINED]
    lost = [c for c in changes if c.change_type == ProperManagementChangeType.LOST]
    
    html = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; direction: rtl; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: right; }
            th { background-color: #4CAF50; color: white; }
            .gained { background-color: #d4edda; }
            .lost { background-color: #f8d7da; }
            h2 { color: #333; }
            a { color: #0066cc; }
        </style>
    </head>
    <body>
        <h1>שינויים בסטטוס ניהול תקין</h1>
    """
    
    if gained:
        html += """
        <h2>עמותות שקיבלו אישור ניהול תקין ✅</h2>
        <table>
            <tr>
                <th>מזהה עמותה</th>
                <th>שם עמותה</th>
                <th>קישור</th>
            </tr>
        """
        for change in gained:
            html += f"""
            <tr class="gained">
                <td>{change.ngo_id}</td>
                <td>{change.ngo_name}</td>
                <td><a href="{change.guidestar_url}">צפה בגיידסטאר</a></td>
            </tr>
            """
        html += "</table>"
    
    if lost:
        html += """
        <h2>עמותות שאיבדו אישור ניהול תקין ❌</h2>
        <table>
            <tr>
                <th>מזהה עמותה</th>
                <th>שם עמותה</th>
                <th>קישור</th>
            </tr>
        """
        for change in lost:
            html += f"""
            <tr class="lost">
                <td>{change.ngo_id}</td>
                <td>{change.ngo_name}</td>
                <td><a href="{change.guidestar_url}">צפה בגיידסטאר</a></td>
            </tr>
            """
        html += "</table>"
    
    html += f"""
        <p>סה"כ שינויים: {len(changes)}</p>
        <p>קיבלו אישור: {len(gained)} | איבדו אישור: {len(lost)}</p>
    </body>
    </html>
    """
    
    return html


def send_notification_email(changes: list[ProperManagementChange]) -> bool:
    """
    Send email notification about proper management status changes via Gmail SMTP.
    
    Required environment variables:
    - GMAIL_SMTP_USER: Gmail address (or account alias)
    - GMAIL_SMTP_PASSWORD: Gmail app password
    - EMAIL_FROM: Sender email address (must be Gmail)
    - EMAIL_TO: Recipient email address(es), comma-separated for multiple
    
    Returns True if email was sent successfully, False otherwise.
    """
    smtp_user = os.environ.get("GMAIL_SMTP_USER")
    smtp_password = os.environ.get("GMAIL_SMTP_PASSWORD")
    email_from = os.environ.get("EMAIL_FROM")
    email_to = os.environ.get("EMAIL_TO")
    
    if not all([smtp_user, smtp_password, email_from, email_to]):
        logger.error(
            "Missing required environment variables for email. "
            "Required: GMAIL_SMTP_USER, GMAIL_SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO"
        )
        return False
    
    # Support multiple recipients
    recipients = [email.strip() for email in email_to.split(",")]
    
    gained_count = len(
        [c for c in changes if c.change_type == ProperManagementChangeType.GAINED]
    )
    lost_count = len(
        [c for c in changes if c.change_type == ProperManagementChangeType.LOST]
    )
    
    subject = f"שינויים בסטטוס ניהול תקין: {gained_count} קיבלו, {lost_count} איבדו"
    html_content = build_email_html(changes)
    text_content = (
        f"NGO Proper Management Status Changes\n"
        f"Total changes: {len(changes)}\n"
        f"Gained: {gained_count} | Lost: {lost_count}\n"
    )

    try:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = email_from
        message["To"] = ", ".join(recipients)
        message.set_content(text_content)
        message.add_alternative(html_content, subtype="html")

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)

        logger.info("Email sent successfully via Gmail SMTP")
        return True
    except Exception as e:
        logger.exception(f"Failed to send email: {e}")
        return False


def check_and_notify() -> tuple[list[ProperManagementChange], bool]:
    """
    Main function to check for proper management changes and send notifications.
    
    The current dataset is loaded from the local data directory, while the
    previous dataset is fetched from the URL provided in the
    REMOTE_PROPER_MANAGEMENT_URL environment variable.

    Returns:
        Tuple of (list of changes, whether notification was sent)
    """
    current_file = DATA_DIR / PROPER_MANAGEMENT_FNAME

    # Load current scraped data from local filesystem
    current_df = load_proper_management_csv(current_file)
    if current_df is None:
        logger.error(f"Cannot load current data from {current_file}")
        return [], False
    
    logger.info(f"Loaded {len(current_df)} NGOs from current data")
    
    # Load previous data from remote URL
    previous_url = os.environ.get("REMOTE_PROPER_MANAGEMENT_URL")
    previous_df = load_remote_proper_management_csv(previous_url)
    logger.info("Loaded %d NGOs from remote previous data", len(previous_df))

    # Detect changes
    changes = detect_changes(previous_df, current_df)
    
    if not changes:
        logger.info("No proper management status changes detected")
        return [], False
    
    logger.info(f"Detected {len(changes)} proper management status changes")
    for change in changes:
        logger.info(f"  - {change.ngo_name} ({change.ngo_id}): {change.change_type}")
    
    # Send notification
    email_sent = send_notification_email(changes)
    
    return changes, email_sent

