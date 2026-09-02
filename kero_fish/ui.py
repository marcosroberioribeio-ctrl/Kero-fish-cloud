from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from . import APP_NAME, __version__
from .bundled_data import ensure_workbook
from .db import APP_ROOT, BACKUP_DIR, DB_PATH, connect, init_db
from .importer import import_excel
from .professional import (
    health_report,
    recent_audit,
    register_purchase_safe,
    register_sale_safe,
    restore_backup,
    safe_backup,
)
from .services import dashboard_metrics, query_df, save_grid, stock_df
from .utils import moeda, hoje

PREMIUM_CSS = """
<style>
:root { --kero-navy:#071a33; --kero-blue:#0f3a69; --kero-cyan:#17d4e8; --kero-gold:#d7a438; }
.stApp { background: radial-gradient(circle at 75% 0%, #102d50 0%, #071a33 35%, #041225 100%); color:#f6fbff; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#102a4b 0%,#071a33 100%); border-right:1px solid rgba(255,255,255,.08); }
[data-testid="stMetric"] { background:rgba(8,32,60,.78); border:1px solid rgba(23,212,232,.16); border-radius:16px; padding:14px 16px; box-shadow:0 12px 30px rgba(0,0,0,.18); }
[data-testid="stDataFrame"] { border:1px solid rgba(23,212,232,.22); border-radius:14px; overflow:hidden; }
div.stButton > button { border-radius:10px; font-weight:700; border:1px solid rgba(23,212,232,.35); }
div.stButton > button[kind="primary"] { background:linear-gradient(90deg,#11c7df,#37e4d6); color:#041225; border:0; }
.kero-title { font-size:2rem; font-weight:800; letter-spacing:-.02em; margin-bottom:.1rem; }
.kero-sub { color:#9fc6e8; margin-bottom:1rem; }
.kero-card { background:rgba(7,26,51,.78); border:1px solid rgba(255,255,255,.08); border-radius:16px; padding:16px; margin-bottom:14px; }
.kero-badge { display:inline-block; padding:6px 10px; border-radius:999px; background:rgba(23,212,232,.12); color:#8cf4ff; border:1px solid rgba(23,212,232,.24); font-size:.82rem; font-weight:700; }
.kero-ok { color:#7ff7b2; font-weight:700; }
.kero-warn { color:#ffd479; font-weight:700; }
</style>
"""


def _bootstrap() -> tuple[Path, Path]:
    init_db()
    bundled = APP_ROOT / "data" / "KERO FISH_Financeira_Completa_Preenchida.xlsx"
    logo = APP_ROOT / "logo.jpg.jpg"
    ensure_workbook(bundled)

    if bundled.exists() and "auto_import_done" not in st.session_state:
        try:
            st.session_state["auto_import_report"] = import_excel(bundled, create_backup=False)
        except Exception as exc:
            st.session_state["auto_import_error"] = str(exc)
        st.session_state["auto_import_done"] = True
    return bundled, logo


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"<div class='kero-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<div class='kero-sub'>{subtitle}</div>", unsafe_allow_html=True)


def sidebar(logo: Path) -> str:
    with st.sidebar:
        st.markdown("## Kero Fish")
        if logo.exists():
            st.image(str(logo), use_container_width=True)
        st.markdown("<div style='text-align:center;font-weight:800;letter-spacing:.08em;margin-top:-8px'>PEIXE E CAMARÃO</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kero-badge'>ERP Premium v{__version__}</div>", unsafe_allow_html=True)
        st.caption(f"Banco: {DB_PATH.name}")

        report = st.session_state.get("auto_import_report")
        if report:
            st.success(f"Base sincronizada: {report.inserted['compras']} compra(s), {report.inserted['vendas']} venda(s) nova(s).")
        if st.session_state.get("auto_import_error"):
            st.error("Falha na sincronização inicial: " + st.session_state["auto_import_error"])

        st.markdown("---")
        pages = [
            "Painel Geral", "Produtos", "Fornecedores", "Compras", "Estoque", "Clientes",
            "Vendas", "Financeiro", "Despesas", "Contas a Pagar", "Contas a Receber",
            "Entregas", "Relatórios", "Importar Planilha", "Auditoria", "Diagnóstico", "Backup"
        ]
        return st.radio("Navegação", pages, label_visibility="collapsed")


