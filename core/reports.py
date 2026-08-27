"""Funções de agregação: totais por cliente, movimentações, finanças por período."""

import pandas as pd
from core.sheets import read_df


def _to_datetime(df, data_col="data", hora_col="hora"):
    if df.empty:
        df["_dt"] = pd.Series(dtype="datetime64[ns]")
        return df
    dt_str = df[data_col].astype(str) + " " + df.get(hora_col, "").astype(str)
    df["_dt"] = pd.to_datetime(dt_str, format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df


def cliente_totais(cliente_id: int) -> dict:
    artes = read_df("Artes")
    pagamentos = read_df("Pagamentos")
    descontos = read_df("Descontos")

    artes_c = artes[artes["cliente_id"].astype(str) == str(cliente_id)]
    pagamentos_c = pagamentos[pagamentos["cliente_id"].astype(str) == str(cliente_id)]
    descontos_c = descontos[descontos["cliente_id"].astype(str) == str(cliente_id)]

    total_vendido = artes_c["valor"].sum() if not artes_c.empty else 0.0
    total_pago = pagamentos_c["valor"].sum() if not pagamentos_c.empty else 0.0
    total_desconto = descontos_c["valor"].sum() if not descontos_c.empty else 0.0
    saldo_devedor = total_vendido - total_pago - total_desconto

    return {
        "total_vendido": round(total_vendido, 2),
        "total_pago": round(total_pago, 2),
        "total_desconto": round(total_desconto, 2),
        "saldo_devedor": round(saldo_devedor, 2),
        "qtd_artes": len(artes_c),
    }


def geral_totais() -> dict:
    artes = read_df("Artes")
    pagamentos = read_df("Pagamentos")
    descontos = read_df("Descontos")
    total_vendido = artes["valor"].sum() if not artes.empty else 0.0
    total_pago = pagamentos["valor"].sum() if not pagamentos.empty else 0.0
    total_desconto = descontos["valor"].sum() if not descontos.empty else 0.0
    a_receber = total_vendido - total_pago - total_desconto
    return {
        "total_vendido": round(total_vendido, 2),
        "total_pago": round(total_pago, 2),
        "total_desconto": round(total_desconto, 2),
        "a_receber": round(a_receber, 2),
    }


def movimentacoes_cliente(cliente_id: int) -> pd.DataFrame:
    """Retorna timeline unificada (artes, pagamentos, descontos) de um cliente."""
    categorias = read_df("Categorias").set_index("id")["nome"].to_dict() if not read_df("Categorias").empty else {}
    artes = read_df("Artes")
    pagamentos = read_df("Pagamentos")
    descontos = read_df("Descontos")

    linhas = []

    artes_c = artes[artes["cliente_id"].astype(str) == str(cliente_id)]
    for _, r in artes_c.iterrows():
        cat_nome = categorias.get(r.get("categoria_id"), "Sem categoria")
        linhas.append({
            "tipo": "Arte / Pedido",
            "descricao": f"{r.get('descricao','')} ({cat_nome})",
            "valor": r.get("valor", 0.0),
            "forma_pagamento": "",
            "data": r.get("data", ""),
            "hora": r.get("hora", ""),
        })

    pagamentos_c = pagamentos[pagamentos["cliente_id"].astype(str) == str(cliente_id)]
    for _, r in pagamentos_c.iterrows():
        linhas.append({
            "tipo": "Pagamento",
            "descricao": r.get("observacoes", ""),
            "valor": r.get("valor", 0.0),
            "forma_pagamento": r.get("forma_pagamento", ""),
            "data": r.get("data", ""),
            "hora": r.get("hora", ""),
        })

    descontos_c = descontos[descontos["cliente_id"].astype(str) == str(cliente_id)]
    for _, r in descontos_c.iterrows():
        linhas.append({
            "tipo": "Desconto",
            "descricao": r.get("motivo", ""),
            "valor": r.get("valor", 0.0),
            "forma_pagamento": "",
            "data": r.get("data", ""),
            "hora": r.get("hora", ""),
        })

    df = pd.DataFrame(linhas, columns=["tipo", "descricao", "valor", "forma_pagamento", "data", "hora"])
    df = _to_datetime(df)
    df = df.sort_values("_dt").drop(columns="_dt")
    return df.reset_index(drop=True)


def financas_periodo(periodo: str) -> pd.DataFrame:
    """periodo: 'D' diario, 'W' semanal, 'M' mensal, 'Y' anual.
    Retorna série agregada de vendas e pagamentos ao longo do tempo."""
    artes = _to_datetime(read_df("Artes"))
    pagamentos = _to_datetime(read_df("Pagamentos"))

    vendas = artes.dropna(subset=["_dt"]).set_index("_dt")["valor"].resample(periodo).sum() if not artes.empty else pd.Series(dtype=float)
    pagos = pagamentos.dropna(subset=["_dt"]).set_index("_dt")["valor"].resample(periodo).sum() if not pagamentos.empty else pd.Series(dtype=float)

    out = pd.DataFrame({"vendas": vendas, "pagamentos": pagos}).fillna(0.0)
    out = out.reset_index().rename(columns={"_dt": "periodo"})
    return out
