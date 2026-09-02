# -*- coding: utf-8 -*-
"""Kero Fish ERP Premium 12.1 - dashboard executivo de teste."""
import base64
from datetime import date
import pandas as pd
from kero_fish import ui

# Mantém toda a V12.1 isolada da versão estável/main.
_original_bootstrap = ui._bootstrap

def _bootstrap_com_logo_oficial():
    bundled, _ = _original_bootstrap()
    return bundled, ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
ui._bootstrap = _bootstrap_com_logo_oficial


def _sidebar_profissional(logo):
    with ui.st.sidebar:
        if logo.exists():
            ui.st.image(str(logo), width=220)
        ui.st.markdown(f"<div class='brand-version'><b>PREMIUM</b><span>v{ui.__version__}</span></div>", unsafe_allow_html=True)
        pages = ["Painel Geral","Produtos","Fornecedores","Compras","Estoque","Clientes","Vendas","Financeiro","Despesas","Contas a Pagar","Contas a Receber","Entregas","Relatórios","Importar Planilha","Auditoria","Diagnóstico","Backup"]
        page = ui.st.radio("Navegação", pages, label_visibility="collapsed")
        ui.st.markdown("<div class='user-card'>👤 &nbsp; <b>Marcos Robério</b><br><small>Administrador</small></div>", unsafe_allow_html=True)
        return page
ui.sidebar = _sidebar_profissional

_logo_path = ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
wm = ""
if _logo_path.exists():
    b64 = base64.b64encode(_logo_path.read_bytes()).decode("ascii")
    wm = f'''[data-testid="stAppViewContainer"]::before{{content:"";position:fixed;left:61%;top:55%;width:min(43vw,620px);aspect-ratio:1;transform:translate(-50%,-50%);background:url("data:image/jpeg;base64,{b64}") center/contain no-repeat;opacity:.028;filter:grayscale(.15);pointer-events:none;z-index:0}}'''

ui.PREMIUM_CSS = f"""
<style>
:root{{--navy:#041a34;--navy2:#073462;--blue:#0879d9;--gold:#e4ae2d;--gold2:#ffd56a}}
.stApp{{background:radial-gradient(circle at 62% 18%,#07539a 0%,#06396d 27%,#05264b 62%,#03182f 100%);color:#fff}}
[data-testid="stSidebar"]{{background:linear-gradient(180deg,#063c70 0%,#031b36 82%);border-right:2px solid var(--gold);box-shadow:8px 0 28px #0005}}
[data-testid="stSidebar"] img{{border-radius:50%;border:3px solid var(--gold);box-shadow:0 0 0 5px #fff,0 0 0 7px var(--gold),0 10px 30px #0006}}
[data-testid="stSidebar"] [role="radiogroup"] label{{padding:7px 10px;border-radius:10px;margin:1px 0}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){{background:linear-gradient(90deg,#ffd86b,#d99c17);color:#092442;font-weight:800;box-shadow:0 5px 14px #0004}}
.brand-version{{display:flex;justify-content:center;gap:8px;align-items:center;margin:16px 0 18px}}.brand-version b{{background:linear-gradient(90deg,#f7c343,#ffd972);color:#17233b;padding:5px 12px;border-radius:18px}}.brand-version span{{background:#0879d9;padding:5px 11px;border-radius:18px}}
.user-card{{margin-top:18px;padding:14px;border:1px solid #d9a72f88;border-radius:14px;background:#092d52cc;font-size:15px}}
[data-testid="stHeader"]{{background:#041d39aa;border-bottom:1px solid #d9a72f55}}
.block-container{{padding-top:1.35rem;max-width:1500px}}
.kero-top{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid var(--gold);padding:0 4px 12px;margin-bottom:18px}}.kero-top h2{{margin:0;font-size:30px}}.kero-top .premium{{background:linear-gradient(90deg,#f2b82f,#ffd96a);color:#17233b;padding:6px 14px;border-radius:18px;font-weight:900;margin-left:10px}}.kero-date{{color:#dcecff;font-weight:600}}
.exec-title{{font-size:31px;font-weight:900;margin:4px 0 0}}.exec-sub{{color:#d6e8f7;margin-bottom:17px}}
.metric-card{{height:126px;border-radius:14px;padding:17px 18px;border:1px solid #ffffff44;box-shadow:0 10px 25px #0004;position:relative;overflow:hidden}}.metric-card:after{{content:"";position:absolute;width:90px;height:90px;border-radius:50%;right:-28px;top:-30px;background:#fff1}}.metric-label{{font-size:14px;opacity:.94}}.metric-value{{font-size:27px;font-weight:900;margin-top:9px;white-space:nowrap}}.metric-note{{font-size:12px;margin-top:5px;opacity:.85}}.green{{background:linear-gradient(135deg,#009c82,#006f6a)}}.red{{background:linear-gradient(135deg,#e33e52,#a51f39)}}.blue{{background:linear-gradient(135deg,#0d82e9,#0752a5)}}.gold{{background:linear-gradient(135deg,#e6a719,#9c6905)}}.purple{{background:linear-gradient(135deg,#7a3ce0,#4324a4)}}.teal{{background:linear-gradient(135deg,#00a998,#006e79)}}
.panel-card{{background:#f7fbffed;color:#08254a;border-radius:14px;padding:15px 16px;box-shadow:0 10px 28px #0004;border:1px solid #fff;margin-top:14px;min-height:250px}}.panel-card h3{{margin:0 0 10px;font-size:19px;color:#08254a}}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{{border:1px solid #d9a72f88;border-radius:12px;overflow:hidden}}
[data-testid="stMetric"]{{background:#0b4173cc;border:1px solid #e5b63a88;border-radius:14px}}
div.stButton>button{{border-radius:10px;font-weight:800;border:1px solid #e5b63a}}div.stButton>button[kind="primary"]{{background:linear-gradient(90deg,#e0a522,#ffd96a);color:#092442}}
.kero-title{{font-size:2rem;font-weight:900}}.kero-sub{{color:#cfe4f5}}.kero-badge{{display:inline-block;padding:6px 10px;border-radius:999px;background:#d7a43833;color:#ffe39a;border:1px solid #d7a43899;font-weight:800}}
{wm}
</style>
"""


