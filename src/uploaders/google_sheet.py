from glob import glob
import json
from pathlib import Path
from typing import List
from marshmallow import fields
from pprint import pprint
from os import environ
from datetime import datetime
from google.oauth2 import service_account
from itertools import count
import pandas as pd
import numpy as np

from scrapers.cfi_midot_scrapy.items import OrderedSchema
import logging

logger = logging.getLogger(__name__)

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

# Files to write from
RANKED_FNAME = environ.get("RANKED_NGO_FNAME", "RankedNGOResult")
# How the input data should be interpreted.
VALUE_INPUT_OPTION = "RAW"
# Google sheet credentials
GOOGLE_CREDENTIALS_JSON = environ["GOOGLE_CREDENTIALS_JSON"]


# Dynamically change the report year.
def _get_ranked_sheet_schema(report_year: int) -> OrderedSchema:

    class RankedSheetSchema(OrderedSchema):

        # Org
        ngo_id = fields.Int(data_key="מזהה עמותה")
        ngo_name = fields.Str(
            attribute="ngo_name", allow_none=True, data_key="שם עמותה"
        )
        main_activity_field = fields.Str(
            attribute="main_activity_field",
            allow_none=True,
            data_key="תחום פעילות מרכזי",
        )
        last_financial_report_year = fields.Integer(
            attribute="report_year", data_key="שנת דוח כספי אחרון"
        )
        yearly_turnover_category_label = fields.String(
            attribute="yearly_turnover_category_label",
            allow_none=True,
            data_key=f"קטגוריית מחזור שנתי לשנת {report_year}",
        )
        _ = fields.Str(dump_default=None)

        # -- Ranks --
        main_rank_benchmark = fields.Float(
            dump_default=None, data_key="ציון ממוצע לקטגורית מחזור"
        )
        main_rank = fields.Float(
            dump_default=None, data_key=f"ציון כלכלי משוקלל לשנת {report_year}"
        )

        percentile_num = fields.Integer(
            allow_none=True, dump_default=None, data_key="מספר חמישיון"
        )
        percentile_label = fields.String(
            allow_none=True, dump_default=None, data_key="חמישיון ביחס לקטגורית מחזור"
        )

        __ = fields.Str(dump_default=None)
        # -- Sub Ranks --
        growth_rank = fields.Float(
            dump_default=None, data_key=f"ציון {report_year}- צמיחה"
        )
        balance_rank = fields.Float(
            dump_default=None, data_key=f"ציון {report_year}- גירעון/יתרה"
        )
        stability_rank = fields.Float(
            dump_default=None, data_key=f"ציון {report_year}- גיוון מקורות הכנסה"
        )
        ___ = fields.Str(dump_default=None)

        admin_expense_ratio = fields.Float(
            attribute="admin_expense_ratio",
            allow_none=True,
            data_key="אחוז הוצאות עבור הנהלה",
        )
        admin_expense_benchmark = fields.Float(
            dump_default=None, data_key="בנצמרק אחוז הנהלה"
        )
        ____ = fields.Str(dump_default=None)
        # -----------------------------------------------------------------------------------------------------------------------------------------------

        # Growth params---------------
        growth_benchmark = fields.Float(dump_default=None, data_key="בנצמרק צמיחה")
        growth_ratio = fields.Float(
            attribute="growth_ratio",
            data_key=f"אחוז צמיחה - {report_year}-{report_year-2}",
        )
        yearly_turnover = fields.Float(
            load_default=None, data_key=f"מחזור שנתי לשנת {report_year}"
        )
        yearly_turnover_1 = fields.Float(
            load_default=None,
            attribute=f"yearly_turnover_{report_year-1}",
            data_key=f"מחזור שנתי לשנת {report_year-1}",
        )
        yearly_turnover_2 = fields.Float(
            load_default=None,
            attribute=f"yearly_turnover_{report_year-2}",
            data_key=f"מחזור שנתי לשנת {report_year-2}",
        )
        yearly_turnover_3 = fields.Float(
            load_default=None,
            attribute=f"yearly_turnover_{report_year-3}",
            data_key=f"מחזור שנתי לשנת {report_year-3}",
        )

        _____ = fields.Str(dump_default=None)
        # -----------------------------------------------------------------------------------------------------------------------------------------------

        # Profit Params-------------------
        balance_benchmark = fields.Float(dump_default=None, data_key="בנצמרק גרעון")
        balance_ratio = fields.Float(
            attribute="balance_ratio", data_key=f"אחוז יתרה לשנת {report_year}"
        )
        last_annual_balance = fields.Float(
            attribute="annual_balance", data_key=f"יתרה לשנת {report_year}"
        )
        ______ = fields.Str(dump_default=None)
        # -----------------------------------------------------------------------------------------------------------------------------------------------

        # Stability Params
        max_income_benchmark = fields.Float(dump_default=None, data_key="בנצמרק גיוון")
        max_income_source_label = fields.String(
            attribute="max_income_source_label",
            allow_none=True,
            data_key="מקור הכנסה מרכזי",
        )
        max_income_ratio = fields.Float(
            attribute="max_income_ratio",
            allow_none=True,
            data_key="אחוז מקור הכנסה מרכזי ביחס לסך הכנסות",
        )

        # Income sources ratios
        total_allocations_income_ratio = fields.Float(
            attribute="total_allocations_income_ratio",
            allow_none=True,
            data_key="אחוז הכנסות מהקצאות",
        )
        total_donations_income_ratio = fields.Float(
            attribute="total_donations_income_ratio",
            allow_none=True,
            data_key="אחוז הכנסות מתרומות",
        )
        total_service_income_ratio = fields.Float(
            attribute="total_service_income_ratio",
            allow_none=True,
            data_key="אחוז הכנסות מפעילות",
        )
        total_other_income_ratio = fields.Float(
            attribute="total_other_income_ratio",
            allow_none=True,
            data_key="אחוז הכנסות אחרות",
        )
        # Computed totals
        total_allocations_income = fields.Float(
            attribute="total_allocations_income", data_key="הכנסות מהקצאות"
        )
        total_donations_income = fields.Float(
            attribute="total_donations_income", data_key="הכנסות מתרומות"
        )
        total_service_income = fields.Float(
            attribute="total_service_income", data_key="הכנסות מפעילות"
        )
        total_other_income = fields.Float(
            attribute="total_other_income", data_key="הכנסות אחרות"
        )
        _______ = fields.Str(dump_default=None)

        # -----------------------------------------------------------------------------------------------------------------------------------------------
        # Mangemnet
        expenses_for_management = fields.Float(attribute="expenses_for_management")
        expenses_salary_for_management = fields.Float(
            attribute="expenses_salary_for_management"
        )
        ________ = fields.Str(dump_default=None)
        # -----------------------------------------------------------------------------------------------------------------------------------------------
        # Unused Params
        ngo_year_founded = fields.Integer(
            attribute="ngo_year_founded",
            allow_none=True,
            data_key="שנת הקמה",
        )

        volunteers_num = fields.Integer(
            attribute="volunteers_num",
            allow_none=True,
            data_key="מספר מתנדבים",
        )
        employees_num = fields.Integer(
            attribute="employees_num",
            allow_none=True,
            data_key="מספר עובדים",
        )
        ngo_members_num = fields.Integer(
            attribute="ngo_members_num",
            allow_none=True,
            data_key="מספר חברים",
        )

        target_audience = fields.Str(
            attribute="target_audience",
            allow_none=True,
            data_key="קהל יעד",
        )
        activity_fields = fields.Str(
            attribute="activity_fields",
            allow_none=True,
            data_key="תחומי פעילות",
        )
        ngo_goal = fields.Str(
            attribute="ngo_goal", allow_none=True, data_key="מטרת העמותה"
        )
        _________ = fields.Str(dump_default=None)

        # Additional ratios
        program_expense_ratio = fields.Float(
            attribute="program_expense_ratio",
            allow_none=True,
            data_key="אחוז הוצאות עבור פעילות",
        )

        total_expenses = fields.Float(
            attribute="total_expenses", data_key='סה"כ הוצאות'
        )

        # Detailed financial info
        expenses_other = fields.Float(attribute="expenses_other")
        expenses_for_activities = fields.Float(attribute="expenses_for_activities")
        expenses_salary_for_activities = fields.Float(
            attribute="expenses_salary_for_activities"
        )
        other_expenses_for_activities = fields.Float(
            attribute="other_expenses_for_activities"
        )

        allocations_from_government = fields.Float(
            attribute="allocations_from_government"
        )
        allocations_from_local_authority = fields.Float(
            attribute="allocations_from_local_authority"
        )
        allocations_from_other_sources = fields.Float(
            attribute="allocations_from_other_sources"
        )

        donations_from_aboard = fields.Float(attribute="donations_from_aboard")
        donations_from_israel = fields.Float(attribute="donations_from_israel")
        donations_of_monetary_value = fields.Float(
            attribute="donations_of_monetary_value"
        )

        service_income_from_country = fields.Float(
            attribute="service_income_from_country"
        )
        service_income_from_local_authority = fields.Float(
            attribute="service_income_from_local_authority"
        )
        service_income_from_other = fields.Float(attribute="service_income_from_other")
        other_income_from_other_sources = fields.Float(
            attribute="other_income_from_other_sources"
        )
        other_income_members_fee = fields.Float(attribute="other_income_members_fee")

    return RankedSheetSchema


