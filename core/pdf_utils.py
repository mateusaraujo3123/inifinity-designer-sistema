"""Geração de relatórios e cupons em PDF e TXT."""

import textwrap
from fpdf import FPDF
from datetime import datetime
from core.sheets import read_df
from core.reports import cliente_totais, movimentacoes_cliente


def _cliente_nome(cliente_id: int) -> str:
    clientes = read_df("Clientes")
    row = clientes[clientes["id"].astype(str) == str(cliente_id)]
    return row.iloc[0]["nome"] if not row.empty else f"Cliente {cliente_id}"


def _fmt(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _safe_text(text) -> str:
    """Remove caracteres que a fonte padrão (latin-1) não consegue desenhar,
    evitando que textos com emojis/símbolos quebrem a geração do PDF."""
    text = "" if text is None else str(text)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _multi_line(pdf, text, line_height=5, max_chars=95):
    """Escreve texto em várias linhas manualmente (em vez de multi_cell),
    evitando o erro do fpdf2 quando encontra palavras muito longas ou
    caracteres que não cabem na largura calculada internamente."""
    text = _safe_text(text)
    if not text.strip():
        pdf.cell(0, line_height, "", ln=True)
        return
    for paragrafo in text.split("\n") or [""]:
        linhas = textwrap.wrap(paragrafo, width=max_chars, break_long_words=True) or [""]
        for linha in linhas:
            pdf.cell(0, line_height, linha, ln=True)


class BasePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(90, 50, 200)
        self.cell(0, 10, "Infinity Designer", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, datetime.now().strftime("Gerado em %d/%m/%Y às %H:%M"), ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def gerar_cupom_pdf(cliente_id: int, tipo: str = "simples") -> bytes:
    """tipo: 'simples' ou 'completo'"""
    nome = _cliente_nome(cliente_id)
    totais = cliente_totais(cliente_id)
    artes = read_df("Artes")
    categorias = read_df("Categorias").set_index("id")["nome"].to_dict() if not read_df("Categorias").empty else {}
    artes_c = artes[artes["cliente_id"].astype(str) == str(cliente_id)]

    pdf = BasePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, _safe_text(f"Cupom {'Completo' if tipo=='completo' else 'Simples'} - {nome}"), ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Quantidade total de artes: {totais['qtd_artes']}", ln=True)
    pdf.cell(0, 7, f"Valor total de vendas: {_fmt(totais['total_vendido'])}", ln=True)
    pdf.cell(0, 7, f"Valor já pago: {_fmt(totais['total_pago'])}", ln=True)
    pdf.cell(0, 7, f"Descontos: {_fmt(totais['total_desconto'])}", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Valor devido: {_fmt(totais['saldo_devedor'])}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Artes / Itens:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for _, r in artes_c.iterrows():
        cat_nome = categorias.get(r.get("categoria_id"), "Sem categoria")
        _multi_line(pdf, f"- {r.get('descricao','')} [{cat_nome}] : {_fmt(r.get('valor',0.0))}", line_height=6)

    if tipo == "completo":
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Relatório completo de movimentações:", ln=True)
        pdf.set_font("Helvetica", "", 9)
        mov = movimentacoes_cliente(cliente_id)
        for _, r in mov.iterrows():
            linha = f"[{r['data']} {r['hora']}] {r['tipo']}: {r['descricao']} - {_fmt(r['valor'])}"
            if r["forma_pagamento"]:
                linha += f" ({r['forma_pagamento']})"
            _multi_line(pdf, linha, line_height=5)

    return bytes(pdf.output())


def gerar_relatorio_pdf(cliente_id: int) -> bytes:
    nome = _cliente_nome(cliente_id)
    totais = cliente_totais(cliente_id)
    mov = movimentacoes_cliente(cliente_id)

    pdf = BasePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _safe_text(f"Relatório de Movimentações - {nome}"), ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Total vendido: {_fmt(totais['total_vendido'])}   |   Pago: {_fmt(totais['total_pago'])}   |   Descontos: {_fmt(totais['total_desconto'])}", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Saldo devedor: {_fmt(totais['saldo_devedor'])}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 7, "Data", border=1)
    pdf.cell(20, 7, "Hora", border=1)
    pdf.cell(30, 7, "Tipo", border=1)
    pdf.cell(70, 7, "Descrição", border=1)
    pdf.cell(25, 7, "Valor", border=1)
    pdf.cell(0, 7, "Pagamento", border=1, ln=True)

    pdf.set_font("Helvetica", "", 9)
    for _, r in mov.iterrows():
        pdf.cell(35, 6, _safe_text(r["data"]), border=1)
        pdf.cell(20, 6, _safe_text(r["hora"]), border=1)
        pdf.cell(30, 6, _safe_text(r["tipo"]), border=1)
        pdf.cell(70, 6, _safe_text(str(r["descricao"])[:38]), border=1)
        pdf.cell(25, 6, _fmt(r["valor"]), border=1)
        pdf.cell(0, 6, _safe_text(r["forma_pagamento"]), border=1, ln=True)

    return bytes(pdf.output())


def gerar_relatorio_txt(cliente_id: int) -> str:
    nome = _cliente_nome(cliente_id)
    totais = cliente_totais(cliente_id)
    mov = movimentacoes_cliente(cliente_id)

    linhas = [
        "=== INFINITY DESIGNER - RELATÓRIO DE MOVIMENTAÇÕES ===",
        f"Cliente: {nome}",
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        f"Total vendido: {_fmt(totais['total_vendido'])}",
        f"Total pago: {_fmt(totais['total_pago'])}",
        f"Descontos: {_fmt(totais['total_desconto'])}",
        f"Saldo devedor: {_fmt(totais['saldo_devedor'])}",
        "",
        "--- Movimentações ---",
    ]
    for _, r in mov.iterrows():
        linha = f"[{r['data']} {r['hora']}] {r['tipo']}: {r['descricao']} - {_fmt(r['valor'])}"
        if r["forma_pagamento"]:
            linha += f" ({r['forma_pagamento']})"
        linhas.append(linha)

    return "\n".join(linhas)
