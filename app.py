# -*- coding: utf-8 -*-
"""Kero Fish ERP Premium 12.1 - painel executivo profissional de teste."""
from __future__ import annotations

import base64
from datetime import date

import altair as alt
import pandas as pd

from kero_fish import ui

_original_bootstrap = ui._bootstrap

def _bootstrap_com_logo_oficial():
    bundled, _ = _original_bootstrap()
    return bundled, ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
ui._bootstrap = _bootstrap_com_logo_oficial

def _sidebar_profissional(logo):
    pages = ["▦  Painel Geral", "◫  Produtos", "♟  Fornecedores", "🛒  Compras", "◈  Estoque", "♙  Clientes", "🛍  Vendas", "◉  Financeiro", "▤  Despesas", "▣  Contas a Pagar", "▧  Contas a Receber", "▰  Entregas", "▥  Relatórios", "⇩  Importar Planilha", "⌕  Auditoria", "◉  Diagnóstico", "☁  Backup"]
    mapping = {p: p.split("  ", 1)[1] for p in pages}
    with ui.st.sidebar:
        if logo.exists(): ui.st.image(str(logo), width=175)
        ui.st.markdown(f"<div class='brand-version'><b>PREMIUM</b><span>v{ui.__version__}</span></div>", unsafe_allow_html=True)
        selected = ui.st.radio("Navegação", pages, label_visibility="collapsed")
        ui.st.markdown("<div class='user-card'>👤 &nbsp; <b>Marcos Robério</b><br><small>Administrador</small></div>", unsafe_allow_html=True)
        return mapping[selected]
ui.sidebar = _sidebar_profissional

_logo_path = ui.APP_ROOT / "IMG-20260826-WA0013 (1).jpg"
wm = ""
if _logo_path.exists():
    b64 = base64.b64encode(_logo_path.read_bytes()).decode("ascii")
    wm = ('[data-testid="stAppViewContainer"]::before{content:"";position:fixed;left:58%;top:53%;' 'width:min(36vw,520px);aspect-ratio:1;transform:translate(-50%,-50%);' f'background:url("data:image/jpeg;base64,{b64}") center/contain no-repeat;' 'opacity:.014;pointer-events:none;z-index:0}')

