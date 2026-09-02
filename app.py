# -*- coding: utf-8 -*-
"""Kero Fish ERP Premium 12.1 - painel executivo profissional de teste."""
import base64
from datetime import date
import altair as alt
import pandas as pd
from kero_fish import ui

# Mantém a V12.1 isolada da versão estável/main.
_original_bootstrap = ui._bootstrap

def _bootstrap_com_logo_oficial():
    bundled, _ = _original_bootstrap()
    return bundled, ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"

ui._bootstrap = _bootstrap_com_logo_oficial


def _sidebar_profissional(logo):
    pages = [
        "▦  Painel Geral", "◫  Produtos", "♟  Fornecedores", "🛒  Compras", "◈  Estoque",
        "♙  Clientes", "🛍  Vendas", "◉  Financeiro", "▤  Despesas", "▣  Contas a Pagar",
        "▧  Contas a Receber", "▰  Entregas", "▥  Relatórios", "⇩  Importar Planilha",
        "⌕  Auditoria", "◉  Diagnóstico", "☁  Backup"
    ]
    mapping = {p: p.split("  ", 1)[1] for p in pages}
    with ui.st.sidebar:
        if logo.exists():
            ui.st.image(str(logo), width=205)
        ui.st.markdown(f"<div class='brand-version'><b>PREMIUM</b><span>v{ui.__version__}</span></div>", unsafe_allow_html=True)
        selected = ui.st.radio("Navegação", pages, label_visibility="collapsed")
        ui.st.markdown("<div class='user-card'>👤 &nbsp; <b>Marcos Robério</b><br><small>Administrador</small></div>", unsafe_allow_html=True)
        return mapping[selected]

ui.sidebar = _sidebar_profissional

_logo_path = ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
wm = ""
if _logo_path.exists():
    b64 = base64.b64encode(_logo_path.read_bytes()).decode("ascii")
    wm = f'''[data-testid="stAppViewContainer"]::before{{content:"";position:fixed;left:58%;top:53%;width:min(38vw,560px);aspect-ratio:1;transform:translate(-50%,-50%);background:url("data:image/jpeg;base64,{b64}") center/contain no-repeat;opacity:.018;pointer-events:none;z-index:0}}'''

