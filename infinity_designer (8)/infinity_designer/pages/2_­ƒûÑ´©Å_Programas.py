import streamlit as st
from core.icone_pwa import injetar_icone_home_screen
from core.sheets import read_df, append_row, update_row, delete_row, next_id, clear_cache
from core.models import PROGRAMAS_PADRAO

st.set_page_config(page_title="Programas - Infinity Designer", page_icon="🖥️", layout="wide")
injetar_icone_home_screen()
st.title("🖥️ Programas Utilizados")
st.caption("Lista de programas que aparecem na ficha de pedido de cada arte (Corel, Photoshop, After Effects...)")

programas = read_df("Programas")

if programas.empty:
    st.info("Nenhum programa cadastrado ainda.")
    if st.button("➕ Carregar lista padrão (CorelDRAW, Photoshop, After Effects...)"):
        proximo_id = next_id(programas)
        for i, nome in enumerate(PROGRAMAS_PADRAO):
            append_row("Programas", {"id": proximo_id + i, "nome": nome})
        clear_cache("Programas")
        st.rerun()

with st.form("novo_programa", clear_on_submit=True):
    nome = st.text_input("Novo programa")
    if st.form_submit_button("Adicionar") and nome.strip():
        append_row("Programas", {"id": next_id(programas), "nome": nome.strip()})
        clear_cache("Programas")
        st.rerun()

st.divider()
st.subheader("Programas cadastrados")

if not programas.empty:
    for _, row in programas.iterrows():
        c1, c2 = st.columns([5, 1])
        c1.write(f"**{row['nome']}**")
        if c2.button("🗑️ Excluir", key=f"del_prog_{row['id']}"):
            delete_row("Programas", row["id"])
            clear_cache("Programas")
            st.rerun()
