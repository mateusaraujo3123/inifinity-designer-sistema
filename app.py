import streamlit as st
import plotly.graph_objects as go

from core.reports import geral_totais, financas_periodo

st.set_page_config(page_title="Infinity Designer", page_icon="✨", layout="wide")

st.title("✨ Infinity Designer")
st.caption("Painel geral de clientes, projetos e finanças")

try:
    totais = geral_totais()
except Exception as e:
    st.error(
        "Não foi possível conectar à planilha do Google. Verifique o arquivo "
        "`.streamlit/secrets.toml` (veja `secrets.toml.example`)."
    )
    st.exception(e)
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total vendido", f"R$ {totais['total_vendido']:,.2f}")
col2.metric("Total pago", f"R$ {totais['total_pago']:,.2f}")
col3.metric("Descontos concedidos", f"R$ {totais['total_desconto']:,.2f}")
col4.metric("A receber", f"R$ {totais['a_receber']:,.2f}")

st.divider()

c1, c2 = st.columns([1, 1])
with c1:
    st.subheader("Distribuição geral")
    fig = go.Figure(data=[go.Pie(
        labels=["A receber", "Pago", "Descontos"],
        values=[totais["a_receber"], totais["total_pago"], totais["total_desconto"]],
        hole=0.45,
        marker=dict(colors=["#7C4DFF", "#00C896", "#FF6B6B"]),
    )])
    fig.update_layout(template="plotly_dark", margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Vendas x Pagamentos (mensal)")
    df = financas_periodo("M")
    fig2 = go.Figure()
    if not df.empty:
        fig2.add_trace(go.Bar(x=df["periodo"], y=df["vendas"], name="Vendas", marker_color="#7C4DFF"))
        fig2.add_trace(go.Bar(x=df["periodo"], y=df["pagamentos"], name="Pagamentos", marker_color="#00C896"))
    fig2.update_layout(template="plotly_dark", barmode="group", margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.info("Use o menu lateral para acessar Clientes, Categorias, Finanças e Relatórios.")
