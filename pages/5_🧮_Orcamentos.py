import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from fpdf import FPDF

st.set_page_config(page_title="Orçamentos - Infinity Designer", page_icon="🧮", layout="wide")
st.title("🧮 Orçamentos")
st.caption("Calcule sua hora mínima, monte pacotes com desconto de escala e exporte propostas em PDF")


# ---------- Helpers ----------

def fmt_brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def safe_text(text) -> str:
    text = "" if text is None else str(text)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class BasePDF(FPDF):
    def __init__(self, titulo_header):
        super().__init__()
        self._titulo_header = titulo_header

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(90, 50, 200)
        self.cell(0, 10, safe_text(self._titulo_header), ln=True, align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        agora = datetime.now(ZoneInfo("America/Recife")).strftime("Gerado em %d/%m/%Y às %H:%M")
        self.cell(0, 6, agora, ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def gerar_pdf_cliente(dados: dict) -> bytes:
    pdf = BasePDF("Infinity Designer — Proposta Comercial")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, safe_text(f"Proposta para: {dados['cliente']}"), ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, safe_text(f"Escopo: {dados['qtd_estaticas']} arte(s) estática(s) e {dados['qtd_motions']} arte(s) motion"), ln=True)
    pdf.cell(0, 7, safe_text(f"Prazo estimado: {dados['prazo_dias']} dia(s) útil(eis)"), ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Condições da Proposta", ln=True)
    pdf.set_font("Helvetica", "", 10)
    termos = [
        "- Inclui até 2 rodadas de ajustes por arte.",
        "- Alterações adicionais ou fora do escopo serão orçadas à parte.",
        "- Prazo de entrega contado a partir da aprovação do briefing e envio de materiais.",
        "- Pagamento: 50% na aprovação da proposta e 50% na entrega final.",
        "- Proposta válida por 7 dias corridos a partir da data de emissão.",
    ]
    for t in termos:
        pdf.cell(0, 6, safe_text(t), ln=True)
    pdf.ln(6)

    pdf.set_fill_color(245, 240, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(90, 50, 200)
    pdf.cell(0, 12, safe_text(f"Valor Final do Pacote: {fmt_brl(dados['valor_pacote'])}"), ln=True, align="C", fill=True)
    pdf.ln(15)

    pdf.set_text_color(20, 20, 20)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "_________________________________________", ln=True, align="C")
    pdf.cell(0, 6, safe_text(f"{dados['cliente']} — Assinatura / De acordo"), ln=True, align="C")

    return bytes(pdf.output())


def gerar_pdf_interno(dados: dict) -> bytes:
    pdf = BasePDF("Infinity Designer — Dashboard Interno")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 8, safe_text(f"Análise do Pacote — {dados['cliente']}"), ln=True)
    pdf.ln(2)

    def linha(label, valor, negrito=False):
        pdf.set_font("Helvetica", "B" if negrito else "", 10)
        pdf.cell(90, 7, safe_text(label), border=1)
        pdf.cell(0, 7, safe_text(valor), border=1, ln=True)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Custos Fixos Mensais", ln=True)
    linha("Salário desejado", fmt_brl(dados["salario"]))
    linha("Depreciação do computador", fmt_brl(dados["depreciacao"]))
    linha("Custos extras (luz/internet/softwares)", fmt_brl(dados["custos_extras"]))
    linha("Custo mensal total", fmt_brl(dados["custo_mensal_total"]), True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Precificação Base", ln=True)
    linha("Margem/reserva de emergência", f"{dados['margem_pct']:.1f}% ({fmt_brl(dados['margem_valor'])})")
    linha("Impostos/taxas", f"{dados['impostos_pct']:.1f}% ({fmt_brl(dados['impostos_valor'])})")
    linha("Faturamento mínimo necessário", fmt_brl(dados["faturamento_minimo"]), True)
    linha("Horas focadas/mês", f"{dados['horas_focadas']:.0f} h")
    linha("Valor da hora mínima", fmt_brl(dados["valor_hora_minima"]), True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Pacote Orçado", ln=True)
    linha("Artes estáticas", str(dados["qtd_estaticas"]))
    linha("Artes motion", str(dados["qtd_motions"]))
    linha("Horas totais estimadas", f"{dados['tempo_total']:.2f} h")
    linha("Valor avulso (sem desconto)", fmt_brl(dados["valor_avulso"]))
    linha("Desconto aplicado", f"{dados['desconto_pct']:.0f}%")
    linha("Valor final do pacote", fmt_brl(dados["valor_pacote"]), True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Eficiência e Lucro Real", ln=True)
    linha("Ganho real por hora", fmt_brl(dados["ganho_real_hora"]), True)
    linha("Diferença vs. hora mínima", fmt_brl(dados["ganho_real_hora"] - dados["valor_hora_minima"]))
    lucro_real = dados["valor_pacote"] - dados["impostos_valor_pacote"] - (dados["custo_mensal_total"] / dados["horas_focadas"] * dados["tempo_total"])
    linha("Lucro real gerado (após custos e impostos)", fmt_brl(lucro_real), True)

    return bytes(pdf.output())


# ---------- Configuração Base (sidebar) ----------

st.sidebar.header("⚙️ Configuração Base — Orçamentos")
salario = st.sidebar.number_input("Salário Desejado (R$/mês)", min_value=0.0, value=1600.0, step=50.0, key="orc_salario")
valor_pc = st.sidebar.number_input("Valor do Computador (R$)", min_value=0.0, value=2000.0, step=100.0, key="orc_pc")
custos_extras = st.sidebar.number_input("Custos Extras (R$/mês)", min_value=0.0, value=145.0, step=5.0, key="orc_extras")
horas_focadas = st.sidebar.number_input("Horas Focadas/Mês", min_value=1.0, value=80.0, step=1.0, key="orc_horas")
margem_pct = st.sidebar.number_input("Margem de Lucro/Reserva (%)", min_value=0.0, value=10.0, step=1.0, key="orc_margem")
impostos_pct = st.sidebar.number_input("Impostos/Taxas (%) (ex: MEI)", min_value=0.0, value=6.0, step=0.5, key="orc_impostos")

depreciacao = valor_pc / 36
custo_mensal_total = salario + depreciacao + custos_extras
margem_valor = custo_mensal_total * (margem_pct / 100)
impostos_valor = custo_mensal_total * (impostos_pct / 100)
faturamento_minimo = custo_mensal_total + margem_valor + impostos_valor
valor_hora_minima = faturamento_minimo / horas_focadas

st.sidebar.divider()
st.sidebar.metric("Depreciação/mês", fmt_brl(depreciacao))
st.sidebar.metric("Valor da Hora Mínima", fmt_brl(valor_hora_minima))


# ---------- Gerador de Pacotes ----------

st.subheader("📦 Gerador de Pacotes Mensais")
col_a, col_b, col_c = st.columns(3)
with col_a:
    qtd_estaticas = st.number_input("Qtd. Artes Estáticas", min_value=0, value=4, step=1)
with col_b:
    qtd_motions = st.number_input("Qtd. Artes Motion", min_value=0, value=2, step=1)
with col_c:
    cliente_nome = st.text_input("Nome do Cliente", value="")

total_artes = qtd_estaticas + qtd_motions
tempo_total = (qtd_estaticas * 1.0) + (qtd_motions * 1.5) + 1.0  # +1h fixo de setup/briefing
valor_avulso = tempo_total * valor_hora_minima

if total_artes <= 5:
    desconto_pct = 15
elif total_artes <= 10:
    desconto_pct = 20
else:
    desconto_pct = 25

valor_pacote = valor_avulso * (1 - desconto_pct / 100) if total_artes > 0 else 0.0
ganho_real_hora = (valor_pacote / tempo_total) if tempo_total > 0 else 0.0

horas_dia = horas_focadas / 20 if horas_focadas > 0 else 4.0  # referência: 80h/mês = 4h/dia, 20 dias/mês
prazo_dias = max(1, round(tempo_total / horas_dia)) if horas_dia > 0 else 1

st.divider()

# ---------- Painel de Validação Financeira ----------

st.subheader("📊 Painel de Validação Financeira")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Valor Avulso (sem desconto)", fmt_brl(valor_avulso))
m2.metric(f"Valor com Desconto ({desconto_pct}%)", fmt_brl(valor_pacote))
m3.metric("Horas Totais Estimadas", f"{tempo_total:.2f} h")
m4.metric("Ganho Real por Hora", fmt_brl(ganho_real_hora))

if total_artes == 0:
    st.warning("Adicione ao menos uma arte (estática ou motion) para calcular o pacote.")
elif ganho_real_hora < valor_hora_minima:
    st.error(f"⚠️ Atenção: Margem Abaixo do Mínimo — Ganho real ({fmt_brl(ganho_real_hora)}/h) menor que a hora mínima ({fmt_brl(valor_hora_minima)}/h).")
else:
    st.success(f"✅ Pacote Altamente Lucrativo — Ganho real de {fmt_brl(ganho_real_hora)}/h acima da hora mínima de {fmt_brl(valor_hora_minima)}/h.")

st.divider()

# ---------- Exportação de PDFs ----------

st.subheader("📄 Exportar Propostas")

dados_pdf = {
    "cliente": cliente_nome if cliente_nome.strip() else "Cliente",
    "qtd_estaticas": qtd_estaticas,
    "qtd_motions": qtd_motions,
    "prazo_dias": prazo_dias,
    "tempo_total": tempo_total,
    "valor_avulso": valor_avulso,
    "desconto_pct": desconto_pct,
    "valor_pacote": valor_pacote,
    "ganho_real_hora": ganho_real_hora,
    "salario": salario,
    "depreciacao": depreciacao,
    "custos_extras": custos_extras,
    "custo_mensal_total": custo_mensal_total,
    "margem_pct": margem_pct,
    "margem_valor": margem_valor,
    "impostos_pct": impostos_pct,
    "impostos_valor": impostos_valor,
    "impostos_valor_pacote": valor_pacote * (impostos_pct / 100),
    "faturamento_minimo": faturamento_minimo,
    "horas_focadas": horas_focadas,
    "valor_hora_minima": valor_hora_minima,
}

col_pdf1, col_pdf2 = st.columns(2)
with col_pdf1:
    st.download_button(
        "⬇️ Baixar PDF do Cliente (comercial)",
        data=gerar_pdf_cliente(dados_pdf),
        file_name=f"proposta_{dados_pdf['cliente'].replace(' ', '_').lower()}.pdf",
        mime="application/pdf",
        use_container_width=True,
        disabled=(total_artes == 0),
    )
with col_pdf2:
    st.download_button(
        "⬇️ Baixar PDF Interno (meus ganhos)",
        data=gerar_pdf_interno(dados_pdf),
        file_name=f"interno_{dados_pdf['cliente'].replace(' ', '_').lower()}.pdf",
        mime="application/pdf",
        use_container_width=True,
        disabled=(total_artes == 0),
    )