ui.PREMIUM_CSS = f"""
<style>
:root{{--navy:#031426;--navy2:#061e38;--navy3:#082a4d;--gold:#f1b92f;--line:#174b76}}
html,body,[class*="css"]{{font-family:Inter,Segoe UI,Arial,sans-serif}}
.stApp{{background:linear-gradient(135deg,#061d35 0%,#031426 55%,#041a30 100%);color:#fff}}
[data-testid="stHeader"]{{background:#031426e8;border-bottom:1px solid #174b76}}
.block-container{{padding-top:1.05rem;max-width:1550px;padding-left:1.15rem;padding-right:1.15rem}}
[data-testid="stSidebar"]{{background:linear-gradient(180deg,#04182c 0%,#021120 100%);border-right:1px solid #1c4468;box-shadow:8px 0 30px #0006}}
[data-testid="stSidebar"] img{{border-radius:50%;border:3px solid var(--gold);box-shadow:0 0 0 4px #fff,0 0 0 6px var(--gold),0 10px 28px #0007;margin-top:6px}}
[data-testid="stSidebar"] [role="radiogroup"] label{{padding:7px 10px;border-radius:8px;margin:1px 0;color:#edf6ff}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){{background:linear-gradient(90deg,#e9a915,#f6c94e);color:#08213b;font-weight:900;box-shadow:0 5px 14px #0005}}
.brand-version{{display:flex;justify-content:center;gap:8px;align-items:center;margin:14px 0 18px}}.brand-version b{{background:#f5b927;color:#152238;padding:5px 12px;border-radius:8px;box-shadow:none}}.brand-version span{{background:#0879d9;padding:5px 11px;border-radius:8px;color:white}}
.user-card{{margin-top:18px;padding:13px;border:1px solid #234d70;border-radius:12px;background:#071f38;font-size:14px}}
.kero-top{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid var(--gold);padding:0 4px 10px;margin-bottom:13px}}.kero-top h2{{margin:0;font-size:29px;letter-spacing:-.02em}}.kero-top .premium{{background:#f4b928;color:#17233b;padding:6px 14px;border-radius:8px;font-weight:900;margin-left:10px;box-shadow:none}}.kero-date{{color:#e8f2fb;font-weight:650}}
.exec-title{{font-size:30px;font-weight:900;margin:2px 0 0}}.exec-sub{{color:#d2e1ee;margin-bottom:12px}}
.metric-card{{height:118px;border-radius:12px;padding:14px 15px;border:1px solid #ffffff33;box-shadow:0 8px 22px #0004;position:relative;overflow:hidden}}.metric-card:after{{content:"";position:absolute;width:88px;height:88px;border-radius:50%;right:-32px;top:-32px;background:#fff0f0f0}}.metric-label{{font-size:12px;opacity:.94}}.metric-value{{font-size:24px;font-weight:900;margin-top:8px;white-space:nowrap}}.metric-note{{font-size:11px;margin-top:4px;opacity:.88}}.green{{background:linear-gradient(135deg,#08793f,#035d32)}}.red{{background:linear-gradient(135deg,#d52f28,#a31313)}}.blue{{background:linear-gradient(135deg,#0b78e5,#0750a7)}}.gold{{background:linear-gradient(135deg,#e68c09,#b96000)}}.purple{{background:linear-gradient(135deg,#7a39dc,#412096)}}.teal{{background:linear-gradient(135deg,#07816f,#045a5d)}}.navycard{{background:linear-gradient(135deg,#168da5,#087186)}}
[data-testid="stVerticalBlockBorderWrapper"]{{background:linear-gradient(180deg,#071f38,#04172b);border:1px solid #1a496f !important;border-radius:12px !important;box-shadow:0 8px 24px #0003}}
[data-testid="stVerticalBlockBorderWrapper"] h3{{margin-top:0;color:#fff}}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{{border:1px solid #1b4a70;border-radius:9px;overflow:hidden}}
.alert-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}}.alert-box{{min-height:128px;border-radius:10px;padding:13px;border:1px solid #214a6b;background:#082640}}.alert-box.warn{{background:#3b3316aa;border-color:#b78a17}}.alert-box.danger{{background:#3d2027aa;border-color:#a73b4b}}.alert-box.good{{background:#07392eaa;border-color:#1d7f66}}.alert-icon{{font-size:25px}}.alert-label{{font-size:12px;margin-top:9px;color:#d5e5f1}}.alert-value{{font-size:25px;font-weight:900;margin-top:5px}}.alert-note{{font-size:11px;color:#d3e1ec}}
.footerbar{{display:flex;gap:28px;align-items:center;border-top:1px solid #1d4668;margin-top:13px;padding:11px 2px 2px;color:#d7e5ef;font-size:12px}}.footerbar span:last-child{{margin-left:auto}}
{wm}
</style>
"""


