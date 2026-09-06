"""Cálculos do módulo de Orçamento: valor da hora do designer, precificação de
itens avulsos e simulação de pacotes mensais com desconto progressivo."""

# (quantidade máxima da faixa, desconto aplicado)
FAIXAS_DESCONTO_PACOTE = [(5, 0.15), (10, 0.20), (float("inf"), 0.25)]

TEMPO_ESTATICA_H = 1.0
TEMPO_MOTION_H = 1.5
TEMPO_SETUP_PACOTE_H = 1.0


def calcular_valor_hora(cfg: dict) -> dict:
    """cfg: salario_desejado, valor_computador, custos_extras, horas_trabalho_mes"""
    depreciacao = cfg["valor_computador"] / 36 if cfg["valor_computador"] else 0.0
    custo_mensal_total = cfg["salario_desejado"] + depreciacao + cfg["custos_extras"]
    valor_hora = custo_mensal_total / cfg["horas_trabalho_mes"] if cfg["horas_trabalho_mes"] else 0.0
    return {
        "depreciacao_mensal": round(depreciacao, 2),
        "custo_mensal_total": round(custo_mensal_total, 2),
        "valor_hora": round(valor_hora, 2),
    }


def desconto_para_quantidade(qtd: int) -> float:
    for limite, desconto in FAIXAS_DESCONTO_PACOTE:
        if qtd <= limite:
            return desconto
    return FAIXAS_DESCONTO_PACOTE[-1][1]


def calcular_item_avulso(horas: float, quantidade: float, valor_hora: float) -> float:
    return round(horas * quantidade * valor_hora, 2)


def calcular_pacote(qtd_estaticas: int, qtd_motions: int, valor_hora: float) -> dict:
    tempo_estaticas = qtd_estaticas * TEMPO_ESTATICA_H
    tempo_motions = qtd_motions * TEMPO_MOTION_H
    tempo_total = tempo_estaticas + tempo_motions + TEMPO_SETUP_PACOTE_H

    valor_avulso = (tempo_estaticas + tempo_motions) * valor_hora
    qtd_total = qtd_estaticas + qtd_motions
    desconto = desconto_para_quantidade(qtd_total)
    valor_pacote = valor_avulso * (1 - desconto)
    ganho_hora_pacote = (valor_pacote / tempo_total) if tempo_total else 0.0

    return {
        "qtd_estaticas": qtd_estaticas,
        "qtd_motions": qtd_motions,
        "qtd_total": qtd_total,
        "tempo_estaticas": round(tempo_estaticas, 2),
        "tempo_motions": round(tempo_motions, 2),
        "tempo_setup": TEMPO_SETUP_PACOTE_H,
        "tempo_total": round(tempo_total, 2),
        "valor_avulso": round(valor_avulso, 2),
        "desconto_pct": desconto,
        "valor_pacote": round(valor_pacote, 2),
        "ganho_hora_pacote": round(ganho_hora_pacote, 2),
    }
