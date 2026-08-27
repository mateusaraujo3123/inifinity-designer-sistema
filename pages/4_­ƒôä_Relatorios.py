import streamlit as st
from core.sheets import read_df
from core.reports import cliente_totais
from core.pdf_utils import gerar_relatorio_pdf, gerar_relatorio_txt

st.set_page_config(page_title="Relatórios - Infinity Designer", page_icon="📄", layout="wide")
st.title("📄 Relatórios Gerais")

clientes = read_df("Clientes")
if clientes.empty:
    st.info("Nenhum cliente cadastrado ainda.")
    st.stop()

st.subheader("Resumo de todos os clientes")
linhas = []
for _, c in clientes.iterrows():
    t = cliente_totais(c["id"])
    linhas.append({
        "Cliente": c["nome"], "Total vendido": t["total_vendido"],
        "Pago": t["total_pago"], "Desconto": t["total_desconto"],
        "Saldo devedor": t["saldo_devedor"], "Qtd. artes": t["qtd_artes"],
    })
st.dataframe(linhas, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Baixar relatório individual")
nomes = clientes.set_index("id")["nome"].to_dict()
cliente_id = st.selectbox("Cliente", options=list(nomes.keys()), format_func=lambda x: nomes[x])

col1, col2 = st.columns(2)
with col1:
    st.download_button("⬇️ Relatório em PDF", data=gerar_relatorio_pdf(cliente_id),
                        file_name=f"relatorio_{nomes[cliente_id]}.pdf", mime="application/pdf")
with col2:
    st.download_button("⬇️ Relatório em TXT", data=gerar_relatorio_txt(cliente_id),
                        file_name=f"relatorio_{nomes[cliente_id]}.txt", mime="text/plain")
