# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from functools import cached_property
import sys
from datetime import datetime
from enum import Enum
from typing import Optional, Union

import attr
from attrs_strict import type_validator
from marshmallow import Schema, SchemaOpts, fields, post_dump
from marshmallow_enum import EnumField


class IncomeSourceLabels(Enum):
    """Maps income source ratio keys to labels. Used for display purposes."""

    total_allocations_income_ratio = "הכנסות מהקצאות"
    total_donations_income_ratio = "הכנסות מתרומות"
    total_service_income_ratio = "הכנסות משירותים"
    total_other_income_ratio = "הכנסות ממקורות אחרים"


class IncomeSourceRatioLabels(Enum):
    """Maps income source ratio keys to labels. Used for display purposes."""

    total_allocations_income_ratio = "אחוז הכנסות מהקצאות"
    total_donations_income_ratio = "אחוז הכנסות מתרומות"
    total_service_income_ratio = "אחוז הכנסות משירותים"
    total_other_income_ratio = "אחוז הכנסות ממקורות אחרים"


class TurnoverCategory(Enum):
    """Maps yearly turnover to categories. Used for ranking and display purposes"""

    CAT_500K = (0, 500_000, "100K-500K ₪")
    CAT_1M = (500_000, 1_000_000, "500K-1M ₪")
    CAT_3M = (1_000_000, 3_000_000, "1M-3M ₪")
    CAT_5M = (3_000_000, 5_000_000, "3M-5M ₪")
    CAT_10M = (5_000_000, 10_000_000, "5M-10M ₪")
    CAT_50M = (10_000_000, 50_000_000, "10M-50M ₪")
    CAT_MAX = (50_000_000, sys.maxsize, "50M+ ₪")

    def __init__(self, min_value: int, max_value: int, label: str):
        self.min_value = min_value
        self.max_value = max_value
        self.label = label

    def __lt__(self, other: "TurnoverCategory"):
        return self.min_value < other.min_value

    @classmethod
    def from_value(cls, value: int | float) -> "TurnoverCategory":
        for turnover_category in cls:
            if (
                value >= turnover_category.min_value
                and value < turnover_category.max_value
            ):
                return turnover_category
        raise ValueError(f"Could not find turnover category for value: {value}")


def _add_type_validator(cls, fields):
    validated_fields = []
    for field in fields:
        if field.validator is not None:
            validated_fields.append(field)
            continue
        validated_fields.append(field.evolve(validator=type_validator()))
    return validated_fields


@attr.s(frozen=True, auto_attribs=True, field_transformer=_add_type_validator)
class NgoTopRecipientSalary:
    recipient_title: str
    gross_salary_in_nis: float


@attr.s(frozen=True, auto_attribs=True, field_transformer=_add_type_validator)
class NgoTopRecipientsSalaries:
    ngo_id: int = attr.ib(converter=int)
    report_year: int = attr.ib(converter=int)
    top_earners_salaries: list[NgoTopRecipientSalary]


@attr.s(frozen=True, auto_attribs=True, field_transformer=_add_type_validator)
class NgoGeneralInfo:
    ngo_id: int = attr.ib(converter=int)
    ngo_name: str
    ngo_year_founded: Optional[int] = None
    ngo_goal: Optional[str] = None
    volunteers_num: Optional[int] = None
    employees_num: Optional[int] = None
    ngo_members_num: Optional[int] = None

    main_activity_field: Optional[str] = None
    activity_fields: Optional[list[str]] = None
    target_audience: Optional[list[str]] = None


