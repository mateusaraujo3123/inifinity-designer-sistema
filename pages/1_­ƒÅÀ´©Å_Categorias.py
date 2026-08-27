import streamlit as st
from core.sheets import read_df, append_row, update_row, delete_row, next_id, clear_cache

st.set_page_config(page_title="Categorias - Infinity Designer", page_icon="🏷️", layout="wide")
st.title("🏷️ Categorias de Arte")
st.caption("Cadastre quantas categorias quiser (ex: Motion, Identidade Visual, Logos...)")

categorias = read_df("Categorias")

with st.form("nova_categoria", clear_on_submit=True):
    nome = st.text_input("Nova categoria")
    submitted = st.form_submit_button("Adicionar categoria")
    if submitted and nome.strip():
        append_row("Categorias", {"id": next_id(categorias), "nome": nome.strip()})
        clear_cache()
        st.success(f"Categoria '{nome}' adicionada!")
        st.rerun()

st.divider()
st.subheader("Categorias cadastradas")

if categorias.empty:
    st.info("Nenhuma categoria cadastrada ainda.")
else:
    for _, row in categorias.iterrows():
        c1, c2, c3 = st.columns([4, 2, 1])
        c1.write(f"**{row['nome']}**")
        novo_nome = c2.text_input("Renomear", value=row["nome"], key=f"ren_{row['id']}", label_visibility="collapsed")
        if novo_nome != row["nome"]:
            if c2.button("Salvar", key=f"save_{row['id']}"):
                update_row("Categorias", row["id"], {"nome": novo_nome})
                clear_cache()
                st.rerun()
        if c3.button("🗑️ Excluir", key=f"del_{row['id']}"):
            delete_row("Categorias", row["id"])
            clear_cache()
            st.rerun()