def _card(col, css, icon, label, value, note="Este mês"):
    col.markdown(f"<div class='metric-card {css}'><div class='metric-label'>{icon} &nbsp; {label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)


def _safe_df(sql, params=None):
    try:
        with ui.connect() as conn:
            return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        return pd.DataFrame()


def _moeda_br_num(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _data_br(v):
    try:
        return pd.to_datetime(v).strftime("%d/%m/%Y")
    except Exception:
        return str(v or "")


def _chart_theme(chart):
    return chart.configure_view(strokeOpacity=0).configure_axis(
        labelColor="#dce8f2", titleColor="#dce8f2", gridColor="#173b5a", domainColor="#355d7b", tickColor="#355d7b"
    ).configure_legend(labelColor="#dce8f2", titleColor="#dce8f2")


def painel_executivo():
    m = ui.dashboard_metrics()
    hoje = date.today(); hoje_br = hoje.strftime("%d/%m/%Y"); ano_atual = hoje.year; mes_atual = hoje.month

    vendas_mes = _safe_df(
        "SELECT COALESCE(SUM(total),0) total, COUNT(*) qtd FROM vendas WHERE CAST(substr(data,1,4) AS INTEGER)=? AND CAST(substr(data,6,2) AS INTEGER)=?",
        [ano_atual, mes_atual],
    )
    valor_mes = float(vendas_mes.iloc[0]["total"]) if not vendas_mes.empty else 0.0
    qtd_mes = int(vendas_mes.iloc[0]["qtd"]) if not vendas_mes.empty else 0

    ui.st.markdown(f"<div class='kero-top'><div><h2>Kero Fish ERP <span class='premium'>PREMIUM</span></h2></div><div class='kero-date'>📅 {hoje_br}</div></div>", unsafe_allow_html=True)
    ui.st.markdown("<div class='exec-title'>📊 Painel Geral</div><div class='exec-sub'>Visão executiva de vendas, caixa, compromissos e estoque.</div>", unsafe_allow_html=True)

    cols = ui.st.columns(7, gap="small")
    _card(cols[0], "green", "↥", "Entradas realizadas", ui.moeda(m["entradas"]))
    _card(cols[1], "red", "↧", "Saídas realizadas", ui.moeda(m["saidas"]))
    _card(cols[2], "blue", "▣", "Saldo realizado", ui.moeda(m["saldo"]))
    _card(cols[3], "gold", "♙", "Contas a receber", ui.moeda(m["receber"]), "Pendências")
    _card(cols[4], "purple", "▤", "Contas a pagar", ui.moeda(m["pagar"]), "Pendências")
    _card(cols[5], "teal", "🛒", "Vendas do mês", ui.moeda(valor_mes), hoje.strftime("%m/%Y"))
    _card(cols[6], "navycard", "▥", "Vendas registradas", f"{qtd_mes} pedidos", "Este mês")

    anos_df = _safe_df("SELECT DISTINCT CAST(substr(data,1,4) AS INTEGER) ano FROM vendas WHERE length(data)>=10 ORDER BY ano DESC")
    anos = [int(x) for x in anos_df["ano"].dropna().tolist()] if not anos_df.empty else []
    if ano_atual not in anos: anos.insert(0, ano_atual)
    anos = sorted(set(anos), reverse=True)

    c1, c2, c3 = ui.st.columns([1.45, .9, .95], gap="small")
    with c1:
        with ui.st.container(border=True):
            h1, h2 = ui.st.columns([3,1])
            h1.markdown("### Vendas por mês")
            ano = h2.selectbox("Ano", anos, index=anos.index(ano_atual) if ano_atual in anos else 0, label_visibility="collapsed", key="ano_dashboard")
            mensal = _safe_df("SELECT CAST(substr(data,6,2) AS INTEGER) mes, SUM(COALESCE(total,0)) Vendas FROM vendas WHERE CAST(substr(data,1,4) AS INTEGER)=? GROUP BY CAST(substr(data,6,2) AS INTEGER)", [ano])
            nomes = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
            base = pd.DataFrame({"mes": range(1,13), "Mês": nomes})
            mensal = base.merge(mensal, on="mes", how="left").fillna({"Vendas":0}).sort_values("mes")
            mensal["Valor"] = mensal["Vendas"].apply(_moeda_br_num)
            bars = alt.Chart(mensal).mark_bar(color="#54b8f4", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("Mês:N", sort=nomes, title=None, axis=alt.Axis(labelAngle=-48)),
                y=alt.Y("Vendas:Q", title="Vendas (R$)"),
                tooltip=[alt.Tooltip("Mês:N", title="Mês"), alt.Tooltip("Valor:N", title="Vendas")],
            )
            labels = alt.Chart(mensal).mark_text(dy=-8, color="#f2f7fb", fontSize=10).encode(
                x=alt.X("Mês:N", sort=nomes), y="Vendas:Q", text=alt.Text("Valor:N")
            ).transform_filter("datum.Vendas > 0")
            ui.st.altair_chart(_chart_theme((bars + labels).properties(height=300)), use_container_width=True)
            ui.st.caption("Valores em R$ (Real)")

    with c2:
        with ui.st.container(border=True):
            ui.st.markdown("### Vendas por Categoria")
            cats = _safe_df("SELECT COALESCE(p.categoria,'Outros') Categoria, SUM(COALESCE(v.total,0)) Total FROM vendas v LEFT JOIN produtos p ON lower(trim(p.nome))=lower(trim(v.produto)) WHERE CAST(substr(v.data,1,4) AS INTEGER)=? GROUP BY COALESCE(p.categoria,'Outros') ORDER BY Total DESC", [ano])
            if not cats.empty:
                total = float(cats["Total"].sum())
                cats["Participação"] = cats["Total"].apply(lambda x: f"{(float(x)/total*100):.2f}%".replace(".", ",") if total else "0,00%")
                cats["Valor (R$)"] = cats["Total"].apply(_moeda_br_num)
                tabela = cats[["Categoria","Participação","Valor (R$)"]].copy()
                total_row = pd.DataFrame([{"Categoria":"Total","Participação":"100,00%","Valor (R$)":_moeda_br_num(total)}])
                ui.st.dataframe(pd.concat([tabela,total_row], ignore_index=True), hide_index=True, use_container_width=True, height=300)
            else:
                ui.st.info("Sem vendas no ano selecionado.")

    with c3:
        with ui.st.container(border=True):
            ui.st.markdown(f"### Top 5 Produtos — {ano}")
            top = _safe_df("SELECT produto Produto, SUM(COALESCE(total,0)) Faturamento FROM vendas WHERE CAST(substr(data,1,4) AS INTEGER)=? GROUP BY produto ORDER BY Faturamento DESC LIMIT 5", [ano])
            if not top.empty:
                top["Valor"] = top["Faturamento"].apply(_moeda_br_num)
                chart = alt.Chart(top).mark_bar(color="#58b9f2", cornerRadiusEnd=4).encode(
                    y=alt.Y("Produto:N", sort="-x", title=None, axis=alt.Axis(labelLimit=110)),
                    x=alt.X("Faturamento:Q", title=None),
                    tooltip=[alt.Tooltip("Produto:N"), alt.Tooltip("Valor:N", title="Faturamento")],
                ).properties(height=300)
                ui.st.altair_chart(_chart_theme(chart), use_container_width=True)
                ui.st.caption("Valores em R$ (Real)")
            else:
                ui.st.info("Sem vendas no ano selecionado.")

    estoque = ui.stock_df()
    b1, b2 = ui.st.columns([1.05, 1.35], gap="small")
    with b1:
        with ui.st.container(border=True):
            ui.st.markdown("### 📦 Estoque e Alertas")
            itens = len(estoque) if estoque is not None else 0
            baixo = int((estoque["Situacao"] == "BAIXO").sum()) if estoque is not None and not estoque.empty and "Situacao" in estoque else 0
            negativo = int((estoque["Situacao"] == "NEGATIVO").sum()) if estoque is not None and not estoque.empty and "Situacao" in estoque else 0
            prox = _safe_df("SELECT COUNT(*) qtd FROM compras WHERE validade IS NOT NULL AND TRIM(validade)<>'' AND date(validade) BETWEEN date('now') AND date('now','+30 day')")
            validade = int(prox.iloc[0]["qtd"]) if not prox.empty else 0
            ui.st.markdown(f"""<div class='alert-grid'>
              <div class='alert-box'><div class='alert-icon'>➕</div><div class='alert-label'>Itens cadastrados</div><div class='alert-value'>{itens}</div><div class='alert-note'>produtos</div></div>
              <div class='alert-box warn'><div class='alert-icon'>⚠️</div><div class='alert-label'>Estoque baixo</div><div class='alert-value'>{baixo}</div><div class='alert-note'>produtos</div></div>
              <div class='alert-box danger'><div class='alert-icon'>🔺</div><div class='alert-label'>Estoque negativo</div><div class='alert-value'>{negativo}</div><div class='alert-note'>produtos</div></div>
              <div class='alert-box good'><div class='alert-icon'>⬇</div><div class='alert-label'>Validade próxima</div><div class='alert-value'>{validade}</div><div class='alert-note'>até 30 dias</div></div>
            </div>""", unsafe_allow_html=True)

    with b2:
        with ui.st.container(border=True):
            ui.st.markdown("### 🧾 Últimas Movimentações")
            mov = _safe_df("SELECT data Data, descricao Descrição, tipo Tipo, valor Valor FROM financeiro ORDER BY data DESC,id DESC LIMIT 6")
            if not mov.empty:
                mov["Data"] = mov["Data"].apply(_data_br)
                mov["Valor (R$)"] = mov["Valor"].apply(_moeda_br_num)
                ui.st.dataframe(mov[["Data","Descrição","Tipo","Valor (R$)"]], hide_index=True, use_container_width=True, height=245)
            else:
                ui.st.info("Nenhuma movimentação encontrada.")

    ui.st.markdown(f"<div class='footerbar'><span>👤 Usuário: admin</span><span>♙ Perfil: Administrador</span><span>◉ Banco de dados: {ui.DB_PATH.name}</span><span>🟢 Sistema online</span><span>Kero Fish ERP Premium v{ui.__version__}</span></div>", unsafe_allow_html=True)

ui.painel = painel_executivo
ui.run()