@attr.s(
    frozen=True, auto_attribs=True, kw_only=True, field_transformer=_add_type_validator
)
class NgoFinanceInfo:
    report_year: int = attr.ib(converter=int)
    ngo_id: int = attr.ib(converter=int)

    allocations_from_government: Union[int, float] = 0
    allocations_from_local_authority: Union[int, float] = 0
    allocations_from_other_sources: Union[int, float] = 0

    donations_from_aboard: Union[int, float] = 0
    donations_from_israel: Union[int, float] = 0

    service_income_from_country: Union[int, float] = 0
    service_income_from_local_authority: Union[int, float] = 0
    service_income_from_other: Union[int, float] = 0

    other_income_from_other_sources: Union[int, float] = 0
    other_income_members_fee: Union[int, float] = 0

    expenses_other: Union[int, float] = 0
    expenses_for_management: Union[int, float] = 0
    expenses_salary_for_management: Union[int, float] = 0
    expenses_salary_for_activities: Union[int, float] = 0
    other_expenses_for_activities: Union[int, float] = 0
    expenses_for_activities: Union[int, float] = 0
    donations_of_monetary_value: Union[int, float] = 0

    # ------------ Computed ------------
    total_allocations_income: Union[int, float] = attr.ib(init=False)
    total_donations_income: Union[int, float] = attr.ib(init=False)
    total_service_income: Union[int, float] = attr.ib(init=False)
    total_other_income: Union[int, float] = attr.ib(init=False)
    total_expenses: Union[int, float] = attr.ib(init=False)
    # ------------ Ratios ------------
    program_expense_ratio: Optional[float] = attr.ib(init=False)
    admin_expense_ratio: Optional[int | float] = attr.ib(init=False)
    total_allocations_income_ratio: Union[int, float] = attr.ib(init=False)
    total_donations_income_ratio: Union[int, float] = attr.ib(init=False)
    total_service_income_ratio: Union[int, float] = attr.ib(init=False)
    total_other_income_ratio: Union[int, float] = attr.ib(init=False)
    # Used for ranking
    # yearly_turnover: Union[int, float] = attr.ib(init=False)
    balance_ratio: Union[int, float] = attr.ib(init=False)
    max_income_ratio: Union[int, float] = attr.ib(init=False)
    growth_ratio: Union[int, float] = attr.ib(init=False)

    @total_allocations_income.default
    def _total_allocations_income(self) -> Union[int, float]:
        return (
            self.allocations_from_government
            + self.allocations_from_local_authority
            + self.allocations_from_other_sources
        )

    @total_donations_income.default
    def _total_donations_income(self) -> Union[int, float]:
        return (
            self.donations_from_aboard
            + self.donations_from_israel
            + self.donations_of_monetary_value
        )

    @total_service_income.default
    def _total_service_income(self) -> Union[int, float]:
        return (
            self.service_income_from_country
            + self.service_income_from_local_authority
            + self.service_income_from_other
        )

    @total_other_income.default
    def _total_other_income(self) -> Union[int, float]:
        return self.other_income_from_other_sources + self.other_income_members_fee

    @total_expenses.default
    def _total_expenses(self) -> Union[int, float]:
        return (
            self.expenses_other
            + self.other_expenses_for_activities
            + self.expenses_for_activities
            + self.expenses_for_management
            + self.expenses_salary_for_management
            + self.expenses_salary_for_activities
        )

    @cached_property
    def yearly_turnover(self) -> Union[int, float]:
        return (
            self.total_allocations_income
            + self.total_donations_income
            + self.total_service_income
            + self.total_other_income
        )

    # ------------ Categories ------------
    @cached_property
    def yearly_turnover_category(self) -> TurnoverCategory:
        return TurnoverCategory.from_value(self.yearly_turnover)

    @cached_property
    def yearly_turnover_category_label(self) -> str:
        return self.yearly_turnover_category.label

    # ------------ Ratios ------------
    @total_allocations_income_ratio.default
    def _total_allocations_income_ratio(self) -> Union[int, float]:
        # Precentage of total allocations income to yearly turnover
        if not self.yearly_turnover:
            return 0
        return self.total_allocations_income / self.yearly_turnover

    @total_donations_income_ratio.default
    def _total_donations_income_ratio(self) -> Union[int, float]:
        # Precentage of total donations income to yearly turnover
        if not self.yearly_turnover:
            return 0
        return self.total_donations_income / self.yearly_turnover

    @total_service_income_ratio.default
    def _total_service_income_ratio(self) -> Union[int, float]:
        # Precentage of total service income to yearly turnover
        if not self.yearly_turnover:
            return 0
        return self.total_service_income / self.yearly_turnover

    @total_other_income_ratio.default
    def _total_other_income_ratio(self) -> Union[int, float]:
        # Precentage of total other income to yearly turnover
        if not self.yearly_turnover:
            return 0
        return self.total_other_income / self.yearly_turnover

    @property
    def expenses_for_management_ratio(self) -> Union[int, float]:
        # Precentage of total other income to yearly turnover
        if not self.expenses_for_management:
            return 0
        return self.expenses_for_management / self.yearly_turnover

    @property
    def income_source_ratios(self) -> dict[str, float]:
        # Returens `ratio_keys` as label: value dict
        ratio_keys = [
            "total_allocations_income_ratio",
            "total_donations_income_ratio",
            "total_service_income_ratio",
            "total_other_income_ratio",
        ]

        return {
            IncomeSourceRatioLabels[key].value.replace("אחוז ", ""): getattr(self, key)
            for key in ratio_keys
        }

    # return {
    #     f"{IncomeSourceRatioLabels[key].name}": getattr(self, key)
    #     for key in ratio_keys
    # }

    @max_income_ratio.default
    def _max_income_ratio(self) -> float:
        return max(self.income_source_ratios.values())

    @property
    def max_income_source_label(self) -> str:
        return max(self.income_source_ratios, key=self.income_source_ratios.get)

    @property
    def annual_balance(self) -> Union[int, float]:
        # Annual profit made
        if not self.yearly_turnover:
            return 0
        return self.yearly_turnover - self.total_expenses

    @balance_ratio.default
    def _balance_ratio(self) -> Union[int, float]:
        # Precantage of annual profit to yearly turnover
        if not self.annual_balance:
            return 0
        return self.annual_balance / self.yearly_turnover

    @program_expense_ratio.default
    def _program_expense_ratio(self) -> Optional[float]:

        total_program_expenses = (
            self.other_expenses_for_activities + self.expenses_salary_for_activities
        )

        if total_program_expenses == 0 or self.total_expenses == 0:
            return None

        return total_program_expenses / self.total_expenses

    @admin_expense_ratio.default
    def _admin_expense_ratio(self) -> Optional[float | int]:

        total_administrative_expenses = (
            self.expenses_salary_for_management + self.expenses_for_management
        )

        if total_administrative_expenses == 0 or self.yearly_turnover == 0:
            return 0

        return total_administrative_expenses / self.yearly_turnover