def authenticate():
    scopes = ["https://www.googleapis.com/auth/drive"]
    # Step 1: Replace single quotes with double quotes
    credentials_json = GOOGLE_CREDENTIALS_JSON.replace("'", '"')

    # Step 2: Replace unescaped newline characters with escaped newline characters
    credentials_json = credentials_json.replace("\n", "\\n")

    # Step 2: Load as JSON object
    try:
        credentials_data = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_data, scopes=scopes
        )
        return credentials
    except json.JSONDecodeError as e:
        logger.exception(f"Error parsing credentials: {e}")


def _get_batch(lst: list, n: int, counter: count) -> list:
    """Yield successive n-sized chunks from lst."""
    i = next(counter) * n
    return lst[i : i + n]


from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re


def create_sheet_if_not_exists(
    credentials, spreadsheet_id: str, prefix: str, year: int
) -> None:
    """Create a new sheet by duplicating the `ngo_ranking_template` sheet.
    If certain cells in the second row have placeholders like `{YEAR}`, `{YEAR -1}`,
    they will be replaced with dynamic values based on the provided year.
    """
    service = build("sheets", "v4", credentials=credentials)
    sheet_name = f"{prefix}{year}"

    try:
        # Step 1: Check if the sheet already exists
        sheet_metadata = (
            service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        )
        sheets = sheet_metadata.get("sheets", [])

        if any(sheet["properties"]["title"] == sheet_name for sheet in sheets):
            logger.debug(f"Sheet '{sheet_name}' already exists.")
            return

        # Step 2: Get the template sheet ID
        template_sheet_name = "ngo_ranking_template"
        template_sheet_id = next(
            (
                sheet["properties"]["sheetId"]
                for sheet in sheets
                if sheet["properties"]["title"] == template_sheet_name
            ),
            None,
        )

        if template_sheet_id is None:
            raise ValueError(
                f"Template sheet '{template_sheet_name}' not found in the spreadsheet."
            )

        # Step 3: Duplicate the template sheet
        duplicate_request = {
            "duplicateSheet": {
                "sourceSheetId": template_sheet_id,
                "newSheetName": sheet_name,
            }
        }

        response = (
            service.spreadsheets()
            .batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": [duplicate_request]}
            )
            .execute()
        )
        new_sheet_id = response["replies"][0]["duplicateSheet"]["properties"]["sheetId"]
        logger.debug(
            f"Sheet '{sheet_name}' created by duplicating '{template_sheet_name}' successfully."
        )

        # Step 4: Replace placeholders in the second row of the new sheet
        # Define a regex to match `{YEAR}`, `{YEAR -1}`, `{YEAR -2}`, etc.
        placeholder_pattern = re.compile(r"\{YEAR(?:\s*([-+]\s*\d+))?\}")

        # Get the second row values
        second_row = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A2:BP2",  # Adjust range if dynamic columns extend beyond BP
            )
            .execute()
            .get("values", [[]])[0]
        )

        # Update values in the second row by replacing placeholders
        updated_row = []
        for cell_value in second_row:
            if cell_value:
                # Replace placeholders in each cell value
                new_value = placeholder_pattern.sub(
                    lambda match: str(
                        year + int(match.group(1).replace(" ", ""))
                        if match.group(1)
                        else year
                    ),
                    cell_value,
                )
                updated_row.append(new_value)
            else:
                updated_row.append(cell_value)

        # Update the second row in the new sheet
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A2",
            valueInputOption="USER_ENTERED",
            body={"values": [updated_row]},
        ).execute()
        logger.debug(
            "Dynamic year-based naming in the second row updated successfully."
        )

    except HttpError as error:
        logger.exception(f"An error occurred: {error}")


