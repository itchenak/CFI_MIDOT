import json
import logging
import re
from typing import Callable, Iterator, Union

import scrapy
from scrapers.cfi_midot_scrapy.items import NgoInfo
from scrapers.cfi_midot_scrapy.items_loaders import (
    RESOURCE_NAME_TO_METHOD_NAME,
    load_ngo_info,
)

logger = logging.getLogger(__name__)

HEADERS = {
    "X-User-Agent": "Visualforce-Remoting",
    "Origin": "https://www.guidestar.org.il",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,he;q=0.8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive",
}


def _get_csrf(page_text):
    csrf_re = re.compile(
        r'\{"name":"getUserInfo","len":0,"ns":"","ver":43\.0,"csrf":"([^"]+)"\}'
    )
    return "VmpFPSxNakF4T0Mwd05DMHhNMVF3TnpvMU16b3lOaTR5TkRGYSxyWk4waExQQ09WeTJJNnVPMWJuV3IzLFpXWTNaRFkz"
    csrf, *_ = csrf_re.findall(page_text)
    return csrf


def _get_vid(page_text):
    csrf_re = re.compile(r'RemotingProviderImpl\(\{"vf":\{"vid":"([^"]+)"')
    csrf, *_ = csrf_re.findall(page_text)
    return csrf


def generate_body_payload(
    resources: list[str],
    ngo_num: int,
    page_text: str,
) -> list[dict]:
    csrf = _get_csrf(page_text)
    vid = _get_vid(page_text)

    body_payload: list[dict] = []
    for resource_num, resource in enumerate(resources):
        body_payload.append(
            {
                "action": "GSTAR_Ctrl",
                "method": RESOURCE_NAME_TO_METHOD_NAME[resource],
                "data": [ngo_num],
                "type": "rpc",
                "tid": 3 + resource_num,
                "ctx": {"csrf": csrf, "ns": "", "vid": vid, "ver": 39},
            }
        )
    return body_payload


def _parse_ngo_ids(ngo_ids: Union[list[int], str]) -> list[int]:
    try:
        if isinstance(ngo_ids, str):
            return [int(ngo_id) for ngo_id in ngo_ids.split(",")]
        elif isinstance(ngo_ids, list):
            return list(map(int, ngo_ids))
    except ValueError as err:
        raise ValueError(f"Could not parse ngo ids from argument: {ngo_ids}") from err


class GuideStarSpider(scrapy.Spider):
    name = "guidestar"
    # URL to get ngo data
    ngo_xml_data_url = "https://www.guidestar.org.il/apexremote"

    # NGO resources to be scraped
    resources = [
        "general_info",
        "financial_info",
        # "top_earners_info",
    ]

    def __init__(self, ngo_ids: Union[list[int], str], **kwargs) -> None:
        self.ngo_ids = _parse_ngo_ids(ngo_ids)
        super().__init__(**kwargs)

    def request(self, url: str, ngo_id: int, callback: Callable) -> scrapy.Request:
        request = scrapy.Request(url=url, callback=callback, meta={"ngo_id": ngo_id})

        # Mutates headers
        HEADERS["Referer"] = url
        # Set user agenet to avoid 403
        request.headers["User-Agent"] = HEADERS["User-Agent"]

        return request

    def start_requests(self) -> Iterator[scrapy.Request]:
        for ngo_id in self.ngo_ids:
            # Used to build body_payload for ngo_data request
            helper_page_url = f"https://www.guidestar.org.il/organization/{ngo_id}"

            yield self.request(
                url=helper_page_url,
                ngo_id=ngo_id,
                callback=self.scrape_xml_data,
            )

    def scrape_xml_data(self, helper_page_response) -> Iterator[scrapy.Request]:
        ngo_id = helper_page_response.meta["ngo_id"]
        body_payload = generate_body_payload(
            self.resources, ngo_id, helper_page_response.text
        )

        yield scrapy.Request(
            url=self.ngo_xml_data_url,
            method="POST",
            body=json.dumps(body_payload),
            headers=HEADERS,
            callback=self.parse,
            meta=helper_page_response.meta,
        )

    def parse(self, response, **kwargs) -> Iterator[NgoInfo | dict]:
        """Parse NGO data from response"""
        ngo_id = response.meta["ngo_id"]
        logger.debug("Starting Parsing of xml_data for: %s", ngo_id)
        ngo_scraped_data = response.json()
        if not self._validate_all_resources_arrived_successfully(ngo_scraped_data, ngo_id):
            return

        ngo_info_item = load_ngo_info(ngo_id, ngo_scraped_data)
        logger.debug("Finish Parsing xml_data for: %s", ngo_id)

        yield ngo_info_item

    def _validate_all_resources_arrived_successfully(
        self, ngo_scraped_data: list[dict], ngo_id: int
    ) -> None:

        if len(ngo_scraped_data) != len(self.resources):
            raise Exception("Not all resources scraped for ngo")

        for scraped_resource in ngo_scraped_data:
            if scraped_resource["statusCode"] != 200:
                raise Exception(
                    f"Failed to scrap ngo: {ngo_id}, Returned status code: {scraped_resource['statusCode']}"
                )
            if not scraped_resource["result"]["success"]:
                logger.warning(
                    f"Failed to scrap ngo: {ngo_id}. Failed to get one or more malkar resources"
                )
                return False
        return True