@attr.s(frozen=True, auto_attribs=True, field_transformer=_add_type_validator)
class NgoInfo:
    ngo_id: int

    general_info: NgoGeneralInfo
    financial_info: list[NgoFinanceInfo] = attr.ib(
        factory=list,
        converter=lambda reports: sorted(
            reports, key=lambda report: report.report_year
        ),
    )
    top_earners_info: list[NgoTopRecipientsSalaries] = attr.ib(
        factory=list,
        converter=lambda reports: sorted(
            reports, key=lambda report: report.report_year
        ),
    )

    @cached_property
    def last_financial_info(self) -> Optional[NgoFinanceInfo]:
        return self.financial_info[-1] if self.financial_info else None

    @cached_property
    def last_financial_report_year(self) -> Optional[int]:
        if not self.financial_info:
            return None
        return self.financial_info[-1].report_year

    @property
    def last_top_earners_info(self) -> Optional[NgoTopRecipientsSalaries]:
        if not self.top_earners_info:
            return None

        return self.top_earners_info[-1]

    # ---------------- computed ------------------
    @property
    def growth_ratio(self) -> float:
        last_turnover = (
            self.last_financial_info.yearly_turnover
            if self.last_financial_info
            else None
        )
        if not last_turnover:
            return -0.25

        # financial_history: reversed financial_info, 1st is last year
        if len(self.financial_info) < 2:
            return 1.0

        # First turnover either 1 or 2 years back
        year_diff = 1 if len(self.financial_info) == 2 else 2
        for _ in range(1):
            first_turnover = self.financial_info[year_diff].yearly_turnover
            if first_turnover >= 25_000:
                return (last_turnover / first_turnover) ** (1 / year_diff) - 1
            year_diff -= 1
        return 1.0

    @classmethod
    def from_resource_items(cls, ngo_id: int, resources_items: dict) -> "NgoInfo":
        return cls(ngo_id=ngo_id, **resources_items)


# ------------------------------------------------ Display Schemas ------------------------------------------------


class OrderedSchema(Schema):
    class OrderedOpts(SchemaOpts):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.ordered = True

    OPTIONS_CLASS = OrderedOpts

    def __getattr__(self, key):
        try:
            return self._declared_fields[key]
        except KeyError:
            raise AttributeError(key)


class NgoTopRecipientSalarySchema(OrderedSchema):
    recipient_title = fields.String()
    gross_salary_in_nis = fields.Float()


class NgoTopRecipientsSalariesSchema(OrderedSchema):
    ngo_id = fields.Int()
    report_year = fields.Int()
    top_earners_salaries = fields.Nested(NgoTopRecipientSalarySchema, many=True)


