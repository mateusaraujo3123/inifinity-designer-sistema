"""Camada de acesso ao Google Sheets, usado como banco de dados do sistema."""

import time
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo

from core.models import SHEETS

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CACHE_TTL_SEGUNDOS = 45


@st.cache_resource(show_spinner=False)
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    gc = get_gspread_client()
    name = st.secrets.get("spreadsheet_name", "InfinityDesigner_DB")
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
            ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=len(cols) + 2)
            ws.append_row(cols)
        else:
            ws = sh.worksheet(sheet_name)
            header = ws.row_values(1)
            if header != cols:
                ws.update("A1", [cols])


@st.cache_resource(show_spinner=False)
def _worksheet(sheet_name: str):
    """Handle da aba, cacheado como recurso para não refazer fetch_sheet_metadata
    a cada chamada (essa era a principal causa de estourar a cota de leitura)."""
    sh = get_spreadsheet()
    return sh.worksheet(sheet_name)


def _build_df(sheet_name: str) -> pd.DataFrame:
    ws = _worksheet(sheet_name)
    records = ws.get_all_records()
    cols = SHEETS[sheet_name]
    df = pd.DataFrame(records, columns=cols)
    if not df.empty:
        if "id" in df.columns:
            df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
        for money_col in ("valor",):
            if money_col in df.columns:
                df[money_col] = pd.to_numeric(df[money_col], errors="coerce").fillna(0.0)
    return df


def read_df(sheet_name: str) -> pd.DataFrame:
    """Cache manual por aba (guardado na sessão do usuário), válido por
    CACHE_TTL_SEGUNDOS. Diferente de st.cache_data, permite invalidar só a
    aba que mudou em vez de limpar tudo a cada pequena edição — essencial
    para não estourar a cota de leitura da API do Google a cada clique."""
    cache_key = f"_df_{sheet_name}"
    ts_key = f"_df_ts_{sheet_name}"
    agora = time.time()
    if cache_key in st.session_state and (agora - st.session_state.get(ts_key, 0)) < CACHE_TTL_SEGUNDOS:
        return st.session_state[cache_key]
    df = _build_df(sheet_name)
    st.session_state[cache_key] = df
    st.session_state[ts_key] = agora
    return df


def next_id(df: pd.DataFrame) -> int:
    if df.empty or df["id"].isna().all():
        return 1
    return int(df["id"].max()) + 1


def _sanitize(v):
    """Converte tipos numpy/pandas (Int64, numpy.int64, NaN, etc.) para tipos
    nativos do Python, exigidos pelo serializador JSON usado pela API do Sheets."""
    if v is None or pd.isna(v):
        return ""
    if isinstance(v, (pd.Timestamp,)):
        return str(v)
    if hasattr(v, "item"):  # numpy/pandas scalar
        return v.item()
    return v


def _row_number_for_id(sheet_name: str, row_id: int):
    """Acha a linha (1-indexada, já contando o cabeçalho) de um id usando o
    DataFrame já em cache, sem gastar mais uma leitura da API (ws.find())."""
    df = read_df(sheet_name)
    if df.empty:
        return None, None
    matches = df.index[df["id"] == row_id].tolist()
    if not matches:
        return None, None
    idx = matches[0]
    return idx + 2, df.iloc[idx].to_dict()


def append_row(sheet_name: str, row: dict):
    ws = _worksheet(sheet_name)
    cols = SHEETS[sheet_name]
    ws.append_row([_sanitize(row.get(c, "")) for c in cols])


def update_row(sheet_name: str, row_id: int, updates: dict):
    row_number, current = _row_number_for_id(sheet_name, row_id)
    if row_number is None:
        return False
    ws = _worksheet(sheet_name)
    cols = SHEETS[sheet_name]
    row_values = [_sanitize(updates[c]) if c in updates else _sanitize(current.get(c, "")) for c in cols]
    ws.update(f"A{row_number}", [row_values])
    return True


def delete_row(sheet_name: str, row_id: int):
    row_number, _ = _row_number_for_id(sheet_name, row_id)
    if row_number is None:
        return False
    ws = _worksheet(sheet_name)
    ws.delete_rows(row_number)
    return True


def now_data_hora():
    n = datetime.now(ZoneInfo("America/Recife"))
    return n.strftime("%d/%m/%Y"), n.strftime("%H:%M:%S")


def clear_cache(*sheet_names: str):
    """Sem argumentos: limpa tudo (uso raro). Com nomes de abas: limpa só
    aquelas — evita forçar releitura de tudo a cada pequena edição."""
    if not sheet_names:
        for k in list(st.session_state.keys()):
            if k.startswith("_df_"):
                del st.session_state[k]
        return
    for nome in sheet_names:
        st.session_state.pop(f"_df_{nome}", None)
        st.session_state.pop(f"_df_ts_{nome}", None)


def get_config() -> dict:
    """Lê os valores base do usuário (salário desejado, computador, custos, horas).
    Se ainda não configurado, devolve os valores padrão sugeridos."""
    from core.models import CONFIG_PADRAO
    df = read_df("Configuracoes")
    if df.empty:
        return dict(CONFIG_PADRAO)
    row = df.iloc[0]
    cfg = dict(CONFIG_PADRAO)
    for k in CONFIG_PADRAO:
        try:
            cfg[k] = float(row.get(k, CONFIG_PADRAO[k]))
        except (ValueError, TypeError):
            pass
    return cfg


def save_config(cfg: dict):
    df = read_df("Configuracoes")
    row = {"id": 1, **cfg}
    if df.empty:
        append_row("Configuracoes", row)
    else:
        update_row("Configuracoes", 1, row)
    clear_cache("Configuracoes")
