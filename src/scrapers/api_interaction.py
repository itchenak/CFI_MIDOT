# Download latest registered NGOs from https://data.gov.il/dataset/moj-amutot:
import requests
from typing import List
import logging

logger = logging.getLogger(__name__)


def download_registered_ngos_ids() -> List[int]:
    """
    Download latest registered NGOs from https://data.gov.il/dataset/moj-amutot
    Using their API to get the list of registered NGOs
    """

    # Define the endpoint URL
    url = "https://data.gov.il/api/3/action/datastore_search"

    # Define the payload
    payload = {
        "resource_id": "be5b7935-3922-45d4-9638-08871b17ec95",
        "filters": {},
        "q": "",
        "distinct": True,
        "plain": True,
        "limit": 1000000,
        "offset": 0,
        "fields": ["מספר עמותה"],
        "sort": "",
        "include_total": True,
        "records_format": "objects",
    }

    # Make the POST request to the API
    response = requests.post(url, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response to extract NGO IDs
        data = response.json()
        records = data.get("result", {}).get("records", [])
        # Convert the IDs to integers and return as a list
        return [int(record["מספר עמותה"]) for record in records]
    else:
        logger.error(f"Request failed with status code {response.status_code}")
        return []