class NgoGeneralInfoSchema(OrderedSchema):
    ngo_id = fields.Int()
    ngo_name = fields.String()
    ngo_year_founded = fields.Int(allow_none=True)
    ngo_goal = fields.String(allow_none=True)
    volunteers_num = fields.Int(allow_none=True)
    employees_num = fields.Int(allow_none=True)
    ngo_members_num = fields.Int(allow_none=True)

    main_activity_field = fields.String(allow_none=True)
    activity_fields = fields.List(fields.String(), allow_none=True)
    target_audience = fields.List(fields.String(), allow_none=True)


class NgoFinanceInfoSchema(OrderedSchema):
    ngo_id = fields.Int()
    report_year = fields.Int()

    yearly_turnover = fields.Number()
    yearly_turnover_category = EnumField(TurnoverCategory)
    yearly_turnover_category_label = fields.String()
    # ------------ Ratios ------------
    balance_ratio = fields.Number()
    program_expense_ratio = fields.Number(allow_none=True)
    admin_expense_ratio = fields.Number(allow_none=True)
    max_income_ratio = fields.Number()
    max_income_source_label = fields.String()
    total_allocations_income_ratio = fields.Number()
    total_donations_income_ratio = fields.Number()
    total_service_income_ratio = fields.Number()
    total_other_income_ratio = fields.Number()
    # ------------ Totals ------------
    total_allocations_income = fields.Number()
    total_donations_income = fields.Number()
    total_service_income = fields.Number()
    total_other_income = fields.Number()
    total_expenses = fields.Number()

    # ------------ Details ------------
    allocations_from_government = fields.Number()
    allocations_from_local_authority = fields.Number()
    allocations_from_other_sources = fields.Number()
    donations_from_aboard = fields.Number()
    donations_from_israel = fields.Number()
    service_income_from_country = fields.Number()
    service_income_from_local_authority = fields.Number()
    service_income_from_other = fields.Number()
    other_income_from_other_sources = fields.Number()
    other_income_members_fee = fields.Number()
    expenses_other = fields.Number()
    expenses_for_management = fields.Number()
    expenses_salary_for_management = fields.Number()
    expenses_salary_for_activities = fields.Number()
    other_expenses_for_activities = fields.Number()
    expenses_for_activities = fields.Number()
    donations_of_monetary_value = fields.Number()
    annual_balance = fields.Number()


# REPORT_YEAR = 2020


# CURRENT_YEAR = datetime.now().year

# NGO_FINANCE_DYNAMIC_KEYS = {
#     "yearly_turnover": "מחזור שנתי",
# }


# class UnrankedNGOResult(OrderedSchema):
#     """**DEPRECATED**. Use RankedNGOResult instead.
#     Flatten schema for NgoInfo"""

#     # Org
#     ngo_id = fields.Int(data_key="מזהה עמותה")
#     ngo_name = fields.Str(attribute="general_info.ngo_name", allow_none=True, data_key="שם עמותה")
#     main_activity_field = fields.Str(
#         attribute="general_info.main_activity_field", allow_none=True, data_key="תחום פעילות מרכזי")
#     last_financial_report_year = fields.Integer(
#         attribute="last_financial_report_year", data_key="שנת דוח כספי אחרון")
#     yearly_turnover_category_label = fields.String(
#         attribute="last_financial_info.yearly_turnover_category_label", allow_none=True,
#         data_key=f"קטגוריית מחזור שנתי לשנת {REPORT_YEAR}",)
#     _ = fields.Str(dump_default=None)

#     # -- Ranks --
#     main_rank_benchmark = fields.Number(dump_default=None,
#                                         data_key="ציון ממוצע לקטגורית מחזור")
#     main_rank = fields.Number(dump_default=None,
#                               data_key=f"ציון כלכלי משוקלל לשנת {REPORT_YEAR}")

#     percentile_num = fields.Integer(allow_none=True, dump_default=None,
#                                     data_key="מספר חמישיון")
#     percentile_label = fields.String(allow_none=True, dump_default=None,
#                                      data_key="חמישיון ביחס לקטגורית מחזור")

