import streamlit as st

# Ícones hospedados via jsDelivr (CDN do GitHub) — mais confiável que o
# static serving do Streamlit Cloud, que nem sempre funciona corretamente.
URL_ICONE_180 = "https://cdn.jsdelivr.net/gh/mateusaraujo3123/inifinity-designer-sistema@main/static/icon-180.png"
URL_ICONE_192 = "https://cdn.jsdelivr.net/gh/mateusaraujo3123/inifinity-designer-sistema@main/static/icon-192.png"


def injetar_icone_home_screen():
    """Injeta os ícones que o iOS/Android usam ao 'Adicionar à Tela de Início'.
    Usa st.markdown (renderiza direto no documento principal, sem iframe
    isolado) em vez de components.html, que o Safari costuma bloquear.
    Chame isso no topo de CADA página, já que a navegação entre páginas do
    Streamlit recarrega o <head>."""
    st.markdown(
        f'<link rel="apple-touch-icon" href="{URL_ICONE_180}">'
        f'<link rel="apple-touch-icon" sizes="180x180" href="{URL_ICONE_180}">'
        f'<link rel="icon" type="image/png" sizes="192x192" href="{URL_ICONE_192}">',
        unsafe_allow_html=True,
    )