def editable_grid(table: str, sql: str, editable: list[str], disabled: list[str] | None = None, key: str | None = None) -> None:
    df = query_df(sql)
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return
    edited = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=(disabled or ["id"]),
        key=key or f"grid_{table}",
        height=460,
    )
    if st.button("💾 Salvar alterações", type="primary", key=f"save_{table}_{key}"):
        try:
            n = save_grid(table, df, edited, editable)
            if n:
                st.success(f"{n} registro(s) atualizado(s).")
                st.rerun()
            st.info("Nenhuma alteração detectada.")
        except Exception as exc:
            st.error(f"Não foi possível salvar: {exc}")


def painel() -> None:
    page_header("📊 Painel Geral", "Visão executiva de vendas, caixa, compromissos e estoque.")
    m = dashboard_metrics()
    c = st.columns(4)
    c[0].metric("Entradas realizadas", moeda(m["entradas"]))
    c[1].metric("Saídas realizadas", moeda(m["saidas"]))
    c[2].metric("Saldo realizado", moeda(m["saldo"]))
    c[3].metric("Faturamento", moeda(m["vendas"]))
    c2 = st.columns(4)
    c2[0].metric("Contas a receber", moeda(m["receber"]))
    c2[1].metric("Contas a pagar", moeda(m["pagar"]))
    c2[2].metric("Vendas registradas", m["qtd_vendas"])
    c2[3].metric("Compras registradas", m["qtd_compras"])

    st.markdown("### Estoque e alertas")
    estoque_df = stock_df()
    st.dataframe(estoque_df, use_container_width=True, hide_index=True)
    neg = estoque_df[estoque_df["Situacao"] == "NEGATIVO"] if not estoque_df.empty else estoque_df
    if not neg.empty:
        st.warning("Há produto(s) com estoque negativo. Revise as entradas históricas antes de novas vendas.")


def produtos() -> None:
    page_header("🐟 Produtos", "Cadastro mestre com preços, custo e estoque mínimo.")
    with st.expander("➕ Novo produto", expanded=False):
        with st.form("novo_produto"):
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Produto *")
            categoria = c2.text_input("Categoria", "Outros")
            unidade = c3.text_input("Unidade", "kg")
            c4, c5, c6 = st.columns(3)
            custo = c4.number_input("Custo médio", 0.0, step=.01)
            preco = c5.number_input("Preço de venda", 0.0, step=.01)
            minimo = c6.number_input("Estoque mínimo", 0.0, step=.01)
            fornecedor = st.text_input("Fornecedor padrão")
            if st.form_submit_button("Cadastrar", type="primary") and nome.strip():
                with connect() as conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO produtos(nome,categoria,unidade,custo_medio,preco_venda,estoque_minimo,fornecedor_padrao,ativo) VALUES (?,?,?,?,?,?,?,1)",
                        (nome.strip(), categoria, unidade, custo, preco, minimo, fornecedor),
                    )
                st.rerun()
    editable_grid(
        "produtos",
        "SELECT id,nome,categoria,unidade,preco_venda,custo_medio,estoque_minimo,fornecedor_padrao,ativo FROM produtos ORDER BY nome",
        ["nome", "categoria", "unidade", "preco_venda", "custo_medio", "estoque_minimo", "fornecedor_padrao", "ativo"],
        ["id"],
        "produtos",
    )