#     __ = fields.Str(dump_default=None)
#     # -- Sub Ranks --
#     growth_rank = fields.Number(dump_default=None,
#                                 data_key=f"ציון {REPORT_YEAR}- צמיחה")
#     balance_rank = fields.Number(dump_default=None,
#                                  data_key=f"ציון {REPORT_YEAR}- גירעון/יתרה")
#     stability_rank = fields.Number(dump_default=None,
#                                    data_key=f"ציון {REPORT_YEAR}- גיוון מקורות הכנסה")
#     ___ = fields.Str(dump_default=None)

#     admin_expense_ratio = fields.Number(
#         attribute="last_financial_info.admin_expense_ratio", allow_none=True,
#         data_key="אחוז הוצאות עבור הנהלה")
#     admin_expense_benchmark = fields.Number(
#         dump_default=None,
#         data_key="בנצמרק אחוז הנהלה")
#     ____ = fields.Str(dump_default=None)
#     # -----------------------------------------------------------------------------------------------------------------------------------------------

#     # Growth params---------------
#     growth_benchmark = fields.Number(
#         dump_default=None,
#         data_key="בנצמרק צמיחה")
#     growth_ratio = fields.Number(attribute="growth_ratio", data_key=f"אחוז צמיחה - {REPORT_YEAR}-{REPORT_YEAR-2}")
#     # TODO: dynamic data_key year
#     yearly_turnover_2021 = fields.Number(load_default=0, data_key="מחזור שנתי לשנת 2021")
#     yearly_turnover_2020 = fields.Number(load_default=0, data_key="מחזור שנתי לשנת 2020")
#     yearly_turnover_2019 = fields.Number(load_default=0, data_key="מחזור שנתי לשנת 2019")
#     yearly_turnover_2018 = fields.Number(load_default=0, data_key="מחזור שנתי לשנת 2018")
#     _____ = fields.Str(dump_default=None)
#     # -----------------------------------------------------------------------------------------------------------------------------------------------

#     # Profit Params-------------------
#     balance_benchmark = fields.Number(dump_default=None, data_key="בנצמרק גרעון")
#     balance_ratio = fields.Number(attribute="last_financial_info.balance_ratio",
#                                   data_key=f"אחוז יתרה לשנת {REPORT_YEAR}")
#     last_annual_balance = fields.Number(attribute="last_financial_info.annual_balance",
#                                         data_key=f"יתרה לשנת {REPORT_YEAR}")
#     ______ = fields.Str(dump_default=None)
#     # -----------------------------------------------------------------------------------------------------------------------------------------------

#     # Stability Params
#     max_income_benchmark = fields.Number(
#         dump_default=None,
#         data_key="בנצמרק גיוון")
#     max_income_source_label = fields.String(
#         attribute="last_financial_info.max_income_source_label", allow_none=True,
#         data_key="מקור הכנסה מרכזי")
#     max_income_ratio = fields.Number(
#         attribute="last_financial_info.max_income_ratio", allow_none=True,
#         data_key="אחוז מקור הכנסה מרכזי ביחס לסך הכנסות")

#     # Income sources ratios
#     total_allocations_income_ratio = fields.Number(
#         attribute="last_financial_info.total_allocations_income_ratio", allow_none=True, data_key="אחוז הכנסות מהקצאות")
#     total_donations_income_ratio = fields.Number(
#         attribute="last_financial_info.total_donations_income_ratio", allow_none=True, data_key="אחוז הכנסות מתרומות")
#     total_service_income_ratio = fields.Number(
#         attribute="last_financial_info.total_service_income_ratio", allow_none=True, data_key="אחוז הכנסות מפעילות")
#     total_other_income_ratio = fields.Number(
#         attribute="last_financial_info.total_other_income_ratio", allow_none=True, data_key="אחוז הכנסות אחרות")
#     # Computed totals
#     total_allocations_income = fields.Number(
#         attribute="last_financial_info.total_allocations_income", data_key="הכנסות מהקצאות")
#     total_donations_income = fields.Number(
#         attribute="last_financial_info.total_donations_income", data_key="הכנסות מתרומות")
#     total_service_income = fields.Number(
#         attribute="last_financial_info.total_service_income", data_key="הכנסות מפעילות")
#     total_other_income = fields.Number(
#         attribute="last_financial_info.total_other_income", data_key="הכנסות אחרות")
#     _______ = fields.Str(dump_default=None)

