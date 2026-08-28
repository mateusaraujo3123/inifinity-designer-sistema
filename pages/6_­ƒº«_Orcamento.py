import streamlit as st
from core.sheets import read_df, get_config, save_config, append_row, next_id, now_data_hora, clear_cache
from core.orcamento import calcular_valor_hora, calcular_pacote
from core.pdf_utils import gerar_orcamento_pdf_cliente, gerar_orcamento_pdf_interno

st.set_page_config(page_title="Orçamento - Infinity Designer", page_icon="🧮", layout="wide")
st.title("🧮 Orçamento")

cfg = get_config()
calc = calcular_valor_hora(cfg)

tab1, tab2, tab3 = st.tabs(["⚙️ Valores base", "📝 Orçamento avulso", "📦 Pacote mensal"])

# ---------- Valores base ----------
with tab1:
    with st.form("form_config"):
        c1, c2 = st.columns(2)
        salario = c1.number_input("Salário desejado (R$/mês)", min_value=0.0, value=cfg["salario_desejado"], step=50.0)
        computador = c2.number_input("Valor do computador (R$)", min_value=0.0, value=cfg["valor_computador"], step=50.0)
        custos = c1.number_input("Custos extras (luz/internet/softwares) (R$/mês)", min_value=0.0, value=cfg["custos_extras"], step=10.0)
        horas = c2.number_input("Horas de trabalho focadas por mês", min_value=1.0, value=cfg["horas_trabalho_mes"], step=5.0)
        if st.form_submit_button("Salvar valores base"):
            save_config({
                "salario_desejado": salario, "valor_computador": computador,
                "custos_extras": custos, "horas_trabalho_mes": horas,
            })
            st.success("Valores base atualizados!")
            st.rerun()

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Depreciação do computador", f"R$ {calc['depreciacao_mensal']:,.2f}/mês")
    c2.metric("Custo mensal total", f"R$ {calc['custo_mensal_total']:,.2f}")
    c3.metric("Valor da sua hora", f"R$ {calc['valor_hora']:,.2f}")

