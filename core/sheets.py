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


def _normalizar_private_key(key):
    """Normaliza a private_key recebida pelo Streamlit."""

    if key is None:
        raise ValueError("private_key não encontrada nos Secrets.")

    key = str(key).strip()

    # Remove aspas que possam ter sido armazenadas como parte do valor
    if len(key) >= 2:
        if key.startswith('"') and key.endswith('"'):
            key = key[1:-1]

        elif key.startswith("'") and key.endswith("'"):
            key = key[1:-1]

    # Converte diferentes representações de quebra de linha
    key = key.replace("\\\\r\\\\n", "\n")
    key = key.replace("\\\\n", "\n")
    key = key.replace("\\r\\n", "\n")
    key = key.replace("\\n", "\n")
    key = key.replace("\r\n", "\n")
    key = key.replace("\r", "\n")

    # Garante que o PEM começa e termina corretamente
    begin = "-----BEGIN PRIVATE KEY-----"
    end = "-----END PRIVATE KEY-----"

    begin_pos = key.find(begin)
    end_pos = key.find(end)

    if begin_pos == -1:
        raise ValueError(
            "A private_key não contém -----BEGIN PRIVATE KEY-----. "
            "Verifique o Secrets."
        )

    if end_pos == -1:
        raise ValueError(
            "A private_key não contém -----END PRIVATE KEY-----. "
            "Verifique o Secrets."
        )

    # Remove qualquer coisa antes/depois do PEM
    key = key[begin_pos:end_pos + len(end)]

    # Normaliza espaços nas linhas
    linhas = [
        linha.strip()
        for linha in key.split("\n")
        if linha.strip()
    ]

    key = "\n".join(linhas)

    # Confere novamente
    if not key.startswith(begin):
        raise ValueError("Início da private_key inválido.")

    if not key.endswith(end):
        raise ValueError("Final da private_key inválido.")

    return key + "\n"


@st.cache_resource(show_spinner=False)
def get_gspread_client():

    if "gcp_service_account" not in st.secrets:
        raise ValueError(
            "A seção [gcp_service_account] não foi encontrada "
            "no Streamlit Secrets."
        )

    creds_dict = dict(
        st.secrets["gcp_service_account"]
    )

    if "private_key" not in creds_dict:
        raise ValueError(
            "private_key não encontrada em [gcp_service_account]."
        )

    # Corrige automaticamente o formato da chave
    creds_dict["private_key"] = _normalizar_private_key(
        creds_dict["private_key"]
    )

    # Remove valores que não fazem parte da credencial
    creds_dict.pop("spreadsheet_name", None)

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

    existing = [
        ws.title
        for ws in sh.worksheets()
    ]

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

                ws.update(
                    "A1",
                    [cols]
                )


def _worksheet(sheet_name: str):

    sh = get_spreadsheet()

    return sh.worksheet(sheet_name)


def read_df(sheet_name: str) -> pd.DataFrame:

    ws = _worksheet(sheet_name)

    records = ws.get_all_records()

    cols = SHEETS[sheet_name]

    df = pd.DataFrame(
        records,
        columns=cols
    )

    if not df.empty:

        if "id" in df.columns:

            df["id"] = pd.to_numeric(
                df["id"],
                errors="coerce"
            ).astype("Int64")

        if "valor" in df.columns:

            df["valor"] = pd.to_numeric(
                df["valor"],
                errors="coerce"
            ).fillna(0.0)

    return df


def next_id(df: pd.DataFrame) -> int:

    if df.empty or df["id"].isna().all():

        return 1

    return int(
        df["id"].max()
    ) + 1


def append_row(
    sheet_name: str,
    row: dict
):

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

    id_col_idx = (
        cols.index("id") + 1
    )

    cell = ws.find(
        str(row_id),
        in_column=id_col_idx
    )

    if cell is None:

        return False

    row_values = ws.row_values(
        cell.row
    )

    row_values += [
        ""
        for _ in range(
            len(cols) - len(row_values)
        )
    ]

    for key, value in updates.items():

        if key in cols:

            row_values[
                cols.index(key)
            ] = value

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

    id_col_idx = (
        cols.index("id") + 1
    )

    cell = ws.find(
        str(row_id),
        in_column=id_col_idx
    )

    if cell is not None:

        ws.delete_rows(
            cell.row
        )

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
