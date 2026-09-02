from __future__ import annotations

import json
from datetime import date, datetime

import pandas as pd

from .annual import next_order_number


STATUSES = ("NOVO", "CONFIRMADO", "CANCELADO", "ERRO")


def ensure_online_orders_schema(ui) -> None:
    with ui.connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pedidos_online (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                criado_em TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'NOVO',
                cliente_nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                cep TEXT,
                endereco TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                observacoes TEXT,
                forma_pagamento TEXT NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                taxa_entrega REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                itens_json TEXT NOT NULL,
                origem TEXT NOT NULL DEFAULT 'LOJA_PWA'
            )
            """
        )
        cols = {row[1] for row in conn.execute("PRAGMA table_info(pedidos_online)")}
        additions = {
            "processado_em": "TEXT DEFAULT ''",
            "processado_por": "TEXT DEFAULT ''",
            "vendas_ids_json": "TEXT DEFAULT '[]'",
            "erro_processamento": "TEXT DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in cols:
                conn.execute(f"ALTER TABLE pedidos_online ADD COLUMN {name} {definition}")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_online_status ON pedidos_online(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_online_criado ON pedidos_online(criado_em)")


def _items(row) -> list[dict]:
    try:
        data = json.loads(row["itens_json"] or "[]")
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _stock_available(conn, product_name: str) -> float:
    bought = conn.execute(
        "SELECT COALESCE(SUM(qtd),0) FROM compras WHERE produto=?", (product_name,)
    ).fetchone()[0] or 0
    sold = conn.execute(
        "SELECT COALESCE(SUM(qtd_kg),0) FROM vendas WHERE produto=? AND UPPER(COALESCE(status_pedido,'')) NOT IN ('CANCELADO','CANCELADA')",
        (product_name,),
    ).fetchone()[0] or 0
    adjustment = conn.execute(
        """
        SELECT COALESCE(SUM(
            CASE
                WHEN UPPER(tipo) IN ('AJUSTE ENTRADA','AJUSTE_ENTRADA','ENTRADA') THEN quantidade
                WHEN UPPER(tipo) IN ('AJUSTE SAÍDA','AJUSTE SAIDA','AJUSTE_SAIDA','PERDA','SAÍDA','SAIDA') THEN -quantidade
                ELSE 0
            END
        ),0)
        FROM movimentos_estoque WHERE produto=? AND LOWER(COALESCE(origem_tipo,''))='manual'
        """,
        (product_name,),
    ).fetchone()[0] or 0
    return float(bought) - float(sold) + float(adjustment)


def _payment_label(code: str) -> str:
    return {
        "PIX": "Pix",
        "DINHEIRO": "Dinheiro",
        "CARTAO_ENTREGA": "Cartão na entrega",
    }.get(str(code or "").upper(), str(code or "Outro"))


def _upsert_customer(conn, row, today: str) -> int:
    phone = str(row["telefone"] or "").strip()
    name = str(row["cliente_nome"] or "").strip()
    found = None
    if phone:
        found = conn.execute("SELECT id FROM clientes WHERE telefone=? ORDER BY id LIMIT 1", (phone,)).fetchone()
    if not found:
        found = conn.execute("SELECT id FROM clientes WHERE LOWER(nome)=LOWER(?) ORDER BY id LIMIT 1", (name,)).fetchone()

    full_address = ", ".join(x for x in [str(row["endereco"] or "").strip(), str(row["numero"] or "").strip(), str(row["complemento"] or "").strip(), str(row["bairro"] or "").strip()] if x)
    if found:
        cid = int(found[0])
        conn.execute(
            "UPDATE clientes SET telefone=?,cidade=?,endereco=?,ativo=1 WHERE id=?",
            (phone, str(row["cidade"] or ""), full_address, cid),
        )
        return cid

    cur = conn.execute(
        "INSERT INTO clientes(nome,telefone,cidade,endereco,data_cad,observacoes,ativo) VALUES (?,?,?,?,?,?,1)",
        (name, phone, str(row["cidade"] or ""), full_address, today, "Cliente originado pela Loja Kero Fish"),
    )
    return int(cur.lastrowid)


def confirm_online_order(ui, order_id: int, payment_confirmed: bool, delivery_status: str = "Aguardando") -> list[int]:
    ensure_online_orders_schema(ui)
    actor = str(ui.st.session_state.get("auth_username", "") or "system")
    today = date.today().isoformat()
    now = datetime.now().isoformat(timespec="seconds")

    with ui.connect() as conn:
        row = conn.execute("SELECT * FROM pedidos_online WHERE id=?", (int(order_id),)).fetchone()
        if not row:
            raise ValueError("Pedido online não encontrado.")
        if str(row["status"] or "").upper() != "NOVO":
            raise ValueError("Este pedido já foi processado ou cancelado.")

        items = _items(row)
        if not items:
            raise ValueError("O pedido não possui itens válidos.")

        catalog = {}
        for item in items:
            pid = int(item.get("product_id") or 0)
            product = conn.execute("SELECT id,nome,COALESCE(preco_venda,0) preco_venda FROM produtos WHERE id=? AND COALESCE(ativo,1)=1", (pid,)).fetchone()
            if not product:
                raise ValueError(f"Produto indisponível no ERP: {item.get('name','item')}")
            qty = float(item.get("quantity") or 0)
            if qty <= 0:
                raise ValueError(f"Quantidade inválida para {product['nome']}.")
            available = _stock_available(conn, str(product["nome"]))
            if available + 1e-9 < qty:
                raise ValueError(f"Estoque insuficiente para {product['nome']}. Disponível: {available:.3f}.")
            catalog[pid] = product

        _upsert_customer(conn, row, today)
        sale_ids: list[int] = []
        payment = _payment_label(row["forma_pagamento"])
        customer = str(row["cliente_nome"] or "")
        web_code = str(row["codigo"] or f"WEB-{order_id}")

        for index, item in enumerate(items, start=1):
            pid = int(item["product_id"])
            product = catalog[pid]
            qty = float(item["quantity"])
            unit_price = float(item.get("unit_price") or product["preco_venda"] or 0)
            line_total = round(qty * unit_price, 2)
            received = line_total if payment_confirmed else 0.0
            pay_status = "Pago" if payment_confirmed else "Pendente"
            pedido = next_order_number(conn, today)
            note = f"Pedido online {web_code} • item {index}/{len(items)}"
            cur = conn.execute(
                """
                INSERT INTO vendas(
                    pedido,cliente,produto,qtd_kg,preco_kg,desconto,valor_total,data_venda,
                    forma_pagamento,status_pagamento,valor_recebido,vencimento,observacoes,
                    source_key,status_pedido,entrega
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (pedido, customer, str(product["nome"]), qty, unit_price, 0.0, line_total, today,
                 payment, pay_status, received, today, note, f"ONLINE:{order_id}:{index}", "Confirmado", 1 if index == 1 else 0),
            )
            sale_id = int(cur.lastrowid)
            sale_ids.append(sale_id)

            if payment_confirmed and line_total > 0:
                conn.execute(
                    "INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id,categoria) VALUES (?,?,?,?,?,?,?,?)",
                    (today, f"Venda {pedido} - pedido online {web_code}", "Entrada", line_total, payment, "venda", sale_id, "Venda"),
                )
            elif line_total > 0:
                conn.execute(
                    "INSERT INTO contas_receber(cliente,descricao,valor,valor_recebido,vencimento,status,origem_tipo,origem_id,forma_pagamento) VALUES (?,?,?,?,?,?,?,?,?)",
                    (customer, f"Venda {pedido} - pedido online {web_code}", line_total, 0.0, today, "Pendente", "venda", sale_id, payment),
                )

            conn.execute(
                "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",
                (now, "CREATE_FROM_ONLINE", "venda", sale_id, f"{web_code} -> {pedido}"),
            )

        first_sale_id = sale_ids[0]
        first_pedido = conn.execute("SELECT pedido FROM vendas WHERE id=?", (first_sale_id,)).fetchone()[0]
        address = ", ".join(x for x in [str(row["endereco"] or "").strip(), str(row["numero"] or "").strip(), str(row["complemento"] or "").strip()] if x)
        conn.execute(
            """
            INSERT INTO entregas(pedido,cliente,data_ent,endereco,bairro,cidade,taxa_entrega,status,observacoes,origem_id)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (first_pedido, customer, today, address, str(row["bairro"] or ""), str(row["cidade"] or ""),
             float(row["taxa_entrega"] or 0), delivery_status, f"Pedido online {web_code}. {str(row['observacoes'] or '')}".strip(), first_sale_id),
        )
        conn.execute(
            "UPDATE pedidos_online SET status='CONFIRMADO',processado_em=?,processado_por=?,vendas_ids_json=?,erro_processamento='' WHERE id=?",
            (now, actor, json.dumps(sale_ids), int(order_id)),
        )
        conn.execute(
            "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",
            (now, "CONFIRM", "pedido_online", int(order_id), f"{web_code}; vendas={sale_ids}"),
        )
        return sale_ids


def cancel_online_order(ui, order_id: int, reason: str = "") -> None:
    ensure_online_orders_schema(ui)
    actor = str(ui.st.session_state.get("auth_username", "") or "system")
    now = datetime.now().isoformat(timespec="seconds")
    with ui.connect() as conn:
        row = conn.execute("SELECT status,codigo FROM pedidos_online WHERE id=?", (int(order_id),)).fetchone()
        if not row:
            raise ValueError("Pedido online não encontrado.")
        if str(row["status"] or "").upper() != "NOVO":
            raise ValueError("Somente pedidos NOVOS podem ser cancelados.")
        conn.execute(
            "UPDATE pedidos_online SET status='CANCELADO',processado_em=?,processado_por=?,erro_processamento=? WHERE id=?",
            (now, actor, str(reason or "Cancelado pelo ERP")[:500], int(order_id)),
        )
        conn.execute(
            "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",
            (now, "CANCEL", "pedido_online", int(order_id), f"{row['codigo']}: {reason}"[:2000]),
        )


def online_orders_page(ui) -> None:
    ensure_online_orders_schema(ui)
    st = ui.st
    ui.page_header("🌐 Pedidos Online", "Pedidos recebidos pela Loja Kero Fish, com confirmação segura antes de afetar o ERP.")

    with ui.connect() as conn:
        summary = conn.execute(
            "SELECT COUNT(*) total, SUM(CASE WHEN status='NOVO' THEN 1 ELSE 0 END) novos, SUM(CASE WHEN status='CONFIRMADO' THEN 1 ELSE 0 END) confirmados, SUM(CASE WHEN status='CANCELADO' THEN 1 ELSE 0 END) cancelados, COALESCE(SUM(CASE WHEN status='NOVO' THEN total ELSE 0 END),0) valor_novos FROM pedidos_online"
        ).fetchone()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Novos", int(summary["novos"] or 0))
    c2.metric("Confirmados", int(summary["confirmados"] or 0))
    c3.metric("Cancelados", int(summary["cancelados"] or 0))
    c4.metric("Valor aguardando", ui.moeda(float(summary["valor_novos"] or 0)))

    status_filter = st.selectbox("Status", ["Todos", "NOVO", "CONFIRMADO", "CANCELADO"], key="online_status_filter")
    sql = "SELECT id,codigo,criado_em,status,cliente_nome,telefone,forma_pagamento,total,cidade,bairro FROM pedidos_online"
    params = ()
    if status_filter != "Todos":
        sql += " WHERE status=?"
        params = (status_filter,)
    sql += " ORDER BY id DESC"
    with ui.connect() as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    if df.empty:
        st.info("Nenhum pedido online neste filtro.")
        return
    df["total"] = df["total"].map(ui.moeda)
    st.dataframe(df, use_container_width=True, hide_index=True)

    ids = [int(v) for v in df["id"].tolist()]
    selected_id = st.selectbox("Abrir pedido", ids, format_func=lambda v: f"#{v} • {df.loc[df['id']==v,'codigo'].iloc[0]}", key="online_order_selected")
    with ui.connect() as conn:
        row = conn.execute("SELECT * FROM pedidos_online WHERE id=?", (selected_id,)).fetchone()
    if not row:
        return

    st.markdown(f"### {row['codigo']} — {row['cliente_nome']}")
    a, b, c = st.columns(3)
    a.write(f"**Telefone:** {row['telefone']}")
    b.write(f"**Pagamento:** {_payment_label(row['forma_pagamento'])}")
    c.write(f"**Total:** {ui.moeda(float(row['total'] or 0))}")
    st.write(f"**Entrega:** {row['endereco']}, {row['numero']} {row['complemento'] or ''} — {row['bairro']} — {row['cidade']} • CEP {row['cep']}")
    if row["observacoes"]:
        st.caption(f"Observações: {row['observacoes']}")

    item_df = pd.DataFrame(_items(row))
    if not item_df.empty:
        rename = {"name": "Produto", "quantity": "Quantidade", "unit_price": "Preço unitário", "line_total": "Total"}
        visible = [c for c in ["name", "quantity", "unit_price", "line_total"] if c in item_df.columns]
        shown = item_df[visible].rename(columns=rename)
        for col in ["Preço unitário", "Total"]:
            if col in shown.columns:
                shown[col] = shown[col].map(ui.moeda)
        st.dataframe(shown, use_container_width=True, hide_index=True)

    if str(row["status"]).upper() == "NOVO":
        st.markdown("#### Processar pedido")
        payment_default = str(row["forma_pagamento"] or "").upper() == "PIX"
        payment_confirmed = st.checkbox("Pagamento já confirmado", value=payment_default, key=f"online_paid_{selected_id}")
        delivery_status = st.selectbox("Status inicial da entrega", ["Aguardando", "Em separação", "Saiu para entrega"], key=f"online_delivery_{selected_id}")
        reason = st.text_input("Motivo do cancelamento (opcional)", key=f"online_cancel_reason_{selected_id}")
        b1, b2 = st.columns(2)
        if b1.button("✅ Confirmar e integrar ao ERP", type="primary", use_container_width=True, key=f"online_confirm_{selected_id}"):
            try:
                ids_created = confirm_online_order(ui, selected_id, payment_confirmed, delivery_status)
                st.success(f"Pedido integrado com segurança. {len(ids_created)} item(ns) lançado(s) em Vendas, Estoque, Financeiro/Receber e Entregas.")
                st.rerun()
            except Exception as exc:
                with ui.connect() as conn:
                    conn.execute("UPDATE pedidos_online SET erro_processamento=? WHERE id=?", (str(exc)[:500], selected_id))
                st.error(f"Não foi possível confirmar: {exc}")
        if b2.button("✖ Cancelar pedido online", use_container_width=True, key=f"online_cancel_{selected_id}"):
            try:
                cancel_online_order(ui, selected_id, reason)
                st.warning("Pedido online cancelado. Nenhum lançamento foi feito no ERP.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    else:
        st.info(f"Pedido {row['status']}. Processado por {row['processado_por'] or '—'} em {row['processado_em'] or '—'}.")


def install_online_orders(ui) -> None:
    ensure_online_orders_schema(ui)
    ui.pedidos_online = lambda: online_orders_page(ui)
