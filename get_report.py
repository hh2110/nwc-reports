from typing import Any, TypedDict

import pandas as pd  # type: ignore
import plotly.graph_objects as go  # type: ignore
from plotly.subplots import make_subplots  # type: ignore

REVENUE_GENERATING_CATEGORIES = [
    "Consultation",
    "Lab",
    "Radiology",
    "Procedure",
    "Lab",
    "Consumable",
    "Drug",
]


class DataFrameOperations:
    @staticmethod
    def rename_cols(df: pd.DataFrame) -> pd.DataFrame:
        rename_col_list = []
        for col_list in df.columns:
            new_col_name = ""
            for col in col_list:
                if "Unnamed" not in col:
                    new_col_name += f"{col}_"

            rename_col_list.append(new_col_name[:-1])
        df.columns = rename_col_list

        return df

    @staticmethod
    def focus_on_specific_columns(df: pd.DataFrame) -> pd.DataFrame:
        required_cols = []
        for col in df.columns:
            if "_Net_" in col:
                required_cols.append(col)

        required_cols += [
            "Net Revenue",
            "Ins.",
            "Policy Name",
            "New Reg.",
            "Old Reg.",
            "Speciality",
            "Doctor Name",
            "(CVR) Date",
        ]
        df = df[required_cols]
        df["(CVR) Date"] = df["(CVR) Date"].apply(lambda x: x.strftime("%Y-%m-%d"))

        return df

    @staticmethod
    def get_revenue_per_category(df: pd.DataFrame) -> pd.DataFrame:
        remove_cols = []
        for category in REVENUE_GENERATING_CATEGORIES:
            df[category] = df[category + "_Net_Cash"] + df[category + "_Net_Ins."]
            remove_cols.append(category + "_Net_Cash")
            remove_cols.append(category + "_Net_Ins.")
        df.drop(remove_cols, axis=1, inplace=True)

        return df


def get_df_from_excel(file_name: Any) -> pd.DataFrame:
    df = pd.read_excel(file_name, header=[3, 4, 5], skipfooter=8, index_col=0)
    df = df.dropna(axis=1, how="all")
    # Join the multi-index column names with underscore
    df = DataFrameOperations.rename_cols(df)
    df = DataFrameOperations.focus_on_specific_columns(df)
    df = DataFrameOperations.get_revenue_per_category(df)

    return df


class Indicator(TypedDict):
    value: float
    title: str


class PieChart(TypedDict):
    labels: list[str]
    values: list[float]
    textinfo: str


class Report:
    @staticmethod
    def calculate_number_of_episodes(df: pd.DataFrame) -> Indicator:
        number = df[REVENUE_GENERATING_CATEGORIES].map(lambda x: x != 0).sum().sum()
        return Indicator(value=number, title="Revenue Generating<br>Episodes")

    @staticmethod
    def calculate_number_of_patients(df: pd.DataFrame) -> Indicator:
        return Indicator(value=df.shape[0], title="Number of Patients")

    @staticmethod
    def calculate_net_revnenue(df: pd.DataFrame) -> Indicator:
        return Indicator(value=df["Net Revenue"].sum(), title="Net Revenue")

    @staticmethod
    def calculate_new_vs_old_reg(df: pd.DataFrame) -> PieChart:
        new_reg = df["New Reg."].sum()
        old_reg = df["Old Reg."].sum()
        return PieChart(
            labels=["New", "Old"],
            values=[new_reg, old_reg],
            textinfo="label+value",
        )

    @staticmethod
    def calculate_revenue_per_speciality(df: pd.DataFrame) -> PieChart:
        revenue_per_speciality = df.groupby("Speciality").sum()["Net Revenue"]
        return PieChart(
            labels=[i[:6] for i in revenue_per_speciality.index.tolist()],
            values=revenue_per_speciality.tolist(),
            textinfo="label+value",
        )

    @staticmethod
    def calculate_insurance_vs_non_insurance(df: pd.DataFrame) -> PieChart:
        insurance = df["Ins."].sum()
        non_insurance = df["Net Revenue"].sum() - insurance
        return PieChart(
            labels=["Non Ins", "Ins"],
            values=[non_insurance, insurance],
            textinfo="label+value",
        )

    @staticmethod
    def calculate_episodes_per_category(df: pd.DataFrame) -> PieChart:
        episodes_per_category = {}
        for category in REVENUE_GENERATING_CATEGORIES:
            episodes = df[[category]].map(lambda x: x != 0).sum().sum()
            if episodes != 0:
                episodes_per_category[category] = episodes

        return PieChart(
            labels=list(episodes_per_category.keys()),
            values=list(episodes_per_category.values()),
            textinfo="label+value",
        )

    @staticmethod
    def make_plot(df: pd.DataFrame) -> Any:
        # Create subplots: 2 rows, 3 cols
        fig = make_subplots(
            rows=3,
            cols=3,
            specs=[
                [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}],
                [{"type": "pie"}, {"type": "pie"}, {"type": "pie"}],
            ],
            vertical_spacing=0.1,
            row_heights=[0.2, 0.4, 0.4],
            x_title=df["(CVR) Date"].iloc[0],
        )

        # Add indicators row 1
        fig.add_trace(
            go.Indicator(mode="number", **Report.calculate_number_of_episodes(df)),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Indicator(mode="number", **Report.calculate_number_of_patients(df)),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Indicator(mode="number", **Report.calculate_net_revnenue(df)),
            row=1,
            col=3,
        )

        # Add pie charts row 2
        fig.add_trace(
            go.Pie(**Report.calculate_episodes_per_category(df)), row=2, col=1
        )
        fig.add_trace(go.Pie(**Report.calculate_new_vs_old_reg(df)), row=2, col=2)
        fig.add_trace(
            go.Pie(**Report.calculate_revenue_per_speciality(df)), row=2, col=3
        )

        # Add pie charts row 3
        fig.add_trace(
            go.Pie(**Report.calculate_insurance_vs_non_insurance(df)), row=3, col=3
        )

        fig.update_layout(height=800, width=1000, showlegend=False)

        return fig
