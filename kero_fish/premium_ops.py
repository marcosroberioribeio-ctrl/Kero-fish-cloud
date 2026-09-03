from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd

from .annual import available_years, close_year, closing_info, year_summary
from .professional import safe_backup


def _money(value) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def install_premium_operations(ui) -> None:
    """Acabamento premium e lacunas operacionais da V12.1 sem trocar o núcleo estável."""
    st = ui.st

    def premium_header(title: str, subtitle: str = "") -> None:
        st.markdown("""<style>
        .kf-page-head{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin:2px 0 14px;padding:14px 16px;border:1px solid #214d72;border-radius:14px;background:linear-gradient(135deg,#092642d9,#06192de8);box-shadow:0 10px 28px #0003}
        .kf-page-title{font-size:25px;font-weight:900;letter-spacing:-.025em;color:#f7fbff}.kf-page-sub{font-size:12px;color:#b9d0e3;margin-top:4px}.kf-page-tag{white-space:nowrap;color:#f3c34c;border:1px solid #8d6a20;background:#2a2415;padding:5px 9px;border-radius:999px;font-size:10px;font-weight:800;letter-spacing:.06em}
        .kf-section{margin:8px 0 6px;color:#eef7ff;font-size:15px;font-weight:850}.kf-mini{color:#a9c3d8;font-size:11px}
        [data-testid="stForm"],[data-testid="stExpander"]{border-color:#214d72!important;border-radius:13px!important;background:#061b30cc!important}
        [data-testid="stDataEditor"],[data-testid="stDataFrame"]{box-shadow:0 8px 24px #0002}
        .stTabs [data-baseweb="tab-list"]{gap:5px}.stTabs [data-baseweb="tab"]{border-radius:9px 9px 0 0;padding:7px 12px}.stTabs [aria-selected="true"]{background:#173956;color:#f4c44d}
        </style>""", unsafe_allow_html=True)
        st.markdown(
            f"<div class='kf-page-head'><div><div class='kf-page-title'>{title}</div>"
            f"<div class='kf-page-sub'>{subtitle}</div></div><div class='kf-page-tag'>KERO FISH • PREMIUM</div></div>",
            unsafe_allow_html=True,
        )

    ui.page_header = premium_header

    def premium_grid(table: str, sql: str, editable: list[str], disabled: list[str] | None = None, key: str | None = None) -> None:
        df = ui.query_df(sql)
        if df.empty:
            st.info("Nenhum registro encontrado.")
            return
        grid_key = key or table
        top1, top2 = st.columns([3, 1])
        search = top1.text_input("Pesquisar nesta lista", key=f"search_{grid_key}", placeholder="Digite nome, pedido, produto, status...")
        top2.metric("Registros", len(df))
        view = df
        if search.strip():
            mask = df.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
            view = df.loc[mask].copy()
            st.caption(f"{len(view)} registro(s) encontrado(s).")
        if view.empty:
            st.info("Nenhum registro corresponde à pesquisa.")
            return
        edited = st.data_editor(
            view, use_container_width=True, hide_index=True, num_rows="fixed",
            disabled=(disabled or ["id"]), key=f"premium_{grid_key}", height=430,
        )
        if st.button("💾 Salvar alterações", type="primary", key=f"save_premium_{grid_key}"):
            try:
                n = ui.save_grid(table, view, edited, editable)
                if n:
                    st.success(f"{n} registro(s) atualizado(s) com auditoria.")
                    st.rerun()
                else:
                    st.info("Nenhuma alteração detectada.")
            except Exception as exc:
                st.error(f"Não foi possível salvar: {exc}")

    ui.editable_grid = premium_grid

    def _audit(conn, entity, entity_id, detail):
        conn.execute(
            "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), "CREATE", entity, entity_id, detail),
        )

    def finance_page():
        premium_header("💰 Financeiro", "Entradas e saídas realizadas, com lançamento manual auditável.")
        with st.expander("➕ Novo lançamento manual", expanded=False):
            with st.form("fin_manual_v121"):
                c1, c2, c3 = st.columns(3)
                dt = c1.date_input("Data", date.today())
                tipo = c2.selectbox("Tipo", ["Entrada", "Saída"])
                categoria = c3.text_input("Categoria", "Outros")
                c4, c5 = st.columns([2, 1])
                desc = c4.text_input("Descrição *")
                valor = c5.number_input("Valor", min_value=0.0, step=0.01)
                forma = st.selectbox("Forma de pagamento", ["PIX", "Dinheiro", "Cartão", "Transferência", "Boleto", "Outro"])
                if st.form_submit_button("Registrar lançamento", type="primary"):
                    if not desc.strip() or valor <= 0:
                        st.error("Informe a descrição e um valor maior que zero.")
                    else:
                        with ui.connect() as conn:
                            cur = conn.execute(
                                "INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,categoria) VALUES (?,?,?,?,?,'manual',?)",
                                (dt.isoformat(), desc.strip(), tipo, valor, forma, categoria.strip()),
                            )
                            _audit(conn, "financeiro", cur.lastrowid, f"Lançamento manual {tipo}")
                        st.success("Lançamento registrado.")
                        st.rerun()
        ui.editable_grid("financeiro", "SELECT id,data,tipo,categoria,descricao,valor,forma_pagamento,origem,origem_id FROM financeiro ORDER BY data DESC,id DESC", ["data","tipo","categoria","descricao","valor","forma_pagamento"], ["id","origem","origem_id"], "financeiro_v121")

    def expenses_page():
        premium_header("🧾 Despesas", "Custos operacionais com integração automática ao caixa ou contas a pagar.")
        with st.expander("➕ Nova despesa", expanded=False):
            with st.form("despesa_v121"):
                c1, c2, c3 = st.columns(3)
                dt = c1.date_input("Data", date.today())
                categoria = c2.text_input("Categoria", "Operacional")
                fornecedor = c3.text_input("Fornecedor")
                desc = st.text_input("Descrição *")
                c4, c5, c6 = st.columns(3)
                valor = c4.number_input("Valor", min_value=0.0, step=.01)
                forma = c5.selectbox("Pagamento", ["PIX","Dinheiro","Cartão","Transferência","Boleto","Outro"])
                status = c6.selectbox("Status", ["Pago","Pendente"])
                venc = st.date_input("Vencimento", dt)
                obs = st.text_area("Observações")
                if st.form_submit_button("Registrar despesa", type="primary"):
                    if not desc.strip() or valor <= 0:
                        st.error("Informe descrição e valor maior que zero.")
                    else:
                        with ui.connect() as conn:
                            cur = conn.execute(
                                "INSERT INTO despesas(data_desp,categoria,descricao,valor,pagamento,status,vencimento,observacoes,fornecedor) VALUES (?,?,?,?,?,?,?,?,?)",
                                (dt.isoformat(),categoria.strip(),desc.strip(),valor,forma,status,venc.isoformat(),obs.strip(),fornecedor.strip()),
                            )
                            did = cur.lastrowid
                            if status == "Pago":
                                conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id,categoria) VALUES (?,?,?,?,?,?,?,?)", (dt.isoformat(),desc.strip(),"Saída",valor,forma,"despesa",did,categoria.strip()))
                            else:
                                conn.execute("INSERT INTO contas_pagar(fornecedor,descricao,valor,valor_pago,vencimento,status,origem_tipo,origem_id,forma_pagamento) VALUES (?,?,?,?,?,'Pendente','despesa',?,?)", (fornecedor.strip(),desc.strip(),valor,0,venc.isoformat(),did,forma))
                            _audit(conn,"despesa",did,"Despesa integrada")
                        st.success("Despesa registrada e integrada.")
                        st.rerun()
        ui.editable_grid("despesas", "SELECT id,data,categoria,descricao,valor,forma_pagamento,pago,fornecedor,observacao FROM despesas ORDER BY data DESC,id DESC", ["data","categoria","descricao","valor","forma_pagamento","fornecedor","observacao"], ["id","pago"], "despesas_v121")

    def _open_accounts(table, value_paid_col):
        sql = f"SELECT id,descricao,valor_total AS valor,{value_paid_col} pago,status FROM {table} WHERE status IN ('Pendente','Parcial') ORDER BY vencimento,id"
        try:
            with ui.connect() as conn:
                return pd.read_sql_query(sql, conn)
        except Exception:
            return pd.DataFrame()

    def payables_page():
        premium_header("📤 Contas a Pagar", "Obrigações, vencimentos e baixas financeiras parciais ou totais.")

        with st.expander("➕ Nova conta a pagar", expanded=False):
            with st.form("nova_cp_v121"):
                c1, c2 = st.columns(2)
                desc_new = c1.text_input("Descrição *", placeholder="Ex.: ALUGUEL")
                fornecedor_new = c2.text_input("Fornecedor / favorecido")
                c3, c4, c5 = st.columns(3)
                valor_new = c3.number_input("Valor total", min_value=0.0, step=.01)
                venc_new = c4.date_input("Vencimento", date.today())
                forma_new = c5.selectbox("Forma prevista", ["PIX","Dinheiro","Cartão","Transferência","Boleto","Outro"], key="cp_nova_forma")
                if st.form_submit_button("Cadastrar conta", type="primary"):
                    if not desc_new.strip() or valor_new <= 0:
                        st.error("Informe a descrição e um valor maior que zero.")
                    else:
                        with ui.connect() as conn:
                            cur = conn.execute(
                                "INSERT INTO contas_pagar(fornecedor,descricao,valor,valor_pago,vencimento,status,origem_tipo,forma_pagamento) VALUES (?,?,?,?,?,'Pendente','manual',?)",
                                (fornecedor_new.strip(), desc_new.strip(), valor_new, 0.0, venc_new.isoformat(), forma_new),
                            )
                            _audit(conn, "contas_pagar", cur.lastrowid, "Conta a pagar cadastrada manualmente")
                        st.success("Conta a pagar cadastrada.")
                        st.rerun()

        pending = _open_accounts("contas_pagar", "valor_pago")
        with st.expander("💳 Registrar pagamento", expanded=False):
            if pending.empty:
                st.success("Não há contas pendentes para pagamento.")
            else:
                labels = {int(r.id): f"#{int(r.id)} • {r.descricao} • saldo {_money(float(r.valor)-float(r.pago))}" for r in pending.itertuples()}
                selected = st.selectbox("Conta", list(labels), format_func=lambda x: labels[x], key="cp_baixa_id")
                row = pending[pending.id == selected].iloc[0]
                saldo = max(float(row["valor"]) - float(row["pago"]), 0.0)
                c1, c2, c3 = st.columns(3)
                amount = c1.number_input("Valor pago agora", min_value=0.0, max_value=float(saldo), value=float(saldo), step=.01)
                dt = c2.date_input("Data do pagamento", date.today())
                forma = c3.selectbox("Forma", ["PIX","Dinheiro","Cartão","Transferência","Boleto","Outro"], key="cp_forma")
                if st.button("Confirmar pagamento", type="primary", key="cp_baixar"):
                    if amount <= 0:
                        st.error("Informe um valor maior que zero.")
                    else:
                        novo = float(row["pago"]) + amount
                        status = "Pago" if novo >= float(row["valor"]) - .005 else "Parcial"
                        with ui.connect() as conn:
                            conn.execute("UPDATE contas_pagar SET valor_pago=?,status=?,forma_pagamento=? WHERE id=?", (novo,status,forma,int(selected)))
                            conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id,categoria) VALUES (?,?,?,?,?,'conta_pagar',?,'Pagamento')", (dt.isoformat(),f"Pagamento: {row['descricao']}","Saída",amount,forma,int(selected)))
                            _audit(conn,"contas_pagar",int(selected),f"Baixa {amount:.2f} | {status}")
                        st.success("Pagamento registrado.")
                        st.rerun()
        ui.editable_grid("contas_pagar", "SELECT id,descricao,fornecedor,valor_total,valor_pago,vencimento,status,forma_pagamento,origem,origem_id FROM contas_pagar ORDER BY status,vencimento", ["descricao","fornecedor","valor_total","vencimento","forma_pagamento"], ["id","valor_pago","status","origem","origem_id"], "cp_v121")

    def receivables_page():
        premium_header("📥 Contas a Receber", "Recebíveis com baixa parcial ou total e integração automática ao caixa.")
        pending = _open_accounts("contas_receber", "valor_recebido")
        with st.expander("💵 Registrar recebimento", expanded=False):
            if pending.empty:
                st.success("Não há contas pendentes para recebimento.")
            else:
                labels = {int(r.id): f"#{int(r.id)} • {r.descricao} • saldo {_money(float(r.valor)-float(r.pago))}" for r in pending.itertuples()}
                selected = st.selectbox("Conta", list(labels), format_func=lambda x: labels[x], key="cr_baixa_id")
                row = pending[pending.id == selected].iloc[0]
                saldo = max(float(row["valor"]) - float(row["pago"]), 0.0)
                c1, c2, c3 = st.columns(3)
                amount = c1.number_input("Valor recebido agora", min_value=0.0, max_value=float(saldo), value=float(saldo), step=.01)
                dt = c2.date_input("Data do recebimento", date.today())
                forma = c3.selectbox("Forma", ["PIX","Dinheiro","Cartão","Transferência","Boleto","Outro"], key="cr_forma")
                if st.button("Confirmar recebimento", type="primary", key="cr_baixar"):
                    if amount <= 0:
                        st.error("Informe um valor maior que zero.")
                    else:
                        novo = float(row["pago"]) + amount
                        status = "Pago" if novo >= float(row["valor"]) - .005 else "Parcial"
                        with ui.connect() as conn:
                            conn.execute("UPDATE contas_receber SET valor_recebido=?,status=?,forma_pagamento=? WHERE id=?", (novo,status,forma,int(selected)))
                            conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id,categoria) VALUES (?,?,?,?,?,'conta_receber',?,'Recebimento')", (dt.isoformat(),f"Recebimento: {row['descricao']}","Entrada",amount,forma,int(selected)))
                            _audit(conn,"contas_receber",int(selected),f"Baixa {amount:.2f} | {status}")
                        st.success("Recebimento registrado.")
                        st.rerun()
        ui.editable_grid("contas_receber", "SELECT id,descricao,cliente,valor_total,valor_recebido,vencimento,status,forma_pagamento,origem,origem_id FROM contas_receber ORDER BY status,vencimento", ["descricao","cliente","valor_total","vencimento","forma_pagamento"], ["id","valor_recebido","status","origem","origem_id"], "cr_v121")

    original_simple = ui.simple_page
    def premium_simple(title, subtitle, table, sql, editable):
        if table == "financeiro": return finance_page()
        if table == "despesas": return expenses_page()
        if table == "contas_pagar": return payables_page()
        if table == "contas_receber": return receivables_page()
        return original_simple(title, subtitle, table, sql, editable)
    ui.simple_page = premium_simple

    original_products = ui.produtos
    def products_plus():
        original_products()
        try:
            with ui.connect() as conn:
                df = pd.read_sql_query("SELECT nome,categoria,custo_medio,preco_venda FROM produtos WHERE ativo=1 ORDER BY nome", conn)
            if not df.empty:
                df["Margem R$"] = (pd.to_numeric(df.preco_venda)-pd.to_numeric(df.custo_medio)).map(_money)
                base = pd.to_numeric(df.preco_venda).replace(0, pd.NA)
                df["Margem %"] = (((pd.to_numeric(df.preco_venda)-pd.to_numeric(df.custo_medio))/base)*100).fillna(0).map(lambda x: f"{x:.1f}%".replace(".",","))
                df["Custo"] = df.custo_medio.map(_money); df["Venda"] = df.preco_venda.map(_money)
                st.markdown("<div class='kf-section'>Análise de margem</div>", unsafe_allow_html=True)
                st.dataframe(df[["nome","categoria","Custo","Venda","Margem R$","Margem %"]], use_container_width=True, hide_index=True)
        except Exception:
            pass
    ui.produtos = products_plus

    original_stock = ui.estoque
    def stock_plus():
        try:
            sdf = ui.stock_df()
            total = len(sdf); low = int((sdf.get("Situacao") == "BAIXO").sum()) if not sdf.empty else 0; neg = int((sdf.get("Situacao") == "NEGATIVO").sum()) if not sdf.empty else 0
            c1,c2,c3 = st.columns(3); c1.metric("Produtos monitorados",total); c2.metric("Estoque baixo",low); c3.metric("Estoque negativo",neg)
        except Exception:
            pass
        original_stock()
        try:
            with ui.connect() as conn:
                lots = pd.read_sql_query("SELECT produto,lote,validade,qtd FROM compras WHERE COALESCE(validade,'')<>'' ORDER BY validade", conn)
            if not lots.empty:
                lots["dt"] = pd.to_datetime(lots["validade"], errors="coerce", dayfirst=True)
                limit = pd.Timestamp(date.today()+timedelta(days=30))
                near = lots[(lots.dt.notna()) & (lots.dt <= limit)].copy()
                if not near.empty:
                    near["validade"] = near.dt.dt.strftime("%d/%m/%Y")
                    st.warning("Há lotes vencidos ou com validade nos próximos 30 dias.")
                    st.dataframe(near[["produto","lote","validade","qtd"]], use_container_width=True, hide_index=True)
        except Exception:
            pass
    ui.estoque = stock_plus

    def reports_plus():
        premium_header("📈 Relatórios", "Análise gerencial mensal ou anual, preservando o histórico contínuo e o fechamento do exercício.")

        nomes_meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        f1, f2, f3 = st.columns([1, 1, 1])
        periodo = f1.selectbox("Período", ["Mensal", "Anual"], key="rel_periodo_v121")
        years = available_years()
        year = int(f2.selectbox("Ano", years, key="rel_ano_v121"))
        month = None
        if periodo == "Mensal":
            month = int(f3.selectbox("Mês", list(range(1, 13)), index=date.today().month - 1, format_func=lambda m: nomes_meses[m-1], key="rel_mes_v121"))
            start_date = date(year, month, 1)
            next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
            end_date = next_month - timedelta(days=1)
            periodo_label = f"{nomes_meses[month-1]}/{year}"
        else:
            f3.markdown("<div class='kf-mini' style='padding-top:29px'>Janeiro a Dezembro</div>", unsafe_allow_html=True)
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            periodo_label = str(year)

        start, end = start_date.isoformat(), end_date.isoformat()

        def scalar(sql, params):
            try:
                with ui.connect() as conn:
                    row = conn.execute(sql, params).fetchone()
                    return float((row[0] if row else 0) or 0)
            except Exception:
                return 0.0

        vendas_total = scalar("SELECT COALESCE(SUM(total),0) FROM vendas WHERE data BETWEEN ? AND ? AND upper(COALESCE(status_pedido,''))<>'CANCELADO'", (start, end))
        compras_total = scalar("SELECT COALESCE(SUM(total),0) FROM compras WHERE data BETWEEN ? AND ?", (start, end))
        entradas_total = scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE data BETWEEN ? AND ? AND upper(tipo)='ENTRADA'", (start, end))
        saidas_total = scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE data BETWEEN ? AND ? AND upper(tipo) IN ('SAÍDA','SAIDA')", (start, end))
        saldo_total = entradas_total - saidas_total
        receber_aberto = scalar("SELECT COALESCE(SUM(valor_total-valor_recebido),0) FROM contas_receber WHERE vencimento BETWEEN ? AND ? AND status IN ('Pendente','Parcial')", (start, end))
        pagar_aberto = scalar("SELECT COALESCE(SUM(valor_total-valor_pago),0) FROM contas_pagar WHERE vencimento BETWEEN ? AND ? AND status IN ('Pendente','Parcial')", (start, end))

        st.caption(f"Período selecionado: {periodo_label}")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Vendas", _money(vendas_total)); c2.metric("Compras", _money(compras_total)); c3.metric("Entradas", _money(entradas_total)); c4.metric("Saídas", _money(saidas_total))
        c5,c6,c7 = st.columns(3)
        c5.metric("Saldo", _money(saldo_total)); c6.metric("Contas a receber", _money(receber_aberto)); c7.metric("Contas a pagar", _money(pagar_aberto))

        tabs = st.tabs(["Vendas por produto","Compras por fornecedor","Fluxo financeiro","Resumo do período"])
        with tabs[0]:
            st.dataframe(ui.query_df("SELECT produto,COUNT(*) pedidos,SUM(quantidade) quantidade,SUM(total) faturamento FROM vendas WHERE data BETWEEN ? AND ? AND upper(COALESCE(status_pedido,''))<>'CANCELADO' GROUP BY produto ORDER BY SUM(total) DESC", (start,end)), use_container_width=True, hide_index=True)
        with tabs[1]:
            st.dataframe(ui.query_df("SELECT fornecedor,COUNT(*) compras,SUM(quantidade) quantidade,SUM(total) total_comprado FROM compras WHERE data BETWEEN ? AND ? GROUP BY fornecedor ORDER BY SUM(total) DESC", (start,end)), use_container_width=True, hide_index=True)
        with tabs[2]:
            st.dataframe(ui.query_df("SELECT tipo,categoria,SUM(valor) valor FROM financeiro WHERE data BETWEEN ? AND ? GROUP BY tipo,categoria ORDER BY tipo,categoria", (start,end)), use_container_width=True, hide_index=True)
        with tabs[3]:
            st.write(f"Saldo realizado no período: **{_money(saldo_total)}**")
            st.write(f"Contas em aberto com vencimento no período: receber **{_money(receber_aberto)}** • pagar **{_money(pagar_aberto)}**")
            if periodo == "Anual":
                info = closing_info(year)
                if info:
                    st.success(f"Exercício {year} fechado em {info['fechado_em'].replace('T',' ')}. O histórico permanece disponível para consulta.")
                else:
                    st.info("Fechar o exercício cria um snapshot gerencial; nenhum registro é apagado e o estoque continua para o ano seguinte.")
                    notes = st.text_area("Observações do fechamento", key=f"close_notes_{year}")
                    confirm = st.checkbox(f"Confirmo o fechamento do exercício {year}.", key=f"close_confirm_{year}")
                    if st.button("🔒 Fechar exercício", disabled=not confirm, key=f"close_year_{year}"):
                        try:
                            safe_backup(f"pre_fechamento_{year}")
                            close_year(year, notes)
                            st.success(f"Exercício {year} fechado com backup de segurança.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
            else:
                st.info("No modo mensal, os indicadores e tabelas consideram somente o mês selecionado. O fechamento do exercício permanece disponível no modo Anual.")
    ui.relatorios = reports_plus