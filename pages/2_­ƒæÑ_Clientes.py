import streamlit as st
import plotly.graph_objects as go

from core.sheets import read_df, append_row, update_row, delete_row, next_id, now_data_hora, clear_cache
from core.models import FORMAS_PAGAMENTO
from core.reports import cliente_totais, movimentacoes_cliente
from core.pdf_utils import gerar_cupom_pdf, gerar_relatorio_pdf, gerar_relatorio_txt

st.set_page_config(page_title="Clientes - Infinity Designer", page_icon="👥", layout="wide")
st.title("👥 Clientes")

clientes = read_df("Clientes")

# ---------- Cadastro de novo cliente ----------
with st.expander("➕ Cadastrar novo cliente"):
    with st.form("novo_cliente", clear_on_submit=True):
        nome = st.text_input("Nome do cliente")
        contato = st.text_input("Contato (telefone/e-mail)")
        obs = st.text_area("Observações")
        if st.form_submit_button("Cadastrar"):
            if nome.strip():
                data, _ = now_data_hora()
                append_row("Clientes", {
                    "id": next_id(clientes), "nome": nome.strip(),
                    "contato": contato, "observacoes": obs, "data_cadastro": data,
                })
                clear_cache()
                st.success("Cliente cadastrado!")
                st.rerun()

st.divider()

if clientes.empty:
    st.info("Nenhum cliente cadastrado ainda.")
    st.stop()

nomes = clientes.set_index("id")["nome"].to_dict()
cliente_id = st.selectbox(
    "Selecione um cliente",
    options=list(nomes.keys()),
    format_func=lambda x: nomes[x],
)

st.header(f"Perfil: {nomes[cliente_id]}")

totais = cliente_totais(cliente_id)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total vendido", f"R$ {totais['total_vendido']:,.2f}")
c2.metric("Pago", f"R$ {totais['total_pago']:,.2f}")
c3.metric("Descontos", f"R$ {totais['total_desconto']:,.2f}")
c4.metric("Saldo devedor", f"R$ {totais['saldo_devedor']:,.2f}")

fig = go.Figure(data=[go.Pie(
    labels=["Pago", "Descontos", "Saldo devedor"],
    values=[totais["total_pago"], totais["total_desconto"], max(totais["saldo_devedor"], 0)],
    hole=0.45,
    marker=dict(colors=["#00C896", "#FF6B6B", "#7C4DFF"]),
)])
fig.update_layout(template="plotly_dark", margin=dict(t=10, b=10), height=320)
st.plotly_chart(fig, use_container_width=True)

tabs = st.tabs(["📁 Projetos & Artes", "💵 Pagamentos", "🏷️ Descontos", "📜 Movimentações", "🧾 Cupom / Relatório"])

# ---------- Projetos & Artes ----------
with tabs[0]:
    projetos = read_df("Projetos")
    projetos_c = projetos[projetos["cliente_id"].astype(str) == str(cliente_id)]

    with st.form("novo_projeto", clear_on_submit=True):
        st.subheader("Novo projeto")
        nome_proj = st.text_input("Nome do projeto")
        desc_proj = st.text_area("Descrição / anotações")
        if st.form_submit_button("Criar projeto"):
            if nome_proj.strip():
                data, _ = now_data_hora()
                append_row("Projetos", {
                    "id": next_id(projetos), "cliente_id": cliente_id,
                    "nome_projeto": nome_proj.strip(), "descricao": desc_proj, "data_criacao": data,
                })
                clear_cache()
                st.rerun()

    if projetos_c.empty:
        st.info("Nenhum projeto cadastrado para este cliente.")
    else:
        categorias = read_df("Categorias")
        cat_dict = categorias.set_index("id")["nome"].to_dict() if not categorias.empty else {}

        for _, proj in projetos_c.iterrows():
            with st.expander(f"📁 {proj['nome_projeto']} — {proj['descricao'] or 'sem descrição'}"):
                artes = read_df("Artes")
                artes_p = artes[artes["projeto_id"].astype(str) == str(proj["id"])]

                st.markdown("**Adicionar arte / item ao pedido**")
                if categorias.empty:
                    st.warning("Cadastre categorias primeiro na página 'Categorias'.")
                else:
                    with st.form(f"nova_arte_{proj['id']}", clear_on_submit=True):
                        cat_id = st.selectbox(
                            "Categoria", options=list(cat_dict.keys()),
                            format_func=lambda x: cat_dict[x], key=f"cat_{proj['id']}",
                        )
                        desc_arte = st.text_input("Descrição da arte", key=f"desc_{proj['id']}")
                        valor_arte = st.number_input("Valor (R$)", min_value=0.0, step=10.0, key=f"val_{proj['id']}")
                        if st.form_submit_button("Adicionar arte"):
                            data, hora = now_data_hora()
                            append_row("Artes", {
                                "id": next_id(artes), "projeto_id": proj["id"], "cliente_id": cliente_id,
                                "categoria_id": cat_id, "descricao": desc_arte, "valor": valor_arte,
                                "data": data, "hora": hora,
                            })
                            clear_cache()
                            st.rerun()

                if not artes_p.empty:
                    st.markdown("**Itens deste projeto**")
                    for _, arte in artes_p.iterrows():
                        cA, cB, cC, cD = st.columns([3, 2, 2, 1])
                        cA.write(arte["descricao"])
                        cB.write(cat_dict.get(arte["categoria_id"], "-"))
                        novo_valor = cC.number_input(
                            "Valor", value=float(arte["valor"]), key=f"editval_{arte['id']}",
                            label_visibility="collapsed",
                        )
                        if novo_valor != arte["valor"]:
                            if cC.button("💾", key=f"savearte_{arte['id']}"):
                                update_row("Artes", arte["id"], {"valor": novo_valor})
                                clear_cache()
                                st.rerun()
                        if cD.button("🗑️", key=f"delarte_{arte['id']}"):
                            delete_row("Artes", arte["id"])
                            clear_cache()
                            st.rerun()