from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from itertools import count
from pprint import pprint


def write_to_sheet(
    credentials,
    spreadsheet_id: str,
    sheet_name: str,
    values_to_write: list[list],
    batch_num=5,
) -> None:
    """Writes data to an existing sheet in batches, ensuring the range does not exceed grid limits.

    Assumes the sheet is already created and has the first two rows filled with headers and data.
    """
    service = build("sheets", "v4", credentials=credentials)

    # Retrieve the sheet's current row count
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = sheet_metadata.get("sheets", [])
    sheet_info = next(
        (sheet for sheet in sheets if sheet["properties"]["title"] == sheet_name), None
    )
    if sheet_info is None:
        raise ValueError(f"Sheet '{sheet_name}' not found in the spreadsheet.")

    max_rows = sheet_info["properties"]["gridProperties"]["rowCount"]

    # Calculate batch size and prepare for writing in batches
    batch_size = len(values_to_write) // batch_num or batch_num
    counter = count()

    for n in range(batch_num):
        # Get a batch of values to write
        batch = _get_batch(values_to_write, batch_size, counter)
        if not batch:
            break

        # Calculate the starting row for this batch
        start_row = 3 + n * batch_size
        end_row = start_row + len(batch) - 1

        # Check if the range exceeds the sheet's current row count
        if end_row > max_rows:
            # Expand the sheet to accommodate additional rows if necessary
            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [
                        {
                            "appendDimension": {
                                "sheetId": sheet_info["properties"]["sheetId"],
                                "dimension": "ROWS",
                                "length": end_row - max_rows,
                            }
                        }
                    ]
                },
            ).execute()
            logger.debug(f"Expanded '{sheet_name}' to {end_row} rows.")

            # Update max_rows to reflect the new sheet size
            max_rows = end_row

        # Define the A1 notation range for the current batch
        range_ = f"{sheet_name}!$A{start_row}"

        # Write the batch to the sheet
        request = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                body=dict(values=batch),
            )
        )
        response = request.execute()

        # Log the response for debugging or further processing
        pprint(response)


