from __future__ import annotations

import hashlib
from datetime import date, datetime

import pandas as pd


def _actor(ui) -> str:
    return str(ui.st.session_state.get("auth_username", "system") or "system")


def _audit(ui, action: str, entity_type: str, entity_id=None, detail: str = "") -> None:
    with ui.connect() as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(audit_log)")}
        if "username" in cols:
            conn.execute(
                "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail,username) VALUES (?,?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), action, entity_type, entity_id, detail[:2000], _actor(ui)),
            )
        else:
            conn.execute(
                "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), action, entity_type, entity_id, detail[:2000]),
            )


def ensure_analyst_schema(ui) -> None:
    with ui.connect() as conn:
        desp_cols = {row[1] for row in conn.execute("PRAGMA table_info(despesas)")}
        if "tipo_custo" not in desp_cols:
            conn.execute("ALTER TABLE despesas ADD COLUMN tipo_custo TEXT DEFAULT 'Não classificado'")

        # Sincronização operacional entre origem e módulos derivados.
        conn.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS trg_cp_status_compra_au
            AFTER UPDATE OF valor_pago,status ON contas_pagar
            WHEN lower(COALESCE(NEW.origem_tipo,''))='compra' AND NEW.origem_id IS NOT NULL
            BEGIN
              UPDATE compras SET status_pagamento=NEW.status WHERE id=NEW.origem_id;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_cp_status_despesa_au
            AFTER UPDATE OF valor_pago,status ON contas_pagar
            WHEN lower(COALESCE(NEW.origem_tipo,''))='despesa' AND NEW.origem_id IS NOT NULL
            BEGIN
              UPDATE despesas SET status=NEW.status,pago=CASE WHEN NEW.status='Pago' THEN 1 ELSE 0 END WHERE id=NEW.origem_id;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_cr_status_venda_au
            AFTER UPDATE OF valor_recebido,status ON contas_receber
            WHEN lower(COALESCE(NEW.origem_tipo,''))='venda' AND NEW.origem_id IS NOT NULL
            BEGIN
              UPDATE vendas SET valor_recebido=NEW.valor_recebido,status_pagamento=NEW.status WHERE id=NEW.origem_id;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_entrega_status_venda_au
            AFTER UPDATE OF status ON entregas
            WHEN NEW.origem_id IS NOT NULL
            BEGIN
              UPDATE vendas SET status_pedido=NEW.status WHERE id=NEW.origem_id;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_venda_status_entrega_au
            AFTER UPDATE OF status_pedido ON vendas
            BEGIN
              UPDATE entregas SET status=NEW.status_pedido WHERE origem_id=NEW.id;
            END;
            """
        )

        # Exercícios fechados ficam imutáveis até reabertura administrativa.
        conn.executescript(
            """
            CREATE TRIGGER IF NOT EXISTS trg_lock_vendas_bu BEFORE UPDATE ON vendas
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(OLD.data_venda,''),OLD.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de alterar a venda.'); END;
            CREATE TRIGGER IF NOT EXISTS trg_lock_vendas_bd BEFORE DELETE ON vendas
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(OLD.data_venda,''),OLD.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: venda protegida.'); END;
            CREATE TRIGGER IF NOT EXISTS trg_lock_vendas_bi BEFORE INSERT ON vendas
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(NEW.data_venda,''),NEW.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de lançar venda.'); END;

            CREATE TRIGGER IF NOT EXISTS trg_lock_compras_bu BEFORE UPDATE ON compras
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(OLD.data_compra,''),OLD.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de alterar a compra.'); END;
            CREATE TRIGGER IF NOT EXISTS trg_lock_compras_bd BEFORE DELETE ON compras
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(OLD.data_compra,''),OLD.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: compra protegida.'); END;
            CREATE TRIGGER IF NOT EXISTS trg_lock_compras_bi BEFORE INSERT ON compras
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(NEW.data_compra,''),NEW.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de lançar compra.'); END;

            CREATE TRIGGER IF NOT EXISTS trg_lock_despesas_bu BEFORE UPDATE ON despesas
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(OLD.data_desp,''),OLD.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de alterar a despesa.'); END;
            CREATE TRIGGER IF NOT EXISTS trg_lock_despesas_bd BEFORE DELETE ON despesas
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(OLD.data_desp,''),OLD.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: despesa protegida.'); END;
            CREATE TRIGGER IF NOT EXISTS trg_lock_despesas_bi BEFORE INSERT ON despesas
            WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr(COALESCE(NULLIF(NEW.data_desp,''),NEW.data),1,4) AS INTEGER))
            BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de lançar despesa.'); END;
            """
        )


def _stock_df(ui):
    return ui.query_df(
        """
        SELECT p.nome AS Produto,p.categoria AS Categoria,p.unidade AS Unidade,
               ROUND(COALESCE(c.compras,0),3) AS Compras,
               ROUND(COALESCE(v.vendas,0),3) AS Vendas,
               ROUND(COALESCE(a.ajustes,0),3) AS Ajustes,
               ROUND(COALESCE(c.compras,0)-COALESCE(v.vendas,0)+COALESCE(a.ajustes,0),3) AS Estoque,
               p.estoque_minimo AS Minimo,
               CASE WHEN COALESCE(c.compras,0)-COALESCE(v.vendas,0)+COALESCE(a.ajustes,0)<0 THEN 'NEGATIVO'
                    WHEN COALESCE(c.compras,0)-COALESCE(v.vendas,0)+COALESCE(a.ajustes,0)<=p.estoque_minimo THEN 'BAIXO'
                    ELSE 'OK' END AS Situacao,
               p.custo_medio AS Custo_medio,p.preco_venda AS Preco_venda
        FROM produtos p
        LEFT JOIN (SELECT produto,SUM(qtd) compras FROM compras GROUP BY produto)c ON lower(c.produto)=lower(p.nome)
        LEFT JOIN (SELECT produto,SUM(qtd_kg) vendas FROM vendas WHERE upper(COALESCE(status_pedido,''))<>'CANCELADO' GROUP BY produto)v ON lower(v.produto)=lower(p.nome)
        LEFT JOIN (
            SELECT produto,SUM(COALESCE(quantidade,0)) ajustes
            FROM movimentos_estoque
            WHERE lower(COALESCE(origem_tipo,origem,'')) IN ('manual','ajuste')
               OR upper(COALESCE(tipo,'')) IN ('AJUSTE_ENTRADA','AJUSTE ENTRADA','AJUSTE_SAIDA','AJUSTE SAÍDA','AJUSTE SAIDA','PERDA')
            GROUP BY produto
        )a ON lower(a.produto)=lower(p.nome)
        WHERE p.ativo=1 ORDER BY p.nome
        """
    )


def _dashboard_metrics(ui):
    ym = date.today().strftime("%Y-%m")
    with ui.connect() as conn:
        def scalar(sql, params=(), default=0):
            row = conn.execute(sql, tuple(params)).fetchone()
            return row[0] if row and row[0] is not None else default

        entradas = float(scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Entrada' AND substr(COALESCE(NULLIF(data_mov,''),data),1,7)=?", (ym,)))
        saidas = float(scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Saída' AND substr(COALESCE(NULLIF(data_mov,''),data),1,7)=?", (ym,)))
        receber = float(scalar("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_recebido,0),0)),0) FROM contas_receber WHERE status IN ('Pendente','Parcial')"))
        pagar = float(scalar("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_pago,0),0)),0) FROM contas_pagar WHERE status IN ('Pendente','Parcial')"))
        vendas = float(scalar("SELECT COALESCE(SUM(valor_total),0) FROM vendas"))
        compras = float(scalar("SELECT COALESCE(SUM(valor_total),0) FROM compras"))
        qtd_vendas = int(scalar("SELECT COUNT(*) FROM vendas"))
        qtd_compras = int(scalar("SELECT COUNT(*) FROM compras"))
    return {"entradas":entradas,"saidas":saidas,"saldo":entradas-saidas,"receber":receber,"pagar":pagar,"vendas":vendas,"compras":compras,"qtd_vendas":qtd_vendas,"qtd_compras":qtd_compras}


def _date_to_iso(value) -> str:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return ""
    text = str(value).strip()[:10]
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return text


def _number(value) -> float:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("R$", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    return float(text or 0)


def _is_closed(conn, value) -> bool:
    iso = _date_to_iso(value)
    if len(iso) < 4 or not iso[:4].isdigit():
        return False
    return bool(conn.execute("SELECT 1 FROM annual_closings WHERE ano=?", (int(iso[:4]),)).fetchone())


def _reconcile_sale(conn, rid: int) -> None:
    row = conn.execute("SELECT * FROM vendas WHERE id=?", (rid,)).fetchone()
    if not row:
        return
    qty = float(row["qtd_kg"] or 0); price = float(row["preco_kg"] or 0); discount = float(row["desconto"] or 0)
    total = max(0.0, qty * price - discount)
    direct_received = min(max(float(row["valor_recebido"] or 0), 0.0), total)
    cr = conn.execute("SELECT id,valor_recebido FROM contas_receber WHERE lower(origem_tipo)='venda' AND origem_id=? ORDER BY id LIMIT 1", (rid,)).fetchone()
    cumulative = max(direct_received, float(cr["valor_recebido"] or 0) if cr else 0.0)
    cumulative = min(cumulative, total)
    status = "Pago" if total > 0 and cumulative >= total - .005 else ("Parcial" if cumulative > 0 else "Pendente")
    conn.execute("UPDATE vendas SET valor_total=?,total=?,valor_recebido=?,status_pagamento=? WHERE id=?", (total,total,cumulative,status,rid))

    # O recebimento inicial ligado diretamente à venda é mantido sem duplicidade.
    base = conn.execute("SELECT id FROM financeiro WHERE lower(origem_tipo)='venda' AND origem_id=? ORDER BY id LIMIT 1", (rid,)).fetchone()
    if direct_received > 0:
        values = (row["data_venda"] or row["data"], f"Venda {row['pedido']} - recebimento", "Entrada", direct_received, row["forma_pagamento"], "venda", rid, "Venda")
        if base:
            conn.execute("UPDATE financeiro SET data_mov=?,descricao=?,tipo=?,valor=?,forma_pagamento=?,origem_tipo=?,origem_id=?,categoria=? WHERE id=?", (*values, base["id"]))
        else:
            conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id,categoria) VALUES (?,?,?,?,?,?,?,?)", values)
    elif base:
        conn.execute("DELETE FROM financeiro WHERE id=?", (base["id"],))

    if total - cumulative > .005:
        if cr:
            conn.execute("UPDATE contas_receber SET cliente=?,descricao=?,valor=?,valor_total=?,valor_recebido=?,vencimento=?,status=?,forma_pagamento=? WHERE id=?", (row["cliente"],f"Venda {row['pedido']}",total,total,cumulative,row["vencimento"] or row["data_venda"],status,row["forma_pagamento"],cr["id"]))
        else:
            conn.execute("INSERT INTO contas_receber(cliente,descricao,valor,valor_total,valor_recebido,vencimento,status,origem_tipo,origem_id,forma_pagamento) VALUES (?,?,?,?,?,?,?,'venda',?,?)", (row["cliente"],f"Venda {row['pedido']}",total,total,cumulative,row["vencimento"] or row["data_venda"],status,rid,row["forma_pagamento"]))
    elif cr:
        conn.execute("UPDATE contas_receber SET valor=?,valor_total=?,valor_recebido=?,status='Pago' WHERE id=?", (total,total,total,cr["id"]))


def _reconcile_purchase(conn, rid: int) -> None:
    row = conn.execute("SELECT * FROM compras WHERE id=?", (rid,)).fetchone()
    if not row:
        return
    total = max(0.0, float(row["qtd"] or 0) * float(row["preco_kg"] or 0))
    cp = conn.execute("SELECT id,valor_pago,status FROM contas_pagar WHERE lower(origem_tipo)='compra' AND origem_id=? ORDER BY id LIMIT 1", (rid,)).fetchone()
    paid = min(float(cp["valor_pago"] or 0), total) if cp else (total if row["status_pagamento"] == "Pago" else 0.0)
    status = "Pago" if total > 0 and paid >= total - .005 else ("Parcial" if paid > 0 else "Pendente")
    conn.execute("UPDATE compras SET valor_total=?,total=?,status_pagamento=? WHERE id=?", (total,total,status,rid))
    base = conn.execute("SELECT id FROM financeiro WHERE lower(origem_tipo)='compra' AND origem_id=? ORDER BY id LIMIT 1", (rid,)).fetchone()
    if status == "Pago":
        values = (row["data_compra"] or row["data"], f"Compra #{rid}: {row['produto']}", "Saída", total, row["forma_pagamento"], "compra", rid, "Compra")
        if base:
            conn.execute("UPDATE financeiro SET data_mov=?,descricao=?,tipo=?,valor=?,forma_pagamento=?,origem_tipo=?,origem_id=?,categoria=? WHERE id=?", (*values, base["id"]))
        else:
            conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id,categoria) VALUES (?,?,?,?,?,?,?,?)", values)
    elif base:
        conn.execute("DELETE FROM financeiro WHERE id=?", (base["id"],))
    if status != "Pago":
        if cp:
            conn.execute("UPDATE contas_pagar SET fornecedor=?,descricao=?,valor=?,valor_total=?,valor_pago=?,vencimento=?,status=?,forma_pagamento=? WHERE id=?", (row["fornecedor"],f"Compra #{rid}: {row['produto']}",total,total,paid,row["vencimento"] or row["data_compra"],status,row["forma_pagamento"],cp["id"]))
        else:
            conn.execute("INSERT INTO contas_pagar(fornecedor,descricao,valor,valor_total,valor_pago,vencimento,status,origem_tipo,origem_id,forma_pagamento) VALUES (?,?,?,?,?,?,?,'compra',?,?)", (row["fornecedor"],f"Compra #{rid}: {row['produto']}",total,total,0,row["vencimento"] or row["data_compra"],"Pendente",rid,row["forma_pagamento"]))
    elif cp:
        conn.execute("UPDATE contas_pagar SET valor=?,valor_total=?,valor_pago=?,status='Pago' WHERE id=?", (total,total,total,cp["id"]))


def _save_grid_integrated(ui, table, original, edited, editable):
    if original.empty or edited.empty:
        return 0
    original_idx = original.set_index("id", drop=False)
    changed_ids = []
    date_candidates = {"vendas":["data","data_venda"],"compras":["data","data_compra"],"despesas":["data","data_desp"]}
    with ui.connect() as conn:
        for _, row in edited.iterrows():
            rid = int(row["id"])
            if rid not in original_idx.index:
                continue
            old = original_idx.loc[rid]
            if not any(str(row.get(c,"")) != str(old.get(c,"")) for c in editable if c in row.index):
                continue
            for dcol in date_candidates.get(table, []):
                if dcol in old.index and _is_closed(conn, old.get(dcol)):
                    raise ValueError("Este registro pertence a um exercício fechado. Reabra o exercício antes de editar.")
            if table == "contas_pagar" and float(_number(old.get("valor_pago",0))) > 0 and any(c in editable for c in ["valor","valor_total"]):
                if any(str(row.get(c,"")) != str(old.get(c,"")) for c in ["valor","valor_total"] if c in row.index):
                    raise ValueError("Conta a pagar com baixa registrada não permite alterar o valor principal. Estorne/revise a baixa primeiro.")
            if table == "contas_receber" and float(_number(old.get("valor_recebido",0))) > 0 and any(c in editable for c in ["valor","valor_total"]):
                if any(str(row.get(c,"")) != str(old.get(c,"")) for c in ["valor","valor_total"] if c in row.index):
                    raise ValueError("Conta a receber com recebimento registrado não permite alterar o valor principal.")
            changed_ids.append(rid)

    count = ui._original_save_grid_analyst(table, original, edited, editable)
    if not count:
        return count
    with ui.connect() as conn:
        for rid in changed_ids:
            if table == "vendas":
                _reconcile_sale(conn, rid)
            elif table == "compras":
                _reconcile_purchase(conn, rid)
    for rid in changed_ids:
        _audit(ui, "INTEGRATED_UPDATE", table, rid, "Edição reconciliada entre módulos")
    return count


def _enhance_expenses(ui, original_simple):
    def wrapped(title, subtitle, table, sql, editable):
        result = original_simple(title, subtitle, table, sql, editable)
        if table != "despesas":
            return result
        st = ui.st
        st.markdown("### 🧮 Classificação gerencial de custos")
        st.caption("Classifique as despesas para que o ponto de equilíbrio seja calculado automaticamente com maior precisão.")
        with ui.connect() as conn:
            df = pd.read_sql_query("SELECT id,data,descricao,valor,tipo_custo FROM despesas ORDER BY data DESC,id DESC", conn)
        if df.empty:
            st.info("Ainda não há despesas para classificar.")
            return result
        edited = st.data_editor(
            df,
            hide_index=True,
            use_container_width=True,
            disabled=["id","data","descricao","valor"],
            column_config={"tipo_custo": st.column_config.SelectboxColumn("Tipo de custo", options=["Fixo","Variável","Não classificado"])},
            key="despesas_tipo_custo_v121",
        )
        if st.button("Salvar classificação de custos", type="primary", key="save_tipo_custo_v121"):
            changed = 0
            with ui.connect() as conn:
                for _, row in edited.iterrows():
                    rid = int(row["id"]); value = str(row.get("tipo_custo") or "Não classificado")
                    old = df.loc[df.id == rid, "tipo_custo"].iloc[0]
                    if value != old:
                        conn.execute("UPDATE despesas SET tipo_custo=? WHERE id=?", (value, rid)); changed += 1
            if changed:
                _audit(ui, "COST_CLASSIFICATION", "despesas", None, f"{changed} despesa(s) classificadas")
                st.success(f"{changed} despesa(s) atualizada(s).")
                st.rerun()
            else:
                st.info("Nenhuma alteração detectada.")
        return result
    return wrapped


def _install_reports_admin(ui) -> None:
    original = ui.relatorios
    def reports_plus_admin():
        original()
        if ui.st.session_state.get("auth_role") != "ADMIN_TOTAL":
            return
        with ui.connect() as conn:
            closed = conn.execute("SELECT ano,fechado_em FROM annual_closings ORDER BY ano DESC").fetchall()
        if not closed:
            return
        ui.st.markdown("### 🔓 Administração de exercícios fechados")
        ui.st.caption("Reabrir um exercício volta a permitir lançamentos e correções naquele ano e fica registrado na auditoria.")
        labels = {int(r["ano"]): f"{r['ano']} • fechado em {str(r['fechado_em']).replace('T',' ')}" for r in closed}
        year = ui.st.selectbox("Exercício fechado", list(labels), format_func=lambda x: labels[x], key="reopen_year_select")
        confirm = ui.st.checkbox(f"Confirmo a reabertura do exercício {year}.", key="reopen_year_confirm")
        if ui.st.button("🔓 Reabrir exercício", disabled=not confirm, key="reopen_year_btn"):
            from .professional import safe_backup
            safe_backup(f"pre_reabertura_{year}")
            with ui.connect() as conn:
                conn.execute("DELETE FROM annual_closings WHERE ano=?", (int(year),))
            _audit(ui, "YEAR_REOPEN", "exercicio", int(year), f"Exercício {year} reaberto")
            ui.st.success(f"Exercício {year} reaberto com backup de segurança.")
            ui.st.rerun()
    ui.relatorios = reports_plus_admin


def _enhanced_importer(ui):
    original_import = ui.import_excel
    def enhanced(path, create_backup=True):
        report = original_import(path, create_backup=create_backup)
        try:
            xls = pd.ExcelFile(path)
            sheet = next((s for s in xls.sheet_names if str(s).strip().lower().replace("_"," ") == "entregas"), None)
            if not sheet:
                return report
            df = pd.read_excel(xls, sheet_name=sheet).dropna(axis=1, how="all")
            if df.empty:
                return report
            cols = {str(c).strip().lower(): c for c in df.columns}
            def get(row, *names):
                for name in names:
                    hit = cols.get(name.lower())
                    if hit is not None:
                        value = row.get(hit, "")
                        return "" if pd.isna(value) else value
                return ""
            with ui.connect() as conn:
                for idx, row in df.iterrows():
                    pedido = str(get(row,"pedido","número pedido","numero pedido")).strip()
                    cliente = str(get(row,"cliente")).strip()
                    data_ent = _date_to_iso(get(row,"data","data entrega"))
                    endereco = str(get(row,"endereço","endereco")).strip()
                    bairro = str(get(row,"bairro")).strip()
                    cidade = str(get(row,"cidade")).strip()
                    entregador = str(get(row,"entregador")).strip()
                    status = str(get(row,"status")).strip() or "Aguardando"
                    try: taxa = _number(get(row,"taxa","taxa entrega","taxa de entrega"))
                    except Exception: taxa = 0.0
                    raw = f"{path}|{sheet}|{idx}|{pedido}|{cliente}|{data_ent}|{endereco}|{taxa}"
                    key = hashlib.sha1(raw.encode("utf-8")).hexdigest()
                    if conn.execute("SELECT 1 FROM import_log WHERE source_key=? AND entity_type='entrega'", (key,)).fetchone():
                        report.skipped += 1; continue
                    origin = conn.execute("SELECT id FROM vendas WHERE pedido=?", (pedido,)).fetchone() if pedido else None
                    cur = conn.execute("INSERT INTO entregas(pedido,cliente,data_ent,endereco,bairro,cidade,entregador,taxa_entrega,taxa,status,origem_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (pedido,cliente,data_ent,endereco,bairro,cidade,entregador,taxa,taxa,status,origin["id"] if origin else None))
                    conn.execute("INSERT INTO import_log(source_file,source_sheet,source_key,entity_type,entity_id,imported_at) VALUES (?,?,?,?,?,?)", (str(path).split('/')[-1],sheet,key,"entrega",cur.lastrowid,datetime.now().isoformat(timespec="seconds")))
                    report.inserted["entregas"] = report.inserted.get("entregas",0) + 1
        except Exception as exc:
            report.warnings.append(f"Entregas: {exc}")
        return report
    ui.import_excel = enhanced


def install_analyst_layer(ui) -> None:
    ensure_analyst_schema(ui)

    # Corrige estoque e indicadores do mês sem alterar os dados históricos.
    ui.stock_df = lambda: _stock_df(ui)
    ui.dashboard_metrics = lambda: _dashboard_metrics(ui)
    try:
        from . import services
        services.stock_df = ui.stock_df
        services.dashboard_metrics = ui.dashboard_metrics
    except Exception:
        pass

    # Edição integrada e auditável.
    if not hasattr(ui, "_original_save_grid_analyst"):
        ui._original_save_grid_analyst = ui.save_grid
    ui.save_grid = lambda table, original, edited, editable: _save_grid_integrated(ui, table, original, edited, editable)

    # Classificação de custos e importação completa de entregas.
    ui.simple_page = _enhance_expenses(ui, ui.simple_page)
    _enhanced_importer(ui)
    _install_reports_admin(ui)

    # Auditoria passa a exibir o usuário responsável quando disponível.
    def recent_audit_plus(limit=500):
        limit = max(1, min(int(limit), 5000))
        with ui.connect() as conn:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(audit_log)")}
            user_expr = "username" if "username" in cols else "'' AS username"
            return pd.read_sql_query(f"SELECT id,event_time,{user_expr},action,entity_type,entity_id,detail FROM audit_log ORDER BY id DESC LIMIT {limit}", conn)
    ui.recent_audit = recent_audit_plus