#     # -----------------------------------------------------------------------------------------------------------------------------------------------
#     # Mangemnet
#     expenses_for_management = fields.Number(
#         attribute="last_financial_info.expenses_for_management"
#     )
#     expenses_salary_for_management = fields.Number(
#         attribute="last_financial_info.expenses_salary_for_management"
#     )
#     ________ = fields.Str(dump_default=None)
#     # -----------------------------------------------------------------------------------------------------------------------------------------------

#     # Unused Params
#     ngo_year_founded = fields.Integer(
#         attribute="general_info.ngo_year_founded", allow_none=True, data_key="שנת הקמה",
#     )

#     volunteers_num = fields.Integer(
#         attribute="general_info.volunteers_num", allow_none=True, data_key="מספר מתנדבים"
#     )
#     employees_num = fields.Integer(attribute="general_info.employees_num", allow_none=True, data_key="מספר עובדים")
#     ngo_members_num = fields.Integer(
#         attribute="general_info.ngo_members_num", allow_none=True, data_key="מספר חברים")

#     target_audience = fields.List(
#         fields.Str(), attribute="general_info.target_audience", allow_none=True, data_key="קהל יעד")
#     activity_fields = fields.List(
#         fields.Str(), attribute="general_info.activity_fields", allow_none=True, data_key="תחומי פעילות")
#     ngo_goal = fields.Str(attribute="general_info.ngo_goal", allow_none=True, data_key="מטרת העמותה")
#     _________ = fields.Str(dump_default=None)

#     # Additional ratios
#     program_expense_ratio = fields.Number(
#         attribute="last_financial_info.program_expense_ratio", allow_none=True, data_key="אחוז הוצאות עבור פעילות")

#     total_expenses = fields.Number(attribute="last_financial_info.total_expenses", data_key='סה"כ הוצאות')

#     financial_info_history = fields.List(
#         fields.Nested(NgoFinanceInfoSchema), attribute="financial_info"
#     )
#     # top_earners_info_history = fields.List(
#     #     fields.Nested(NgoTopRecipientsSalariesSchema), attribute="top_earners_info"
#     # )

#     # Detailed financial info
#     expenses_other = fields.Number(attribute="last_financial_info.expenses_other")
#     expenses_for_activities = fields.Number(
#         attribute="last_financial_info.expenses_for_activities"
#     )
#     expenses_salary_for_activities = fields.Number(
#         attribute="last_financial_info.expenses_salary_for_activities"
#     )
#     other_expenses_for_activities = fields.Number(
#         attribute="last_financial_info.other_expenses_for_activities"
#     )

#     allocations_from_government = fields.Number(
#         attribute="last_financial_info.allocations_from_government"
#     )
#     allocations_from_local_authority = fields.Number(
#         attribute="last_financial_info.allocations_from_local_authority"
#     )
#     allocations_from_other_sources = fields.Number(
#         attribute="last_financial_info.allocations_from_other_sources"
#     )

#     donations_from_aboard = fields.Number(
#         attribute="last_financial_info.donations_from_aboard"
#     )
#     donations_from_israel = fields.Number(
#         attribute="last_financial_info.donations_from_israel"
#     )
#     donations_of_monetary_value = fields.Number(
#         attribute="last_financial_info.donations_of_monetary_value"
#     )

#     service_income_from_country = fields.Number(
#         attribute="last_financial_info.service_income_from_country"
#     )
#     service_income_from_local_authority = fields.Number(
#         attribute="last_financial_info.service_income_from_local_authority"
#     )
#     service_income_from_other = fields.Number(
#         attribute="last_financial_info.service_income_from_other"
#     )
#     other_income_from_other_sources = fields.Number(
#         attribute="last_financial_info.other_income_from_other_sources"
#     )
#     other_income_members_fee = fields.Number(
#         attribute="last_financial_info.other_income_members_fee"
#     )

#     @post_dump
#     def dump_schema(self, data: dict, **kwargs) -> dict:
#         """
#         Add dynamic financial fields to the schema
#         """
#         # We copy the data dict to avoid modifying the original OrderedDict
#         data_copy = data.copy()
#         for field_name, values in data.items():
#             if field_name != "financial_info_history":
#                 continue

#             for report in values:
#                 for key, label in NGO_FINANCE_DYNAMIC_KEYS.items():
#                     data_copy[f"{label} לשנת {report['report_year']}"] = report[
#                         key
#                     ]

#         # Delete to reduce response size
#         del data_copy["financial_info_history"]
#         return data_copy
