from typing import List, Optional
import pandas as pd
import numpy as np
from pandas.core.groupby.generic import DataFrameGroupBy


class Rank:
    d = 40
    c = 60
    b = 80
    a = 100


def growth_rank(growth_ratio: float) -> int:
    if growth_ratio < -0.1:
        return Rank.d
    if growth_ratio < -0.05:
        return Rank.c
    if growth_ratio < 0.05:
        return Rank.b
    return Rank.a


def balance_rank(balance_ratio: float) -> int:
    if balance_ratio < -0.1:
        return Rank.d
    if balance_ratio < -0.05:
        return Rank.c
    if balance_ratio < 0.05:
        return Rank.b
    return Rank.a


def stability_rank(max_income_ratio: float) -> int:
    if max_income_ratio < 0.5:
        return Rank.a
    if max_income_ratio < 0.7:
        return Rank.b
    if max_income_ratio < 0.9:
        return Rank.c
    return Rank.d


def compute_turnover_growth_ratio(
    *,
    last_turnover: Optional[float],
    previous_turnover: Optional[float],
    previous_previous_turnover: Optional[float],
) -> float:
    """Calculate the turnover growth ratio between turnovers.
    If the last turnover is missing, we assume that the NGO didn't report it's financial info, or closed, and we return -0.25.
    If the  NGO turnover is small, we assume the growth ratio is not meaningful, and we return 1.
    Otherwise, we calculate the growth ratio using the formula: (new_turnover / old_turnover)^(1 / year_diff) - 1
    """

    if not last_turnover:
        # If the last turnover is missing, we assume that the NGO didn't report it's financial info, or closed, and we return -0.25.
        return -0.25

    # Determines the year of the old financial report 1 year ago or 2 years ago.
    if previous_previous_turnover and previous_previous_turnover > 25_000:
        old_turnover = previous_previous_turnover
        years_diff = 2
    elif previous_turnover and previous_turnover > 25_000:
        # If the previous year turnover exists and is greater than 25,000 NIS, we use it as the old financial info.
        old_turnover = previous_turnover
        years_diff = 1
    else:
        # If the old NGO turnover is less than 25,000 NIS, we assume the growth ratio isn't relevant, so we return 1.
        return 1.0

    return (last_turnover / old_turnover) ** (1 / years_diff) - 1


def percentile_label(percentile: int) -> str:
    match percentile:
        case 1:
            return "נמוך מאוד ביחס לקט' מחזור"
        case 2:
            return "נמוך ביחס לקט' מחזור"
        case 3:
            return "דומה ביחס לקט' מחזור"
        case 4:
            return "גבוה ביחס לקט' מחזור"
        case 5:
            return "גבוה מאוד ביחס לקט' מחזור"
        case _:
            raise ValueError("No matching percentile: ", percentile)


def rank_ngos(financial_df: DataFrameGroupBy) -> List[pd.DataFrame]:
    """Rank the NGOs based on their financial reports.
    The ranks are calculated for each year and for each ratio,
    based on the NGO's turnover category.
    The given financial_df is a grouped dataframe,
    where each group represents the financial reports of a single year.

    """
    # To fixSettingWithCopyWarning:  https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas
    pd.options.mode.chained_assignment = None  # default='warn'

    max_year = max(financial_df.groups.keys())
    # Merge the financial reports in order to calculate the ratios
    merged_df = pd.DataFrame()
    # Merge the grouped financial reports for each year
    for year in financial_df.groups.keys():
        group = financial_df.get_group(year)
        # Get the financial reports for the current year
        if merged_df.empty:
            merged_df = group
        else:
            # Merge the current year financial reports with the previous years
            merged_df = merged_df.merge(
                group, on="ngo_id", how="outer", suffixes=("", f"_{year}")
            )

    financial_infos = []
    # Define for how many years including the last one we want to calculate the ranks for.
    num_of_years_to_rank = 3
    years_to_rank = range(max_year, max_year - num_of_years_to_rank, -1)

    for year in years_to_rank:
        # Get the financial reports for the current year
        financial_info = financial_df.get_group(year)
        # Add Multi-years ratios
        growth_ratios = merged_df.apply(
            lambda row: compute_turnover_growth_ratio(
                last_turnover=row.get(f"yearly_turnover_{year}", None),
                previous_turnover=row.get(f"yearly_turnover_{year - 1}", None),
                previous_previous_turnover=row.get(f"yearly_turnover_{year - 2}", None),
            ),
            axis=1,
        )
        # Merge it with the multi-years ratios
        financial_info = financial_info.merge(
            pd.DataFrame(
                {"ngo_id": merged_df["ngo_id"], "growth_ratio": growth_ratios}
            ),
            on="ngo_id",
            how="left",
        )

        # Merge the financial reports for the current year with the multi-years ratios
        for i in range(1, 3):
            financial_info = financial_info.merge(
                merged_df[["ngo_id", f"yearly_turnover_{year-i}"]],
                on="ngo_id",
                how="left",
            )

        # Rank the ngo based on the ratios for each year
        financial_info["growth_rank"] = (
            financial_info["growth_ratio"].apply(growth_rank).astype(int)
        )
        financial_info["balance_rank"] = (
            financial_info["balance_ratio"].apply(balance_rank).astype(int)
        )
        financial_info["stability_rank"] = (
            financial_info["max_income_ratio"].apply(stability_rank).astype(int)
        )

        # Calculate the main rank for each year
        financial_info["main_rank"] = (
            0.4 * financial_info["growth_rank"]
            + 0.4 * financial_info["balance_rank"]
            + 0.2 * financial_info["stability_rank"]
        ).astype(int)

        # Add means and percentile relative to the turnover category.

        # Calculate the percentile
        grouped_df = financial_info.groupby("yearly_turnover_category")
        financial_info["percentile_num"] = np.ceil(
            grouped_df["main_rank"].transform("rank", pct=True).values / 0.2
        ).astype(int)
        financial_info["percentile_label"] = financial_info["percentile_num"].apply(
            percentile_label
        )

        # Add the means for each ratio for each turnover category
        financial_info["admin_expense_benchmark"] = grouped_df[
            "admin_expense_ratio"
        ].transform("mean")
        financial_info["growth_benchmark"] = grouped_df["growth_ratio"].transform(
            "mean"
        )
        financial_info["balance_benchmark"] = grouped_df["balance_ratio"].transform(
            "mean"
        )
        financial_info["max_income_benchmark"] = grouped_df[
            "max_income_ratio"
        ].transform("mean")
        # Add the mean for the main rank for each turnover category
        financial_info["main_rank_benchmark"] = grouped_df["main_rank"].transform(
            "mean"
        )

        financial_infos.append(financial_info)

    # Calculate the differences between the yearly ranks (21vs20, 20vs19 etc).
    for idx, financial_info in enumerate(financial_infos[: len(financial_infos) - 1]):
        year = financial_info["report_year"]
        previous_financial_info = financial_infos[idx + 1]

        year_diff_suffix = "_vs_previous_year_rank"

        financial_info[f"main_rank{year_diff_suffix}"] = (
            financial_info["main_rank"] - previous_financial_info["main_rank"]
        )
        financial_info[f"growth_rank{year_diff_suffix}"] = (
            financial_info["growth_rank"] - previous_financial_info["growth_rank"]
        )
        financial_info[f"balance_rank{year_diff_suffix}"] = (
            financial_info["balance_rank"] - previous_financial_info["balance_rank"]
        )
        financial_info[f"stability_rank{year_diff_suffix}"] = (
            financial_info["stability_rank"] - previous_financial_info["stability_rank"]
        )

    return financial_infos
