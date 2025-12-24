import logging

from scrapers.cfi_midot_scrapy.items import (
    NgoFinanceInfo,
    NgoGeneralInfo,
    NgoInfo,
    NgoTopRecipientSalary,
    NgoTopRecipientsSalaries,
)

logger = logging.getLogger(__name__)


RESOURCE_NAME_TO_METHOD_NAME = {
    "general_info": "getMalkarDetails",
    "financial_info": "getMalkarFinances",
    "top_earners_info": "getMalkarWageEarners",
}


METHOD_NAME_RESOURCE_NAME = {v: k for k, v in RESOURCE_NAME_TO_METHOD_NAME.items()}


def _map_between_scraped_and_ngo_item(data_mapper: dict, scraped_data: dict) -> dict:
    ngo_item_data = {}
    for malkar_attr_name, ngo_attr_name in data_mapper.items():
        scraped_data_value = scraped_data.get(malkar_attr_name)
        if scraped_data_value is None:
            logger.debug("Missing %s in scraped NGO data", malkar_attr_name)
            continue
        ngo_item_data[ngo_attr_name] = scraped_data_value
    return ngo_item_data


def _malkar_details_parser(scraped_data: dict, ngo_id: int) -> NgoGeneralInfo:
    general_data_mapper = {
        "Name": "ngo_name",
        "orgGoal": "ngo_goal",
        "orgYearFounded": "ngo_year_founded",
        "volunteers": "volunteers_num",
        "employees": "employees_num",
        "members": "ngo_members_num",
        "tchumPeilutMain": "main_activity_field",
        "tchumPeilutSecondary": "activity_fields",
        "audience": "target_audience",
    }
    ngo_general = _map_between_scraped_and_ngo_item(general_data_mapper, scraped_data)
    return NgoGeneralInfo(ngo_id=ngo_id, **ngo_general)


def _malkar_finance_parser(
    scraped_data: list[dict], ngo_id: int
) -> list[NgoFinanceInfo]:
    finance_data_mapper = {
        "Allocations_Government": "allocations_from_government",
        "Allocations_LocalAuthority": "allocations_from_local_authority",
        "Allocations_Other": "allocations_from_other_sources",
        "Donations_Aboard": "donations_from_aboard",
        "Donations_Country": "donations_from_israel",
        "Donations_ValueForMoney": "donations_of_monetary_value",
        "Expenses_Other": "expenses_other",
        "Expenses_Activities": "expenses_for_activities",
        "Expenses_OtherActivities": "other_expenses_for_activities",
        "Expenses_OtherManagement": "expenses_for_management",
        "Expenses_Salary": "expenses_salary_for_management",
        "Expenses_SalaryActivities": "expenses_salary_for_activities",
        "Incomes_MembersFee": "other_income_members_fee",
        "Incomes_OtherSource": "other_income_from_other_sources",
        "Incomes_ServicesForCountry": "service_income_from_country",
        "Incomes_ServicesForLocalAuthority": "service_income_from_local_authority",
        "Incomes_ServicesForOther": "service_income_from_other",
        "Year": "report_year",
    }

    ngo_finance_objects = []
    for data in scraped_data:
        ngo_finance_pyaload = _map_between_scraped_and_ngo_item(
            finance_data_mapper, data
        )
        ngo_finance_objects.append(NgoFinanceInfo(ngo_id=ngo_id, **ngo_finance_pyaload))
    return ngo_finance_objects


def _malkar_wage_earners_parser(
    scraped_data: list[dict], ngo_id: int
) -> list[NgoTopRecipientsSalaries]:

    # We assumes that Amount is in NIS
    earner_salary_mapper = {
        "MainLabel": "recipient_title",
        "Amount": "gross_salary_in_nis",
    }

    recipient_salaries_objects = []
    for data in scraped_data:
        top_earners_salaries = []
        scraped_earners_salaries = data.get("Data")
        if scraped_earners_salaries is None:
            logger.debug("No information about top earners salaries for: %s", ngo_id)
            continue
        for earner_salary in scraped_earners_salaries:
            earner_salary_data = _map_between_scraped_and_ngo_item(
                earner_salary_mapper, earner_salary
            )
            top_earners_salaries.append(NgoTopRecipientSalary(**earner_salary_data))

        report_year = int(data["Label"].replace(" - שכר לשנה ברוטו", ""))
        recipient_salaries_objects.append(
            NgoTopRecipientsSalaries(
                report_year=report_year,
                ngo_id=ngo_id,
                top_earners_salaries=top_earners_salaries,
            )
        )
    return recipient_salaries_objects


METHOD_NAME_TO_ITEM_PARSER = {
    "getMalkarDetails": _malkar_details_parser,
    "getMalkarFinances": _malkar_finance_parser,
    "getMalkarWageEarners": _malkar_wage_earners_parser,
}


def load_ngo_info(ngo_id: int, ngo_scraped_result: list[dict]) -> NgoInfo | dict:
    resource_items = {}
    for scraped_result in ngo_scraped_result:
        scraped_data = scraped_result["result"]["result"]
        if not scraped_data:
            logger.debug(
                "Missing scraped data for ngo: %s, method: %s",
                ngo_id,
                scraped_result["method"],
            )
            continue

        parser = METHOD_NAME_TO_ITEM_PARSER[scraped_result["method"]]
        resource_item = parser(scraped_data, ngo_id)

        resource_name = METHOD_NAME_RESOURCE_NAME[scraped_result["method"]]
        resource_items[resource_name] = resource_item

    ngo_item = NgoInfo.from_resource_items(ngo_id, resource_items)

    if _should_filter_out_ngo(ngo_item):
        logger.debug("Filtering out ngo %s", ngo_item.ngo_id)
        return dict(ngo_id=ngo_item.ngo_id)

    return ngo_item


def _should_filter_out_ngo(ngo_item: NgoInfo) -> bool:
    return (
        not ngo_item.last_financial_info
        or not ngo_item.last_financial_info.yearly_turnover_category
        # or ngo_item.last_financial_report_year not in (2021, 2020)
        or ngo_item.last_financial_info.yearly_turnover < 100_000
    )
