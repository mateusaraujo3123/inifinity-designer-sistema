import streamlit.components.v1 as components

def injetar_icone_home_screen(url_icone_192: str, url_icone_180: str):
    """Injeta os ícones que o iOS/Android usam ao 'Adicionar à Tela de Início'.
    As URLs precisam ser públicas (ex: link direto de uma imagem no GitHub)."""
    components.html(f"""
    <script>
    var head = window.parent.document.getElementsByTagName('head')[0];

    var appleIcon = document.createElement('link');
    appleIcon.rel = 'apple-touch-icon';
    appleIcon.href = '{url_icone_180}';
    head.appendChild(appleIcon);

    var androidIcon = document.createElement('link');
    androidIcon.rel = 'icon';
    androidIcon.sizes = '192x192';
    androidIcon.href = '{url_icone_192}';
    head.appendChild(androidIcon);
    </script>
    """, height=0)
