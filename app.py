# -*- coding: utf-8 -*-
"""Kero Fish ERP Premium 12.1 - entrada da versão de teste."""
import base64

from kero_fish import ui

# Mantém a V12.1 isolada da versão estável/main.
_original_bootstrap = ui._bootstrap


def _bootstrap_com_logo_oficial():
    bundled, _logo_antigo = _original_bootstrap()
    logo_oficial = ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
    return bundled, logo_oficial


ui._bootstrap = _bootstrap_com_logo_oficial


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

# Marca-d'água: usa o próprio arquivo oficial da branch, embutido localmente.
# Opacidade propositalmente baixa para não competir com números e tabelas.
_logo_path = ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
_watermark_css = ""
if _logo_path.exists():
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode("ascii")
    _watermark_css = f"""
    [data-testid="stAppViewContainer"]::before {{
        content:"";
        position:fixed;
        left:54%;
        top:54%;
        width:min(52vw,720px);
        aspect-ratio:1/1;
        transform:translate(-50%,-50%);
        background:url('data:image/jpeg;base64,{_logo_b64}') center/contain no-repeat;
        opacity:.045;
        filter:saturate(.82) contrast(.96);
        pointer-events:none;
        z-index:0;
    }}
    [data-testid="stMain"] {{ position:relative; z-index:1; }}
    """

# Identidade Premium: azul-marinho + dourado metálico, sem perder o conforto
# visual já aprovado. O dourado aparece como acabamento, não como excesso.
ui.PREMIUM_CSS = f"""
<style>
:root {{ --kero-navy:#0b2744; --kero-blue:#1b4d78; --kero-cyan:#27d7e5; --kero-gold:#d5a63a; --kero-gold-light:#f2d477; }}
.stApp {{ background:radial-gradient(circle at 75% 0%,#285b82 0%,#183e62 38%,#102b49 100%); color:#f8fbff; }}
[data-testid="stSidebar"] {{ background:linear-gradient(180deg,#245578 0%,#173b5d 100%); border-right:1px solid rgba(213,166,58,.58); box-shadow:8px 0 28px rgba(0,0,0,.10); }}
[data-testid="stMetric"] {{ background:linear-gradient(145deg,rgba(36,84,122,.92),rgba(27,70,106,.88)); border:1px solid rgba(242,212,119,.34); border-radius:16px; padding:14px 16px; box-shadow:0 10px 24px rgba(0,0,0,.14); }}
[data-testid="stMetric"]:hover {{ border-color:rgba(242,212,119,.62); }}
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {{ border:1px solid rgba(213,166,58,.42); border-radius:14px; overflow:hidden; background:rgba(32,72,106,.78); box-shadow:0 8px 20px rgba(0,0,0,.10); }}
[data-testid="stDataFrame"] > div, [data-testid="stDataEditor"] > div {{ background:rgba(43,86,120,.38); }}
div.stButton > button {{ border-radius:10px; font-weight:700; border:1px solid rgba(213,166,58,.55); }}
div.stButton > button[kind="primary"] {{ background:linear-gradient(90deg,#c89325,#f0cf6a); color:#102b49; border:0; box-shadow:0 5px 14px rgba(213,166,58,.18); }}
.kero-title {{ font-size:2rem; font-weight:800; letter-spacing:-.02em; margin-bottom:.1rem; color:#fff; text-shadow:0 1px 10px rgba(0,0,0,.12); }}
.kero-sub {{ color:#c8dfef; margin-bottom:1rem; }}
.kero-card {{ background:rgba(31,75,111,.82); border:1px solid rgba(213,166,58,.25); border-radius:16px; padding:16px; margin-bottom:14px; }}
.kero-badge {{ display:inline-block; padding:6px 11px; border-radius:999px; background:linear-gradient(90deg,rgba(185,132,27,.22),rgba(242,212,119,.14)); color:#ffe7a2; border:1px solid rgba(242,212,119,.52); font-size:.82rem; font-weight:800; margin-top:8px; box-shadow:inset 0 0 12px rgba(242,212,119,.06); }}
.kero-ok {{ color:#8dffc0; font-weight:700; }}
.kero-warn {{ color:#ffe09a; font-weight:700; }}
hr {{ border-color:rgba(213,166,58,.34) !important; }}
{_watermark_css}
</style>
"""

ui.run()