ui.PREMIUM_CSS = f"""<style>
:root{{--navy:#031426;--navy2:#061e38;--gold:#f1b92f}} html,body,[class*="css"]{{font-family:Inter,Segoe UI,Arial,sans-serif}} .stApp{{background:linear-gradient(135deg,#061d35 0%,#031426 55%,#041a30 100%);color:#fff}} [data-testid="stHeader"]{{background:#031426e8;border-bottom:1px solid #174b76}} .block-container{{padding-top:3.4rem!important;max-width:none!important;width:100%!important;padding-left:.7rem!important;padding-right:.7rem!important}} [data-testid="stSidebar"]{{width:220px!important;min-width:220px!important;max-width:220px!important;background:linear-gradient(180deg,#04182c 0%,#021120 100%);border-right:1px solid #1c4468;box-shadow:8px 0 30px #0006}} [data-testid="stSidebar"]>div:first-child{{width:220px!important}} [data-testid="stSidebar"] img{{border-radius:50%;border:3px solid var(--gold);box-shadow:0 0 0 4px #fff,0 0 0 6px var(--gold),0 10px 28px #0007;margin:4px auto 0}} [data-testid="stSidebar"] [role="radiogroup"] label{{padding:6px 8px;border-radius:8px;margin:0;color:#edf6ff;font-size:13px}} [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){{background:linear-gradient(90deg,#e9a915,#f6c94e);color:#08213b;font-weight:900;box-shadow:0 5px 14px #0005}} .brand-version{{display:flex;justify-content:center;gap:6px;align-items:center;margin:12px 0 14px}}.brand-version b{{background:#f5b927;color:#152238;padding:5px 10px;border-radius:8px}}.brand-version span{{background:#0879d9;padding:5px 9px;border-radius:8px;color:white}} .user-card{{margin-top:12px;padding:10px;border:1px solid #234d70;border-radius:10px;background:#071f38;font-size:12px}} .kero-top{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid var(--gold);padding:0 2px 8px;margin:0 0 10px}}.kero-top h2{{margin:0;font-size:26px;line-height:1.25}}.kero-top .premium{{background:#f4b928;color:#17233b;padding:5px 12px;border-radius:8px;font-weight:900;margin-left:8px;display:inline-block;vertical-align:middle}}.kero-date{{color:#e8f2fb;font-weight:650;font-size:13px}} .exec-title{{font-size:27px;font-weight:900;margin:0}}.exec-sub{{color:#d2e1ee;margin-bottom:10px;font-size:13px}} .kpi-grid{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:8px;margin-bottom:10px}} .metric-card{{min-width:0;height:108px;border-radius:11px;padding:12px 11px;border:1px solid #ffffff2b;box-shadow:0 7px 20px #0004;position:relative;overflow:hidden}}.metric-card:after{{content:"";position:absolute;width:70px;height:70px;border-radius:50%;right:-27px;top:-28px;background:#ffffff16}} .metric-label{{font-size:10.5px;line-height:1.15;opacity:.96;min-height:24px}}.metric-value{{font-size:19px;font-weight:900;margin-top:5px;white-space:nowrap;letter-spacing:-.02em}}.metric-note{{font-size:9.5px;margin-top:4px;opacity:.88}} .green{{background:linear-gradient(135deg,#08793f,#035d32)}}.red{{background:linear-gradient(135deg,#d52f28,#a31313)}}.blue{{background:linear-gradient(135deg,#0b78e5,#0750a7)}}.gold{{background:linear-gradient(135deg,#e68c09,#b96000)}}.purple{{background:linear-gradient(135deg,#7a39dc,#412096)}}.teal{{background:linear-gradient(135deg,#07816f,#045a5d)}}.navycard{{background:linear-gradient(135deg,#168da5,#087186)}} [data-testid="stVerticalBlockBorderWrapper"]{{background:linear-gradient(180deg,#071f38,#04172b);border:1px solid #1a496f!important;border-radius:12px!important;box-shadow:0 8px 24px #0003}} [data-testid="stVerticalBlockBorderWrapper"] h3{{margin-top:0;color:#fff;font-size:18px}} [data-testid="stDataFrame"],[data-testid="stDataEditor"]{{border:1px solid #1b4a70;border-radius:9px;overflow:hidden}} .alert-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}}.alert-box{{min-height:118px;border-radius:10px;padding:11px;border:1px solid #214a6b;background:#082640}}.alert-box.warn{{background:#3b3316aa;border-color:#b78a17}}.alert-box.danger{{background:#3d2027aa;border-color:#a73b4b}}.alert-box.good{{background:#07392eaa;border-color:#1d7f66}}.alert-icon{{font-size:22px}}.alert-label{{font-size:11px;margin-top:7px;color:#d5e5f1}}.alert-value{{font-size:22px;font-weight:900;margin-top:4px}}.alert-note{{font-size:10px;color:#d3e1ec}} .footerbar{{display:flex;gap:22px;align-items:center;border-top:1px solid #1d4668;margin-top:10px;padding:9px 2px 2px;color:#d7e5ef;font-size:11px}}.footerbar span:last-child{{margin-left:auto}} @media(max-width:1180px){{.kpi-grid{{grid-template-columns:repeat(4,minmax(0,1fr))}}}} {wm}
</style>"""

def _safe_df(sql, params=None):
    try:
        with ui.connect() as conn: return pd.read_sql_query(sql, conn, params=params)
    except Exception: return pd.DataFrame()
def _moeda_br_num(v):
    try: return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception: return "R$ 0,00"
def _data_br(v):
    try: return pd.to_datetime(v, errors="coerce", dayfirst=True).strftime("%d/%m/%Y")
    except Exception: return str(v or "")
def _parse_dates(series):
    try: return pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)
    except TypeError: return pd.to_datetime(series, errors="coerce", dayfirst=True)
def _chart_theme(chart): return chart.configure_view(strokeOpacity=0).configure_axis(labelColor="#dce8f2", titleColor="#dce8f2", gridColor="#173b5a", domainColor="#355d7b", tickColor="#355d7b").configure_legend(labelColor="#dce8f2", titleColor="#dce8f2")
def _kpi_html(items):
    return "<div class='kpi-grid'>" + "".join(f"<div class='metric-card {css}'><div class='metric-label'>{icon}&nbsp;&nbsp;{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>" for css,icon,label,value,note in items) + "</div>"