# ---------- Orçamento avulso ----------
with tab2:
    st.subheader("Montar orçamento para um projeto")

    if "itens_orcamento" not in st.session_state:
        st.session_state.itens_orcamento = []

    clientes = read_df("Clientes")
    nomes_clientes = {0: "(orçamento avulso, sem cliente vinculado)"} | (
        clientes.set_index("id")["nome"].to_dict() if not clientes.empty else {}
    )

    nome_orc = st.text_input("Nome do orçamento", value="Orçamento de Projeto")
    cliente_sel = st.selectbox("Cliente", options=list(nomes_clientes.keys()), format_func=lambda x: nomes_clientes[x])

    with st.form("add_item_orcamento", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        desc_item = c1.text_input("Descrição do item")
        horas_item = c2.number_input("Horas", min_value=0.0, step=0.5, value=1.0)
        qtd_item = c3.number_input("Quantidade", min_value=1, step=1, value=1)
        valor_sugerido = round(horas_item * qtd_item * calc["valor_hora"], 2)
        valor_item = c4.number_input("Valor final (R$)", min_value=0.0, step=10.0, value=valor_sugerido)
        if st.form_submit_button("➕ Adicionar item"):
            if desc_item.strip():
                st.session_state.itens_orcamento.append({
                    "descricao": desc_item.strip(), "horas": horas_item,
                    "quantidade": qtd_item, "valor_total": valor_item,
                })

    if st.session_state.itens_orcamento:
        st.markdown("**Itens do orçamento**")
        for i, item in enumerate(st.session_state.itens_orcamento):
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.write(item["descricao"])
            c2.write(f"{item['horas']} h × {item['quantidade']}")
            c3.write(f"R$ {item['valor_total']:,.2f}")
            if c4.button("🗑️", key=f"delitem_{i}"):
                st.session_state.itens_orcamento.pop(i)
                st.rerun()

        tempo_total = sum(i["horas"] * i["quantidade"] for i in st.session_state.itens_orcamento)
        valor_bruto = sum(i["valor_total"] for i in st.session_state.itens_orcamento)

        desconto_pct = st.slider("Desconto a aplicar (%)", 0, 50, 0) / 100
        valor_final = round(valor_bruto * (1 - desconto_pct), 2)
        obs = st.text_area("Observações (aparecem no PDF do cliente)")

        st.metric("Valor final do orçamento", f"R$ {valor_final:,.2f}")

        orc = {
            "nome_orcamento": nome_orc,
            "cliente_nome": nomes_clientes[cliente_sel] if cliente_sel else "",
            "itens": st.session_state.itens_orcamento,
            "desconto_pct": desconto_pct,
            "tempo_total_horas": round(tempo_total, 2),
            "valor_hora_usado": calc["valor_hora"],
            "valor_bruto": round(valor_bruto, 2),
            "valor_final": valor_final,
            "observacoes": obs,
        }

        colA, colB, colC = st.columns(3)
        colA.download_button(
            "⬇️ PDF para o cliente", data=gerar_orcamento_pdf_cliente(orc),
            file_name=f"orcamento_{nome_orc}.pdf", mime="application/pdf",
        )
        colB.download_button(
            "⬇️ PDF interno (detalhado)", data=gerar_orcamento_pdf_interno(orc),
            file_name=f"orcamento_{nome_orc}_interno.pdf", mime="application/pdf",
        )
        if colC.button("💾 Salvar no histórico"):
            import json
            data, hora = now_data_hora()
            orcamentos = read_df("Orcamentos")
            append_row("Orcamentos", {
                "id": next_id(orcamentos), "tipo": "avulso", "nome_orcamento": nome_orc,
                "cliente_id": cliente_sel or "", "itens_json": json.dumps(st.session_state.itens_orcamento, ensure_ascii=False),
                "desconto_pct": desconto_pct, "tempo_total_horas": round(tempo_total, 2),
                "valor_hora_usado": calc["valor_hora"], "valor_bruto": round(valor_bruto, 2),
                "valor_final": valor_final, "data": data, "hora": hora, "observacoes": obs,
            })
            clear_cache("Orcamentos")
            st.success("Orçamento salvo no histórico!")

        if st.button("🧹 Limpar itens"):
            st.session_state.itens_orcamento = []
            st.rerun()
    else:
        st.info("Adicione itens ao orçamento acima.")

# ---------- Pacote mensal ----------
with tab3:
    st.subheader("Gerador de pacotes mensais")
    c1, c2 = st.columns(2)
    qtd_estaticas = c1.number_input("Quantidade de artes estáticas", min_value=0, step=1, value=6)
    qtd_motions = c2.number_input("Quantidade de motions", min_value=0, step=1, value=2)

    pacote = calcular_pacote(qtd_estaticas, qtd_motions, calc["valor_hora"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Valor se comprado avulso", f"R$ {pacote['valor_avulso']:,.2f}")
    c2.metric(f"Desconto aplicado ({pacote['desconto_pct']*100:.0f}%)", f"- R$ {pacote['valor_avulso'] - pacote['valor_pacote']:,.2f}")
    c3.metric("Valor do pacote mensal", f"R$ {pacote['valor_pacote']:,.2f}")

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Tempo total estimado", f"{pacote['tempo_total']} h")
    ganho = pacote["ganho_hora_pacote"]
    delta = ganho - calc["valor_hora"]
    c2.metric("Ganho real por hora no pacote", f"R$ {ganho:,.2f}", delta=f"R$ {delta:,.2f} vs. mínimo")

    if ganho < calc["valor_hora"]:
        st.warning(f"⚠️ Nesse pacote, sua hora efetiva (R$ {ganho:,.2f}) ficou **abaixo** do mínimo de R$ {calc['valor_hora']:,.2f}/h.")
    else:
        st.success(f"✅ Sua hora efetiva neste pacote (R$ {ganho:,.2f}) está acima do mínimo de R$ {calc['valor_hora']:,.2f}/h.")

    nome_pacote = st.text_input("Nome do pacote", value=f"Pacote Mensal — {qtd_estaticas} estáticas + {qtd_motions} motions")
    clientes2 = read_df("Clientes")
    nomes2 = {0: "(sem cliente vinculado)"} | (clientes2.set_index("id")["nome"].to_dict() if not clientes2.empty else {})
    cliente_sel2 = st.selectbox("Cliente", options=list(nomes2.keys()), format_func=lambda x: nomes2[x], key="cliente_pacote")

    orc_pacote = {
        "nome_orcamento": nome_pacote,
        "cliente_nome": nomes2[cliente_sel2] if cliente_sel2 else "",
        "itens": [
            {"descricao": "Artes estáticas", "quantidade": qtd_estaticas, "horas": 1.0, "valor_total": round(qtd_estaticas * 1.0 * calc["valor_hora"], 2)},
            {"descricao": "Motions", "quantidade": qtd_motions, "horas": 1.5, "valor_total": round(qtd_motions * 1.5 * calc["valor_hora"], 2)},
        ],
        "desconto_pct": pacote["desconto_pct"],
        "tempo_total_horas": pacote["tempo_total"],
        "valor_hora_usado": calc["valor_hora"],
        "valor_bruto": pacote["valor_avulso"],
        "valor_final": pacote["valor_pacote"],
        "observacoes": "Pacote mensal com desconto de escala.",
    }

    colA, colB = st.columns(2)
    colA.download_button(
        "⬇️ PDF para o cliente", data=gerar_orcamento_pdf_cliente(orc_pacote),
        file_name=f"{nome_pacote}.pdf", mime="application/pdf",
    )
    colB.download_button(
        "⬇️ PDF interno (detalhado)", data=gerar_orcamento_pdf_interno(orc_pacote),
        file_name=f"{nome_pacote}_interno.pdf", mime="application/pdf",
    )