# ---------- Pagamentos ----------
with tabs[1]:
    st.subheader("Registrar pagamento")
    projetos_c = read_df("Projetos")
    projetos_c = projetos_c[projetos_c["cliente_id"].astype(str) == str(cliente_id)]
    proj_opts = {0: "(sem projeto específico)"} | projetos_c.set_index("id")["nome_projeto"].to_dict()

    with st.form("novo_pagamento", clear_on_submit=True):
        valor_pag = st.number_input("Valor pago (R$)", min_value=0.0, step=10.0)
        forma = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO)
        proj_ref = st.selectbox("Projeto relacionado", options=list(proj_opts.keys()), format_func=lambda x: proj_opts[x])
        obs_pag = st.text_input("Observações")
        if st.form_submit_button("Registrar pagamento"):
            pagamentos = read_df("Pagamentos")
            data, hora = now_data_hora()
            append_row("Pagamentos", {
                "id": next_id(pagamentos), "cliente_id": cliente_id,
                "projeto_id": proj_ref if proj_ref else "", "valor": valor_pag,
                "forma_pagamento": forma, "data": data, "hora": hora, "observacoes": obs_pag,
            })
            clear_cache()
            st.success("Pagamento registrado e abatido do saldo devedor!")
            st.rerun()

    pagamentos = read_df("Pagamentos")
    pagamentos_c = pagamentos[pagamentos["cliente_id"].astype(str) == str(cliente_id)]
    if not pagamentos_c.empty:
        st.dataframe(pagamentos_c[["data", "hora", "valor", "forma_pagamento", "observacoes"]], use_container_width=True, hide_index=True)

# ---------- Descontos ----------
with tabs[2]:
    st.subheader("Aplicar desconto")
    with st.form("novo_desconto", clear_on_submit=True):
        valor_desc = st.number_input("Valor do desconto (R$)", min_value=0.0, step=10.0)
        motivo = st.text_input("Motivo do desconto")
        if st.form_submit_button("Aplicar desconto"):
            descontos = read_df("Descontos")
            data, hora = now_data_hora()
            append_row("Descontos", {
                "id": next_id(descontos), "cliente_id": cliente_id, "projeto_id": "",
                "valor": valor_desc, "motivo": motivo, "data": data, "hora": hora,
            })
            clear_cache()
            st.success("Desconto aplicado!")
            st.rerun()

    descontos = read_df("Descontos")
    descontos_c = descontos[descontos["cliente_id"].astype(str) == str(cliente_id)]
    if not descontos_c.empty:
        st.dataframe(descontos_c[["data", "hora", "valor", "motivo"]], use_container_width=True, hide_index=True)

# ---------- Movimentações ----------
with tabs[3]:
    st.subheader("Histórico completo de movimentações")
    mov = movimentacoes_cliente(cliente_id)
    st.dataframe(mov, use_container_width=True, hide_index=True)

# ---------- Cupom / Relatório ----------
with tabs[4]:
    st.subheader("Gerar cupom para o cliente")
    tipo_cupom = st.radio("Tipo de cupom", ["Simples", "Completo"], horizontal=True)
    pdf_bytes = gerar_cupom_pdf(cliente_id, tipo="completo" if tipo_cupom == "Completo" else "simples")
    st.download_button(
        "⬇️ Baixar cupom em PDF", data=pdf_bytes,
        file_name=f"cupom_{tipo_cupom.lower()}_{nomes[cliente_id]}.pdf", mime="application/pdf",
    )

    st.divider()
    st.subheader("Relatório de movimentações deste cliente")
    formato = st.radio("Formato do relatório", ["PDF", "TXT"], horizontal=True)
    if formato == "PDF":
        rel_pdf = gerar_relatorio_pdf(cliente_id)
        st.download_button("⬇️ Baixar relatório em PDF", data=rel_pdf,
                            file_name=f"relatorio_{nomes[cliente_id]}.pdf", mime="application/pdf")
    else:
        rel_txt = gerar_relatorio_txt(cliente_id)
        st.download_button("⬇️ Baixar relatório em TXT", data=rel_txt,
                            file_name=f"relatorio_{nomes[cliente_id]}.txt", mime="text/plain")
