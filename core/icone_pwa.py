import streamlit.components.v1 as components

# Ícones hospedados via jsDelivr (CDN do GitHub) — mais confiável que o
# static serving do Streamlit Cloud, que nem sempre funciona corretamente.
URL_ICONE_180 = "https://cdn.jsdelivr.net/gh/mateusaraujo3123/inifinity-designer-sistema@main/static/icon-180.png"
URL_ICONE_192 = "https://cdn.jsdelivr.net/gh/mateusaraujo3123/inifinity-designer-sistema@main/static/icon-192.png"


def injetar_icone_home_screen():
    """Injeta os ícones que o iOS/Android usam ao 'Adicionar à Tela de Início'.
    Chame isso no topo de CADA página, já que a navegação entre páginas do
    Streamlit recarrega o <head>."""
    components.html(f"""
    <script>
    (function() {{
        function injetar(doc) {{
            if (!doc || doc.querySelector('link[rel="apple-touch-icon"]')) return;
            var head = doc.getElementsByTagName('head')[0];
            if (!head) return;

            var appleIcon = doc.createElement('link');
            appleIcon.rel = 'apple-touch-icon';
            appleIcon.href = '{URL_ICONE_180}';
            head.appendChild(appleIcon);

            var androidIcon = doc.createElement('link');
            androidIcon.rel = 'icon';
            androidIcon.sizes = '192x192';
            androidIcon.href = '{URL_ICONE_192}';
            head.appendChild(androidIcon);
        }}
        try {{ injetar(window.parent.document); }} catch (e) {{}}
        try {{ injetar(window.top.document); }} catch (e) {{}}
    }})();
    </script>
    """, height=0)