def _card(col, css, icon, label, value, note="Este mês"):
    col.markdown(f"<div class='metric-card {css}'><div class='metric-label'>{icon} &nbsp; {label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)


def _safe_df(sql):
    try:
        with ui.connect() as conn:
            return pd.read_sql_query(sql, conn)
    except Exception:
        return pd.DataFrame()


def painel_executivo():
    m = ui.dashboard_metrics()
    hoje_br = date.today().strftime("%d/%m/%Y")
    ui.st.markdown(f"<div class='kero-top'><div><h2>Kero Fish ERP <span class='premium'>PREMIUM</span></h2></div><div class='kero-date'>📅 {hoje_br}</div></div>", unsafe_allow_html=True)
    ui.st.markdown("<div class='exec-title'>📊 Painel Geral</div><div class='exec-sub'>Visão executiva de vendas, caixa, compromissos e estoque.</div>", unsafe_allow_html=True)

    cols = ui.st.columns(6)
    _card(cols[0],"green","📈","Entradas realizadas",ui.moeda(m["entradas"]))
    _card(cols[1],"red","📉","Saídas realizadas",ui.moeda(m["saidas"]))
    _card(cols[2],"blue","💼","Saldo realizado",ui.moeda(m["saldo"]))
    _card(cols[3],"gold","👤","Contas a receber",ui.moeda(m["receber"]),"Pendências")
    _card(cols[4],"purple","📄","Contas a pagar",ui.moeda(m["pagar"]),"Pendências")
    _card(cols[5],"teal","🛒","Vendas registradas",str(m["qtd_vendas"]))

    vendas30 = _safe_df("SELECT substr(data,6,5) AS Dia, SUM(COALESCE(total,0)) AS Vendas FROM vendas WHERE date(data)>=date('now','-30 day') GROUP BY data ORDER BY data")
    top = _safe_df("SELECT produto AS Produto, SUM(COALESCE(total,0)) AS Faturamento FROM vendas GROUP BY produto ORDER BY Faturamento DESC LIMIT 5")
    cats = _safe_df("SELECT COALESCE(p.categoria,'Outros') AS Categoria, SUM(COALESCE(v.total,0)) AS Total FROM vendas v LEFT JOIN produtos p ON lower(trim(p.nome))=lower(trim(v.produto)) GROUP BY COALESCE(p.categoria,'Outros') ORDER BY Total DESC")

    a,b,c = ui.st.columns([1.25,1,1])
    with a:
        ui.st.markdown("<div class='panel-card'><h3>Entradas × Vendas — últimos 30 dias</h3>", unsafe_allow_html=True)
        if not vendas30.empty:
            ui.st.bar_chart(vendas30.set_index("Dia"), height=210)
        else: ui.st.info("Sem movimentação no período.")
        ui.st.markdown("</div>", unsafe_allow_html=True)
    with b:
        ui.st.markdown("<div class='panel-card'><h3>Vendas por Categoria</h3>", unsafe_allow_html=True)
        if not cats.empty:
            cats["Participação"] = cats["Total"] / cats["Total"].sum() * 100
            ui.st.dataframe(cats[["Categoria","Participação"]], hide_index=True, use_container_width=True, height=210)
        else: ui.st.info("Sem categorias para exibir.")
        ui.st.markdown("</div>", unsafe_allow_html=True)
    with c:
        ui.st.markdown("<div class='panel-card'><h3>Top 5 Produtos</h3>", unsafe_allow_html=True)
        if not top.empty:
            ui.st.bar_chart(top.set_index("Produto"), horizontal=True, height=210)
        else: ui.st.info("Sem vendas para exibir.")
        ui.st.markdown("</div>", unsafe_allow_html=True)

    estoque = ui.stock_df()
    left,right = ui.st.columns([1.15,1])
    with left:
        ui.st.markdown("### 📦 Estoque e Alertas")
        if not estoque.empty:
            cols_show=[x for x in ["Produto","Categoria","Estoque","Minimo","Situacao"] if x in estoque.columns]
            ui.st.dataframe(estoque[cols_show].head(8), hide_index=True, use_container_width=True, height=300)
    with right:
        ui.st.markdown("### 🧾 Últimas Movimentações")
        mov = _safe_df("SELECT data AS Data, descricao AS Descricao, tipo AS Tipo, valor AS Valor FROM financeiro ORDER BY data DESC,id DESC LIMIT 8")
        if not mov.empty:
            mov["Valor"] = mov["Valor"].apply(ui.moeda)
            ui.st.dataframe(mov, hide_index=True, use_container_width=True, height=300)
        else: ui.st.info("Nenhuma movimentação encontrada.")

ui.painel = painel_executivo
ui.run()