def _get_batch(values, batch_size, counter):
    """Helper function to get the next batch of values."""
    start = next(counter) * batch_size
    return values[start : start + batch_size]


def _get_publish_sheet_values(
    general_info: pd.DataFrame, ranked_dfs: List[pd.DataFrame]
) -> dict[int, list]:
    """Get the values to publish to the public spreadsheet.
    seperated by years
    """
    values = dict()
    for idx, ranked_df in enumerate(ranked_dfs):
        # Add general info to each ranked df
        df_to_publish = ranked_df.merge(general_info, on="ngo_id", how="left")
        df_to_publish = df_to_publish.replace(np.nan, None, regex=True)
        # Dump the ranked df to a list of dicts
        rank_year = int(df_to_publish["report_year"].iloc[0])
        sheet_schema = _get_ranked_sheet_schema(rank_year)
        records = sheet_schema(many=True).dump(df_to_publish.to_dict(orient="records"))
        # # Flatten the list of dicts to a list of lists
        records = [list(record.values()) for record in records]

        values[rank_year] = records

    return values


def load_all_ranked_years() -> List[list]:
    # Find all available ranking csv files and load them to dataframe.
    ranked_years = []
    ranked_files = glob(str(DATA_DIR / f"{RANKED_FNAME}_*.csv"))
    for ranked_file in ranked_files:
        ranked_year = pd.read_csv(ranked_file)
        ranked_year.replace(np.nan, "", inplace=True)
        ranked_years.append(ranked_year.values.tolist())
    return ranked_years


def upload_spread_sheet(
    general_info: pd.DataFrame, ranked_dfs: List[pd.DataFrame]
) -> None:
    """Upload ranked NGO data to the public Google spreadsheet."""
    PUBLIC_SPREADSHEET_ID = environ["PUBLIC_SPREADSHEET_ID"]

    credentials = authenticate()
    prefix = "ngo_ranking_"
    publish_sheet_values = _get_publish_sheet_values(general_info, ranked_dfs)
    for year, ranks in publish_sheet_values.items():
        create_sheet_if_not_exists(credentials, PUBLIC_SPREADSHEET_ID, prefix, year)
        write_to_sheet(credentials, PUBLIC_SPREADSHEET_ID, f"{prefix}{year}", ranks)


def upload_appsheet(general_info: pd.DataFrame, ranked_dfs: List[pd.DataFrame]) -> None:
    """Upload NGO rankings to AppSheet (2 years ago from current date)."""
    credentials = authenticate()
    prefix = "ngo_ranking_"
    target_year = datetime.now().year - 2
    
    publish_sheet_values = _get_publish_sheet_values(general_info, ranked_dfs)
    ranks = publish_sheet_values[target_year]
    
    logger.info(f"Uploading AppSheet data for year {target_year}")
    write_to_sheet(credentials, environ["APPSHEET_SPREADSHEET_ID"], f"{prefix}appsheet", ranks)