def fornecedores() -> None:
    page_header("🚚 Fornecedores", "Fornecedores vinculados aos produtos e compras.")
    with st.form("novo_fornecedor"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Fornecedor *")
        tel = c2.text_input("Telefone")
        contato = c3.text_input("Contato")
        endereco = st.text_input("Endereço")
        produto = st.text_input("Produto fornecido")
        if st.form_submit_button("Cadastrar fornecedor", type="primary") and nome.strip():
            with connect() as conn:
                conn.execute(
                    "INSERT INTO fornecedores(fornecedor,telefone,contato,endereco,produto_fornecido,ativo) VALUES (?,?,?,?,?,1)",
                    (nome.strip(), tel, contato, endereco, produto),
                )
            st.rerun()
    editable_grid(
        "fornecedores",
        "SELECT id,fornecedor,contato,telefone,endereco,produto_fornecido,prazo_pagamento,observacoes,ativo FROM fornecedores ORDER BY fornecedor",
        ["fornecedor", "contato", "telefone", "endereco", "produto_fornecido", "prazo_pagamento", "observacoes", "ativo"],
        ["id"],
        "fornecedores",
    )


def clientes() -> None:
    page_header("👥 Clientes", "Cadastro de clientes e dados de entrega.")
    with st.form("novo_cliente"):
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome *")
        tel = c2.text_input("Telefone")
        cidade = c3.text_input("Cidade")
        endereco = st.text_input("Endereço")
        obs = st.text_area("Observações")
        if st.form_submit_button("Cadastrar cliente", type="primary") and nome.strip():
            with connect() as conn:
                conn.execute(
                    "INSERT INTO clientes(nome,telefone,cidade,endereco,observacoes,ativo) VALUES (?,?,?,?,?,1)",
                    (nome.strip(), tel, cidade, endereco, obs),
                )
            st.rerun()
    editable_grid(
        "clientes",
        "SELECT id,nome,telefone,cidade,endereco,observacoes,ativo FROM clientes ORDER BY nome",
        ["nome", "telefone", "cidade", "endereco", "observacoes", "ativo"],
        ["id"],
        "clientes",
    )


def compras() -> None:
    page_header("📦 Compras", "Entrada de mercadoria integrada ao estoque e ao contas a pagar.")
    with st.form("nova_compra"):
        c1, c2, c3 = st.columns(3)
        data = c1.date_input("Data", date.today())
        fornecedor = c2.text_input("Fornecedor *")
        produto = c3.text_input("Produto *")
        c4, c5, c6 = st.columns(3)
        qtd = c4.number_input("Quantidade", 0.0, step=.01)
        custo = c5.number_input("Custo unitário", 0.0, step=.01)
        pgto = c6.selectbox("Pagamento", ["A prazo", "PIX", "Dinheiro", "Cartão", "Transferência"])
        lote = st.text_input("Lote")
        validade = st.text_input("Validade")
        local = st.text_input("Local de estoque")
        pago = st.checkbox("Compra já paga")
        if st.form_submit_button("Registrar compra", type="primary"):
            try:
                register_purchase_safe(data.isoformat(), fornecedor, produto, qtd, custo, lote, validade, local, pgto, "Pago" if pago else "Pendente")
                st.success("Compra registrada, validada e integrada.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    editable_grid(
        "compras",
        "SELECT id,data,fornecedor,produto,quantidade,custo_unitario,total,lote,validade,local_estoque,forma_pagamento,status_pagamento,vencimento FROM compras ORDER BY data DESC,id DESC",
        ["data", "fornecedor", "produto", "quantidade", "custo_unitario", "total", "lote", "validade", "local_estoque", "forma_pagamento", "status_pagamento", "vencimento"],
        ["id"],
        "compras",
    )


def vendas() -> None:
    page_header("🧾 Vendas", "Pedidos com validação de estoque, recebimentos e entregas.")
    with st.form("nova_venda"):
        c1, c2, c3 = st.columns(3)
        data = c1.date_input("Data", date.today())
        cliente = c2.text_input("Cliente *")
        produto = c3.text_input("Produto *")
        c4, c5, c6 = st.columns(3)
        qtd = c4.number_input("Quantidade", 0.0, step=.01)
        preco = c5.number_input("Preço unitário", 0.0, step=.01)
        desc = c6.number_input("Desconto", 0.0, step=.01)
        c7, c8, c9 = st.columns(3)
        forma = c7.selectbox("Pagamento", ["PIX", "Dinheiro", "Cartão", "Transferência", "A prazo"])
        recebido = c8.number_input("Valor recebido", 0.0, step=.01)
        entrega = c9.checkbox("Tem entrega")
        status = st.selectbox("Status do pedido", ["Em preparação", "Aguardando", "Saiu para entrega", "Entregue", "Cancelado"])
        if st.form_submit_button("Registrar venda", type="primary"):
            try:
                register_sale_safe(data.isoformat(), cliente, produto, qtd, preco, desc, forma, recebido, status, entrega)
                st.success("Venda registrada, validada e integrada.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    editable_grid(
        "vendas",
        "SELECT id,pedido,data,cliente,produto,quantidade,preco_unitario,desconto,total,forma_pagamento,status_pagamento,valor_recebido,vencimento,status_pedido,entrega FROM vendas ORDER BY data DESC,id DESC",
        ["data", "cliente", "produto", "quantidade", "preco_unitario", "desconto", "total", "forma_pagamento", "status_pagamento", "valor_recebido", "vencimento", "status_pedido", "entrega"],
        ["id", "pedido"],
        "vendas",
    )


def simple_page(title: str, subtitle: str, table: str, sql: str, editable: list[str]) -> None:
    page_header(title, subtitle)
    editable_grid(table, sql, editable, ["id"], table)


def estoque() -> None:
    page_header("🧊 Estoque", "Saldo calculado por movimentos. Compras entram; vendas saem; ajustes ficam auditáveis.")
    st.dataframe(stock_df(), use_container_width=True, hide_index=True)
    with st.form("ajuste_estoque"):
        c1, c2, c3 = st.columns(3)
        produto = c1.text_input("Produto")
        tipo = c2.selectbox("Tipo", ["AJUSTE_ENTRADA", "AJUSTE_SAIDA", "PERDA"])
        qtd = c3.number_input("Quantidade", 0.0, step=.01)
        obs = st.text_input("Motivo/observação")
        if st.form_submit_button("Registrar ajuste") and produto.strip() and qtd > 0:
            sinal = qtd if tipo == "AJUSTE_ENTRADA" else -qtd
            with connect() as conn:
                conn.execute(
                    "INSERT INTO movimentos_estoque(data,produto,tipo,quantidade,origem,origem_id,observacao) VALUES (?,?,?,?,?,?,?)",
                    (hoje(), produto.strip(), tipo, sinal, "Ajuste", None, obs),
                )
                conn.execute(
                    "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (datetime('now','localtime'),'CREATE','estoque',NULL,?)",
                    (f"{tipo} | {produto.strip()} | {qtd} | {obs}",),
                )
            st.rerun()
    st.markdown("### Histórico de movimentos")
    st.dataframe(query_df("SELECT * FROM movimentos_estoque ORDER BY id DESC LIMIT 1000"), use_container_width=True, hide_index=True)


def relatorios() -> None:
    page_header("📈 Relatórios", "Indicadores gerenciais para decisão.")
    st.markdown("### Vendas por produto")
    st.dataframe(query_df("SELECT produto,COUNT(*) pedidos,SUM(quantidade) quantidade,SUM(total) faturamento FROM vendas GROUP BY produto ORDER BY faturamento DESC"), use_container_width=True, hide_index=True)
    st.markdown("### Compras por fornecedor")
    st.dataframe(query_df("SELECT fornecedor,COUNT(*) compras,SUM(total) total_comprado FROM compras GROUP BY fornecedor ORDER BY total_comprado DESC"), use_container_width=True, hide_index=True)
    st.markdown("### Fluxo por categoria")
    st.dataframe(query_df("SELECT tipo,categoria,SUM(valor) valor FROM financeiro GROUP BY tipo,categoria ORDER BY tipo,categoria"), use_container_width=True, hide_index=True)


def importar() -> None:
    page_header("📥 Importar Planilha", "Importação idempotente e protegida por backup.")
    up = st.file_uploader("Selecione a planilha Excel", type=["xlsx"])
    if up and st.button("Importar agora", type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(up.getvalue())
            temp = Path(tmp.name)
        try:
            safe_backup("pre_import")
            r = import_excel(temp, create_backup=False)
            st.success("Importação concluída.")
            st.json({"inseridos": r.inserted, "ignorados_existentes": r.skipped, "avisos": r.warnings})
        except Exception as exc:
            st.error(str(exc))
        finally:
            temp.unlink(missing_ok=True)


def auditoria() -> None:
    page_header("🛡️ Auditoria", "Rastreabilidade de operações, alterações e importações.")
    t1, t2 = st.tabs(["Operações do ERP", "Importações"])
    with t1:
        audit = recent_audit(1000)
        if audit.empty:
            st.info("Nenhum evento de auditoria registrado.")
        else:
            st.dataframe(audit, use_container_width=True, hide_index=True)
    with t2:
        st.dataframe(query_df("SELECT * FROM import_log ORDER BY id DESC LIMIT 2000"), use_container_width=True, hide_index=True)


def diagnostico() -> None:
    page_header("🩺 Diagnóstico do Sistema", "Saúde operacional, integridade do banco e alertas preventivos.")
    h = health_report()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Banco", "OK" if h.database_ok else "ATENÇÃO")
    c2.metric("Integridade SQLite", h.integrity.upper())
    c3.metric("Backups", h.backups)
    c4.metric("Tamanho do banco", f"{h.database_size_mb:.2f} MB".replace(".", ","))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("FK inconsistentes", h.foreign_key_issues)
    c6.metric("Estoque negativo", h.negative_stock_items)
    c7.metric("Contas a pagar vencidas", h.overdue_payables)
    c8.metric("Contas a receber vencidas", h.overdue_receivables)

    st.markdown(f"**Último backup:** {h.last_backup}")
    st.markdown(f"**Arquivo do banco:** `{DB_PATH}`")
    if h.database_ok:
        st.success("Banco íntegro e sem violações de chave estrangeira detectadas.")
    else:
        st.error("O diagnóstico encontrou uma inconsistência. Não faça migrações até revisar o banco.")


def backup() -> None:
    page_header("💾 Backup e Recuperação", "Snapshot consistente do SQLite, verificação de integridade e restauração protegida.")
    if st.button("Criar backup seguro agora", type="primary"):
        try:
            p = safe_backup("manual")
            if p:
                st.success(f"Backup validado: {p.name}")
        except Exception as exc:
            st.error(str(exc))

    arquivos = sorted(BACKUP_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True) if BACKUP_DIR.exists() else []
    if not arquivos:
        st.info("Nenhum backup encontrado.")
        return

    st.dataframe(
        pd.DataFrame([{"arquivo": p.name, "tamanho_kb": round(p.stat().st_size / 1024, 1)} for p in arquivos]),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Restaurar backup")
    st.warning("Antes da restauração o ERP cria automaticamente um backup de emergência da base atual.")
    escolhido = st.selectbox("Backup", [p.name for p in arquivos])
    confirmar = st.checkbox("Confirmo que desejo restaurar este backup.")
    if st.button("↩️ Restaurar", disabled=not confirmar):
        try:
            emergency = restore_backup(BACKUP_DIR / escolhido)
            st.success(f"Restauração concluída. Cópia de emergência: {emergency.name}")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def run() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="🐟", layout="wide", initial_sidebar_state="expanded")
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)
    _, logo = _bootstrap()
    page = sidebar(logo)

    if page == "Painel Geral": painel()
    elif page == "Produtos": produtos()
    elif page == "Fornecedores": fornecedores()
    elif page == "Clientes": clientes()
    elif page == "Compras": compras()
    elif page == "Vendas": vendas()
    elif page == "Estoque": estoque()
    elif page == "Financeiro": simple_page("💰 Financeiro", "Entradas e saídas realizadas.", "financeiro", "SELECT id,data,tipo,categoria,descricao,valor,forma_pagamento,origem,origem_id FROM financeiro ORDER BY data DESC,id DESC", ["data", "tipo", "categoria", "descricao", "valor", "forma_pagamento", "origem", "origem_id"])
    elif page == "Despesas": simple_page("🧾 Despesas", "Custos e despesas operacionais.", "despesas", "SELECT id,data,categoria,descricao,valor,forma_pagamento,pago,fornecedor,observacao FROM despesas ORDER BY data DESC,id DESC", ["data", "categoria", "descricao", "valor", "forma_pagamento", "pago", "fornecedor", "observacao"])
    elif page == "Contas a Pagar": simple_page("📤 Contas a Pagar", "Obrigações pendentes e pagas.", "contas_pagar", "SELECT id,descricao,fornecedor,valor_total,valor_pago,vencimento,status,forma_pagamento,origem,origem_id FROM contas_pagar ORDER BY status,vencimento", ["descricao", "fornecedor", "valor_total", "valor_pago", "vencimento", "status", "forma_pagamento"])
    elif page == "Contas a Receber": simple_page("📥 Contas a Receber", "Recebíveis de vendas a prazo ou parcialmente pagas.", "contas_receber", "SELECT id,descricao,cliente,valor_total,valor_recebido,vencimento,status,forma_pagamento,origem,origem_id FROM contas_receber ORDER BY status,vencimento", ["descricao", "cliente", "valor_total", "valor_recebido", "vencimento", "status", "forma_pagamento"])
    elif page == "Entregas": simple_page("🛵 Entregas", "Acompanhamento logístico dos pedidos.", "entregas", "SELECT id,pedido,cliente,endereco,taxa,status,observacao FROM entregas ORDER BY id DESC", ["pedido", "cliente", "endereco", "taxa", "status", "observacao"])
    elif page == "Relatórios": relatorios()
    elif page == "Importar Planilha": importar()
    elif page == "Auditoria": auditoria()
    elif page == "Diagnóstico": diagnostico()
    elif page == "Backup": backup()
