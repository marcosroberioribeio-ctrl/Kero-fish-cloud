# -*- coding: utf-8 -*-
"""Kero Fish ERP Premium 12.1 - entrada da versão de teste."""
from kero_fish import ui

# Usa o novo logo oficial enviado para a branch profissional, sem alterar a
# versão estável/main. Mantemos o bootstrap original e trocamos somente a
# imagem retornada para a sidebar.
_original_bootstrap = ui._bootstrap


def _bootstrap_com_logo_oficial():
    bundled, _logo_antigo = _original_bootstrap()
    logo_oficial = ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
    return bundled, logo_oficial


ui._bootstrap = _bootstrap_com_logo_oficial

# Sidebar refinada: evita ampliar o logo até a largura total do contêiner,
# preservando melhor a nitidez, e remove o texto "PEIXE E CAMARÃO" duplicado.
def _sidebar_profissional(logo):
    with ui.st.sidebar:
        ui.st.markdown("## Kero Fish")
        if logo.exists():
            ui.st.image(str(logo), width=245)
        ui.st.markdown(
            f"<div class='kero-badge'>ERP Premium v{ui.__version__}</div>",
            unsafe_allow_html=True,
        )
        ui.st.markdown("---")
        pages = [
            "Painel Geral", "Produtos", "Fornecedores", "Compras", "Estoque", "Clientes",
            "Vendas", "Financeiro", "Despesas", "Contas a Pagar", "Contas a Receber",
            "Entregas", "Relatórios", "Importar Planilha", "Auditoria", "Diagnóstico", "Backup"
        ]
        return ui.st.radio("Navegação", pages, label_visibility="collapsed")


ui.sidebar = _sidebar_profissional

# Tema Premium Conforto: mantém a identidade azul/turquesa, com fundo mais
# claro e contraste mais confortável para uso prolongado.
ui.PREMIUM_CSS = """
<style>
:root { --kero-navy:#102b49; --kero-blue:#1b4d78; --kero-cyan:#24d7e7; --kero-gold:#d7a438; }
.stApp { background: radial-gradient(circle at 75% 0%, #285b82 0%, #183e62 38%, #102b49 100%); color:#f8fbff; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#245578 0%,#173b5d 100%); border-right:1px solid rgba(255,255,255,.14); }
[data-testid="stMetric"] { background:rgba(31,75,111,.88); border:1px solid rgba(79,220,232,.24); border-radius:16px; padding:14px 16px; box-shadow:0 10px 24px rgba(0,0,0,.14); }

/* Tabelas: superfície um pouco mais clara e cabeçalho visualmente destacado. */
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
    border:1px solid rgba(95,229,239,.42);
    border-radius:14px;
    overflow:hidden;
    background:rgba(43,86,120,.76);
    box-shadow:0 8px 20px rgba(0,0,0,.10);
}
[data-testid="stDataFrame"] > div, [data-testid="stDataEditor"] > div {
    background:rgba(43,86,120,.42);
}

div.stButton > button { border-radius:10px; font-weight:700; border:1px solid rgba(79,220,232,.42); }
div.stButton > button[kind="primary"] { background:linear-gradient(90deg,#19cde1,#48e4d8); color:#08233a; border:0; }
.kero-title { font-size:2rem; font-weight:800; letter-spacing:-.02em; margin-bottom:.1rem; color:#ffffff; }
.kero-sub { color:#c2dff2; margin-bottom:1rem; }
.kero-card { background:rgba(31,75,111,.82); border:1px solid rgba(255,255,255,.12); border-radius:16px; padding:16px; margin-bottom:14px; }
.kero-badge { display:inline-block; padding:6px 10px; border-radius:999px; background:rgba(36,215,231,.16); color:#baf8ff; border:1px solid rgba(79,220,232,.32); font-size:.82rem; font-weight:700; margin-top:8px; }
.kero-ok { color:#8dffc0; font-weight:700; }
.kero-warn { color:#ffe09a; font-weight:700; }
</style>
"""

ui.run()
