"""Camada de acesso ao Google Sheets, usado como banco de dados do sistema."""

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

from core.models import SHEETS


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@st.cache_resource(show_spinner=False)
def get_gspread_client():
    creds_dict = st.secrets["gcp_service_account"].to_dict()

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=SCOPES
    )

    return gspread.authorize(creds)


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    gc = get_gspread_client()

    name = st.secrets.get(
        "spreadsheet_name",
        "InfinityDesigner_DB"
    )

    try:
        sh = gc.open(name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(name)

    ensure_worksheets(sh)

    return sh


def ensure_worksheets(sh):
    existing = [ws.title for ws in sh.worksheets()]

    for sheet_name, cols in SHEETS.items():

        if sheet_name not in existing:
            ws = sh.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=len(cols) + 2
            )

            ws.append_row(cols)

        else:
            ws = sh.worksheet(sheet_name)

            header = ws.row_values(1)

            if header != cols:
                ws.update("A1", [cols])


def _worksheet(sheet_name: str):
    sh = get_spreadsheet()
    return sh.worksheet(sheet_name)


def read_df(sheet_name: str) -> pd.DataFrame:
    ws = _worksheet(sheet_name)

    records = ws.get_all_records()

    cols = SHEETS[sheet_name]

    df = pd.DataFrame(records, columns=cols)

    if not df.empty:

        if "id" in df.columns:
            df["id"] = pd.to_numeric(
                df["id"],
                errors="coerce"
            ).astype("Int64")

        for money_col in ("valor",):

            if money_col in df.columns:
                df[money_col] = pd.to_numeric(
                    df[money_col],
                    errors="coerce"
                ).fillna(0.0)

    return df


def next_id(df: pd.DataFrame) -> int:

    if df.empty or df["id"].isna().all():
        return 1

    return int(df["id"].max()) + 1


def append_row(sheet_name: str, row: dict):

    ws = _worksheet(sheet_name)

    cols = SHEETS[sheet_name]

    ws.append_row([
        row.get(c, "")
        for c in cols
    ])


def update_row(
    sheet_name: str,
    row_id: int,
    updates: dict
):

    ws = _worksheet(sheet_name)

    cols = SHEETS[sheet_name]

    id_col_idx = cols.index("id") + 1

    cell = ws.find(
        str(row_id),
        in_column=id_col_idx
    )

    if cell is None:
        return False

    row_values = ws.row_values(cell.row)

    row_values += [
        ""
        for _ in range(len(cols) - len(row_values))
    ]

    for k, v in updates.items():

        if k in cols:
            row_values[cols.index(k)] = v

    ws.update(
        f"A{cell.row}",
        [row_values]
    )

    return True


def delete_row(
    sheet_name: str,
    row_id: int
):

    ws = _worksheet(sheet_name)

    cols = SHEETS[sheet_name]

    id_col_idx = cols.index("id") + 1

    cell = ws.find(
        str(row_id),
        in_column=id_col_idx
    )

    if cell is not None:

        ws.delete_rows(cell.row)

        return True

    return False


def now_data_hora():

    n = datetime.now()

    return (
        n.strftime("%d/%m/%Y"),
        n.strftime("%H:%M:%S")
    )


def clear_cache():

    st.cache_data.clear()
    st.cache_resource.clear()
