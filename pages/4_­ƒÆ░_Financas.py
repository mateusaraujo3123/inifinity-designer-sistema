import streamlit as st
import plotly.graph_objects as go

from core.reports import financas_periodo, geral_totais

st.set_page_config(page_title="Finanças - Infinity Designer", page_icon="💰", layout="wide")
st.title("💰 Painel de Finanças")

totais = geral_totais()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total vendido", f"R$ {totais['total_vendido']:,.2f}")
c2.metric("Total pago", f"R$ {totais['total_pago']:,.2f}")
c3.metric("Descontos", f"R$ {totais['total_desconto']:,.2f}")
c4.metric("A receber", f"R$ {totais['a_receber']:,.2f}")

st.divider()

periodo_map = {"Diário": "D", "Semanal": "W", "Mensal": "M", "Anual": "Y"}
escolha = st.radio("Ver relatório:", list(periodo_map.keys()), horizontal=True)

df = financas_periodo(periodo_map[escolha])

if df.empty:
    st.info("Ainda não há movimentações suficientes para gerar este relatório.")
else:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["periodo"], y=df["vendas"], name="Vendas", marker_color="#7C4DFF"))
    fig.add_trace(go.Bar(x=df["periodo"], y=df["pagamentos"], name="Pagamentos", marker_color="#00C896"))
    fig.update_layout(template="plotly_dark", barmode="group", title=f"Vendas x Pagamentos ({escolha})")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