def painel_executivo():
    m=ui.dashboard_metrics(); hoje=date.today(); hoje_br=hoje.strftime("%d/%m/%Y"); ano_atual=hoje.year; mes_atual=hoje.month
    vendas_raw=_safe_df("SELECT id,data,produto,COALESCE(quantidade,0) quantidade,COALESCE(total,0) total FROM vendas")
    if not vendas_raw.empty:
        vendas_raw["dt"]=_parse_dates(vendas_raw["data"]); vendas_raw["total"]=pd.to_numeric(vendas_raw["total"],errors="coerce").fillna(0.0); vendas_raw["quantidade"]=pd.to_numeric(vendas_raw["quantidade"],errors="coerce").fillna(0.0)
    else: vendas_raw=pd.DataFrame(columns=["id","data","produto","quantidade","total","dt"])
    vendas_atuais=vendas_raw[(vendas_raw["dt"].dt.year==ano_atual)&(vendas_raw["dt"].dt.month==mes_atual)] if not vendas_raw.empty else vendas_raw; valor_mes=float(vendas_atuais["total"].sum()) if not vendas_atuais.empty else 0.0; qtd_mes=int(len(vendas_atuais))
    ui.st.markdown(f"<div class='kero-top'><div><h2>Kero Fish ERP <span class='premium'>PREMIUM</span></h2></div><div class='kero-date'>📅 {hoje_br}</div></div>",unsafe_allow_html=True); ui.st.markdown("<div class='exec-title'>📊 Painel Geral</div><div class='exec-sub'>Visão executiva de vendas, caixa, compromissos e estoque.</div>",unsafe_allow_html=True)
    ui.st.markdown(_kpi_html([("green","↥","Entradas realizadas",ui.moeda(m["entradas"]),"Este mês"),("red","↧","Saídas realizadas",ui.moeda(m["saidas"]),"Este mês"),("blue","▣","Saldo realizado",ui.moeda(m["saldo"]),"Este mês"),("gold","♙","Contas a receber",ui.moeda(m["receber"]),"Pendências"),("purple","▤","Contas a pagar",ui.moeda(m["pagar"]),"Pendências"),("teal","🛒","Vendas do mês",ui.moeda(valor_mes),hoje.strftime("%m/%Y")),("navycard","▥","Vendas registradas",f"{qtd_mes} pedidos","Este mês")]),unsafe_allow_html=True)
    anos=sorted({int(y) for y in vendas_raw["dt"].dropna().dt.year.tolist()}|{ano_atual},reverse=True); c1,c2,c3=ui.st.columns([1.28,.82,1.12],gap="small")
    with c1:
        with ui.st.container(border=True):
            h1,h2=ui.st.columns([3,1]); h1.markdown("### Vendas por mês"); ano=h2.selectbox("Ano",anos,index=anos.index(ano_atual),label_visibility="collapsed",key="ano_dashboard"); nomes=["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
            ano_df=vendas_raw[vendas_raw["dt"].dt.year==ano].copy() if not vendas_raw.empty else vendas_raw.copy(); mensal_sum=pd.DataFrame(columns=["mes","Vendas"])
            if not ano_df.empty: ano_df["mes"]=ano_df["dt"].dt.month; mensal_sum=ano_df.groupby("mes",as_index=False)["total"].sum().rename(columns={"total":"Vendas"})
            mensal=pd.DataFrame({"mes":range(1,13),"Mês":nomes}).merge(mensal_sum,on="mes",how="left").fillna({"Vendas":0.0}); mensal["Valor"]=mensal["Vendas"].apply(_moeda_br_num); x_axis=alt.Axis(labelAngle=-50,labelOverlap=False,labelLimit=90,values=nomes,title=None)
            max_vendas=max(float(mensal["Vendas"].max()),1.0); teto=max_vendas*1.18; y_axis=alt.Axis(title="Vendas (R$)",labelExpr="replace(format(datum.value, ',.0f'), ',', '.')")
            barras_base=alt.Chart(mensal).encode(x=alt.X("Mês:N",sort=nomes,axis=x_axis),y=alt.Y("Vendas:Q",scale=alt.Scale(domain=[0,teto],nice=False),axis=y_axis))
            bars=barras_base.mark_bar(color="#E2B84B",cornerRadiusTopLeft=3,cornerRadiusTopRight=3,size=24).encode(tooltip=[alt.Tooltip("Mês:N",title="Mês"),alt.Tooltip("Valor:N",title="Vendas")]); labels=barras_base.mark_text(dy=-8,color="#f7e7b3",fontSize=9,clip=False).encode(text=alt.Text("Valor:N")).transform_filter("datum.Vendas > 0"); ui.st.altair_chart(_chart_theme((bars+labels).properties(height=300)),use_container_width=True); ui.st.caption("Valores em R$ (Real) • Janeiro a Dezembro")
    produtos=_safe_df("SELECT nome,categoria FROM produtos"); categoria_map={str(r["nome"]).strip().lower():str(r["categoria"] or "Outros") for _,r in produtos.iterrows()} if not produtos.empty else {}; ano_vendas=vendas_raw[vendas_raw["dt"].dt.year==ano].copy() if not vendas_raw.empty else vendas_raw.copy()
    if not ano_vendas.empty: ano_vendas["Categoria"]=ano_vendas["produto"].astype(str).str.strip().str.lower().map(categoria_map).fillna("Outros")
    with c2:
        with ui.st.container(border=True):
            ui.st.markdown("### Vendas por Categoria")
            if not ano_vendas.empty:
                cats=ano_vendas.groupby("Categoria",as_index=False)["total"].sum().sort_values("total",ascending=False); total_cat=float(cats["total"].sum()); cats["Participação"]=cats["total"].apply(lambda x:f"{(float(x)/total_cat*100):.2f}%".replace(".",",") if total_cat else "0,00%"); cats["Valor (R$)"]=cats["total"].apply(_moeda_br_num); tabela=cats[["Categoria","Participação","Valor (R$)"]]; total_row=pd.DataFrame([{"Categoria":"Total","Participação":"100,00%","Valor (R$)":_moeda_br_num(total_cat)}]); ui.st.dataframe(pd.concat([tabela,total_row],ignore_index=True),hide_index=True,use_container_width=True,height=280)
            else: ui.st.info("Sem vendas no ano selecionado.")
    with c3:
        with ui.st.container(border=True):
            ui.st.markdown(f"### Top 15 Produtos — {ano}")
            if not ano_vendas.empty:
                top=ano_vendas.groupby("produto",as_index=False).agg(total=("total","sum"),quantidade=("quantidade","sum")).sort_values("total",ascending=False).head(15); top["rotulo"]=top.apply(lambda r:f"{_moeda_br_num(r['total'])} • {float(r['quantidade']):,.2f} kg".replace(",","X").replace(".",",").replace("X","."),axis=1); base=alt.Chart(top).encode(y=alt.Y("produto:N",sort=alt.SortField(field="total",order="descending"),title=None,axis=alt.Axis(labelColor="#e6f0f7",labelLimit=130)),x=alt.X("total:Q",title=None,axis=alt.Axis(labelColor="#dce8f2",gridColor="#173b5a"))); bars_top=base.mark_bar(color="#E2B84B",cornerRadiusEnd=3,size=11).encode(tooltip=[alt.Tooltip("produto:N",title="Produto"),alt.Tooltip("total:Q",title="Faturamento",format=",.2f"),alt.Tooltip("quantidade:Q",title="Quantidade (kg)",format=",.2f")]); labels_top=base.mark_text(align="left",baseline="middle",dx=5,color="#f7e7b3",fontSize=9).encode(text=alt.Text("rotulo:N")); ui.st.altair_chart(_chart_theme((bars_top+labels_top).properties(height=445)).configure_view(continuousWidth=430),use_container_width=True)
            else: ui.st.info("Sem vendas no ano selecionado.")
            ui.st.caption("Ranking por faturamento • R$ e quantidade vendida em kg")
    estoque=ui.stock_df(); n_prod=len(estoque) if estoque is not None else 0; n_baixo=int((estoque["Situacao"]=="BAIXO").sum()) if estoque is not None and not estoque.empty and "Situacao" in estoque else 0; n_neg=int((estoque["Situacao"]=="NEGATIVO").sum()) if estoque is not None and not estoque.empty and "Situacao" in estoque else 0; left,right=ui.st.columns([1.02,1.28],gap="small")
    with left:
        with ui.st.container(border=True): ui.st.markdown("### 📦 Estoque e Alertas"); ui.st.markdown(f"<div class='alert-grid'><div class='alert-box'><div class='alert-icon'>＋</div><div class='alert-label'>Itens cadastrados</div><div class='alert-value'>{n_prod}</div><div class='alert-note'>produtos</div></div><div class='alert-box warn'><div class='alert-icon'>⚠</div><div class='alert-label'>Estoque baixo</div><div class='alert-value'>{n_baixo}</div><div class='alert-note'>produtos</div></div><div class='alert-box danger'><div class='alert-icon'>▲</div><div class='alert-label'>Estoque negativo</div><div class='alert-value'>{n_neg}</div><div class='alert-note'>produtos</div></div><div class='alert-box good'><div class='alert-icon'>↓</div><div class='alert-label'>Validade próxima</div><div class='alert-value'>—</div><div class='alert-note'>verificar lotes</div></div></div>",unsafe_allow_html=True)
    with right:
        with ui.st.container(border=True):
            ui.st.markdown("### 🧾 Últimas Movimentações"); mov=_safe_df("SELECT data,descricao,tipo,valor FROM financeiro ORDER BY data DESC,id DESC LIMIT 5")
            if not mov.empty: mov.columns=["Data","Descrição","Tipo","Valor (R$)"]; mov["Data"]=mov["Data"].apply(_data_br); mov["Valor (R$)"]=mov["Valor (R$)"].apply(_moeda_br_num); ui.st.dataframe(mov,hide_index=True,use_container_width=True,height=210)
            else: ui.st.info("Nenhuma movimentação encontrada.")
    ui.st.markdown(f"<div class='footerbar'><span>👤 Usuário: admin</span><span>♙ Perfil: Administrador</span><span>🗄 Banco de dados: {ui.DB_PATH.name}</span><span>● Sistema online</span><span>Kero Fish ERP Premium v{ui.__version__}</span></div>",unsafe_allow_html=True)

ui.painel=painel_executivo
ui.run()
