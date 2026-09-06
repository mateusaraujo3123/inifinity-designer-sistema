import streamlit.components.v1 as components

def injetar_icone_home_screen():
    """Injeta os ícones que o iOS/Android usam ao 'Adicionar à Tela de Início'.
    Usa arquivos hospedados na própria aplicação (pasta /static), evitando
    problemas de origem cruzada. Chame isso no topo de CADA página, já que
    a navegação entre páginas do Streamlit recarrega o <head>."""
    components.html("""
    <script>
    (function() {
        function injetar(doc) {
            if (!doc || doc.querySelector('link[rel="apple-touch-icon"]')) return;
            var head = doc.getElementsByTagName('head')[0];
            if (!head) return;

            var appleIcon = doc.createElement('link');
            appleIcon.rel = 'apple-touch-icon';
            appleIcon.href = './app/static/icon-180.png';
            head.appendChild(appleIcon);

            var androidIcon = doc.createElement('link');
            androidIcon.rel = 'icon';
            androidIcon.sizes = '192x192';
            androidIcon.href = './app/static/icon-192.png';
            head.appendChild(androidIcon);
        }
        try { injetar(window.parent.document); } catch (e) {}
        try { injetar(window.top.document); } catch (e) {}
    })();
    </script>
    """, height=0)

