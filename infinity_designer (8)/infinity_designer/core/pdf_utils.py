"""Geração de relatórios e cupons em PDF e TXT."""

import textwrap
from fpdf import FPDF
from datetime import datetime
from zoneinfo import ZoneInfo
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
        self.cell(0, 6, datetime.now(ZoneInfo("America/Recife")).strftime("Gerado em %d/%m/%Y às %H:%M"), ln=True, align="C")
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
        f"Gerado em: {datetime.now(ZoneInfo('America/Recife')).strftime('%d/%m/%Y %H:%M')}",
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


# ---------------------------------------------------------------------------
# Ficha de pedido (gerada a partir de uma arte específica)
# ---------------------------------------------------------------------------

def gerar_ficha_pedido_pdf(arte: dict, cliente_nome: str, projeto_nome: str, categoria_nome: str) -> bytes:
    """arte: dict com descricao, valor, data, hora, programas, prazo_entrega, anotacoes"""
    pdf = BasePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 9, "Ficha de Pedido", ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, "Cliente:", border=0)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(cliente_nome), ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, "Projeto:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(projeto_nome), ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, "Tipo de arte:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(categoria_nome), ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, "Descrição:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(arte.get("descricao", "")), ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, "Valor:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _fmt(arte.get("valor", 0.0)), ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, "Prazo de entrega:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(arte.get("prazo_entrega", "") or "Não definido"), ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(45, 7, "Programas utilizados:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _safe_text(arte.get("programas", "") or "-"), ln=True)

    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Anotações:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    _multi_line(pdf, arte.get("anotacoes", "") or "Nenhuma anotação.", line_height=6)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, _safe_text(f"Arte cadastrada em {arte.get('data','')} às {arte.get('hora','')}"), ln=True)

    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Orçamentos (cliente / interno)
# ---------------------------------------------------------------------------

def gerar_orcamento_pdf_cliente(orc: dict) -> bytes:
    """orc: nome_orcamento, cliente_nome, itens[{descricao,quantidade,valor_total}],
    desconto_pct, valor_bruto, valor_final, observacoes, validade (opcional)"""
    pdf = BasePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 9, _safe_text(orc.get("nome_orcamento", "Orçamento")), ln=True)
    if orc.get("cliente_nome"):
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, _safe_text(f"Cliente: {orc['cliente_nome']}"), ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 8, "Item", border=1)
    pdf.cell(30, 8, "Qtd.", border=1, align="C")
    pdf.cell(0, 8, "Valor", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "", 10)
    for item in orc.get("itens", []):
        pdf.cell(95, 7, _safe_text(item.get("descricao", ""))[:55], border=1)
        pdf.cell(30, 7, str(item.get("quantidade", "")), border=1, align="C")
        pdf.cell(0, 7, _fmt(item.get("valor_total", 0.0)), border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Valor bruto: {_fmt(orc.get('valor_bruto', 0.0))}", ln=True, align="R")
    if orc.get("desconto_pct", 0) > 0:
        pdf.cell(0, 7, f"Desconto: {orc['desconto_pct']*100:.0f}%", ln=True, align="R")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(90, 50, 200)
    pdf.cell(0, 10, f"Valor total: {_fmt(orc.get('valor_final', 0.0))}", ln=True, align="R")

    if orc.get("observacoes"):
        pdf.set_text_color(20, 20, 20)
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Observações:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        _multi_line(pdf, orc["observacoes"], line_height=5)

    return bytes(pdf.output())


def gerar_orcamento_pdf_interno(orc: dict) -> bytes:
    """Igual ao de cliente, mas com todo o detalhamento de horas, valor/hora,
    desconto e ganho por hora real — uso exclusivo do designer."""
    pdf = BasePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 9, _safe_text(f"[INTERNO] {orc.get('nome_orcamento', 'Orçamento')}"), ln=True)
    if orc.get("cliente_nome"):
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, _safe_text(f"Cliente: {orc['cliente_nome']}"), ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(75, 8, "Item", border=1)
    pdf.cell(20, 8, "Qtd.", border=1, align="C")
    pdf.cell(25, 8, "Horas", border=1, align="C")
    pdf.cell(35, 8, "Valor/hora", border=1, align="C")
    pdf.cell(0, 8, "Valor item", border=1, align="R", ln=True)

    pdf.set_font("Helvetica", "", 9)
    for item in orc.get("itens", []):
        pdf.cell(75, 7, _safe_text(item.get("descricao", ""))[:40], border=1)
        pdf.cell(20, 7, str(item.get("quantidade", "")), border=1, align="C")
        pdf.cell(25, 7, str(item.get("horas", "")), border=1, align="C")
        pdf.cell(35, 7, _fmt(orc.get("valor_hora_usado", 0.0)), border=1, align="C")
        pdf.cell(0, 7, _fmt(item.get("valor_total", 0.0)), border=1, align="R", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, f"Tempo total estimado: {orc.get('tempo_total_horas', 0)} h", ln=True)
    pdf.cell(0, 6, f"Valor da hora utilizado: {_fmt(orc.get('valor_hora_usado', 0.0))}", ln=True)
    pdf.cell(0, 6, f"Valor bruto (sem desconto): {_fmt(orc.get('valor_bruto', 0.0))}", ln=True)
    if orc.get("desconto_pct", 0) > 0:
        pdf.cell(0, 6, f"Desconto aplicado: {orc['desconto_pct']*100:.0f}%", ln=True)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Valor final cobrado: {_fmt(orc.get('valor_final', 0.0))}", ln=True)

    if orc.get("tempo_total_horas"):
        ganho_hora_real = orc["valor_final"] / orc["tempo_total_horas"]
        pdf.set_font("Helvetica", "", 11)
        cor_ok = ganho_hora_real >= orc.get("valor_hora_usado", 0.0)
        pdf.set_text_color(0, 150, 90) if cor_ok else pdf.set_text_color(200, 60, 60)
        pdf.cell(0, 8, f"Ganho real por hora neste orçamento: {_fmt(ganho_hora_real)}", ln=True)
        pdf.set_text_color(20, 20, 20)

    if orc.get("observacoes"):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 7, "Observações:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        _multi_line(pdf, orc["observacoes"], line_height=5)

    return bytes(pdf.output())
