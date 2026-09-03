from __future__ import annotations

import json
import re
from datetime import date, datetime

from .db import connect

_ORDER_RE = re.compile(r"^KF-(\d{4})-(\d+)$", re.IGNORECASE)


def _year_from_value(value) -> int:
    if isinstance(value, (date, datetime)):
        return int(value.year)
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text[:10], fmt).year
        except ValueError:
            pass
    return date.today().year


def ensure_professional_schema() -> None:
    """Migrações aditivas da V12.1: endereço, sequência anual e fechamento de exercício."""
    address_columns = {
        "clientes": {
            "cep": "TEXT DEFAULT ''", "bairro": "TEXT DEFAULT ''", "uf": "TEXT DEFAULT ''",
            "numero": "TEXT DEFAULT ''", "complemento": "TEXT DEFAULT ''",
        },
        "fornecedores": {
            "cep": "TEXT DEFAULT ''", "bairro": "TEXT DEFAULT ''", "cidade": "TEXT DEFAULT ''",
            "uf": "TEXT DEFAULT ''", "numero": "TEXT DEFAULT ''", "complemento": "TEXT DEFAULT ''",
        },
        "entregas": {
            "cep": "TEXT DEFAULT ''", "uf": "TEXT DEFAULT ''", "numero": "TEXT DEFAULT ''",
            "complemento": "TEXT DEFAULT ''",
        },
    }
    with connect() as conn:
        for table, columns in address_columns.items():
            current = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            for name, definition in columns.items():
                if name not in current:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS order_sequences (
                ano INTEGER PRIMARY KEY,
                ultimo_numero INTEGER NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS annual_closings (
                ano INTEGER PRIMARY KEY,
                fechado_em TEXT NOT NULL,
                resumo_json TEXT NOT NULL,
                observacoes TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_vendas_data_venda ON vendas(data_venda);
            CREATE INDEX IF NOT EXISTS idx_compras_data_compra ON compras(data_compra);
            CREATE INDEX IF NOT EXISTS idx_financeiro_data_mov ON financeiro(data_mov);
            CREATE INDEX IF NOT EXISTS idx_despesas_data_desp ON despesas(data_desp);
            CREATE INDEX IF NOT EXISTS idx_entregas_data_ent ON entregas(data_ent);
            """
        )


def next_order_number(conn, sale_date) -> str:
    """Gera KF-ANO-000001, reiniciando a sequência a cada exercício sem colidir."""
    year = _year_from_value(sale_date)
    prefix = f"KF-{year}-"
    max_existing = 0
    rows = conn.execute("SELECT pedido FROM vendas WHERE pedido LIKE ?", (prefix + "%",)).fetchall()
    for row in rows:
        value = row[0] if not hasattr(row, "keys") else row["pedido"]
        match = _ORDER_RE.match(str(value or ""))
        if match and int(match.group(1)) == year:
            max_existing = max(max_existing, int(match.group(2)))

    row = conn.execute("SELECT ultimo_numero FROM order_sequences WHERE ano=?", (year,)).fetchone()
    current = int(row[0]) if row else 0
    current = max(current, max_existing) + 1
    conn.execute(
        """
        INSERT INTO order_sequences(ano,ultimo_numero,atualizado_em) VALUES (?,?,?)
        ON CONFLICT(ano) DO UPDATE SET ultimo_numero=excluded.ultimo_numero,atualizado_em=excluded.atualizado_em
        """,
        (year, current, datetime.now().isoformat(timespec="seconds")),
    )
    return f"KF-{year}-{current:06d}"


def available_years() -> list[int]:
    years = {date.today().year}
    queries = (
        ("vendas", "COALESCE(NULLIF(data_venda,''),data)"),
        ("compras", "COALESCE(NULLIF(data_compra,''),data)"),
        ("financeiro", "COALESCE(NULLIF(data_mov,''),data)"),
        ("despesas", "COALESCE(NULLIF(data_desp,''),data)"),
        ("entregas", "data_ent"),
    )
    with connect() as conn:
        for table, column in queries:
            try:
                for row in conn.execute(f"SELECT DISTINCT substr({column},1,4) ano FROM {table} WHERE {column}<>''"):
                    text = str(row[0] or "")
                    if text.isdigit() and len(text) == 4:
                        years.add(int(text))
            except Exception:
                continue
        for row in conn.execute("SELECT ano FROM annual_closings"):
            years.add(int(row[0]))
    return sorted(years, reverse=True)


def year_summary(year: int) -> dict[str, float | int]:
    start, end = f"{year:04d}-01-01", f"{year:04d}-12-31"
    with connect() as conn:
        def scalar(sql, params=(start, end), default=0):
            row = conn.execute(sql, params).fetchone()
            return row[0] if row and row[0] is not None else default

        vendas = float(scalar("SELECT COALESCE(SUM(valor_total),0) FROM vendas WHERE data_venda BETWEEN ? AND ?"))
        compras = float(scalar("SELECT COALESCE(SUM(valor_total),0) FROM compras WHERE data_compra BETWEEN ? AND ?"))
        entradas = float(scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Entrada' AND data_mov BETWEEN ? AND ?"))
        saidas = float(scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Saída' AND data_mov BETWEEN ? AND ?"))
        despesas = float(scalar("SELECT COALESCE(SUM(valor),0) FROM despesas WHERE data_desp BETWEEN ? AND ?"))
        qtd_vendas = int(scalar("SELECT COUNT(*) FROM vendas WHERE data_venda BETWEEN ? AND ?"))
        qtd_compras = int(scalar("SELECT COUNT(*) FROM compras WHERE data_compra BETWEEN ? AND ?"))
        receber = float(scalar("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_recebido,0),0)),0) FROM contas_receber WHERE status IN ('Pendente','Parcial')", (), 0))
        pagar = float(scalar("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_pago,0),0)),0) FROM contas_pagar WHERE status IN ('Pendente','Parcial')", (), 0))
    return {
        "ano": year, "vendas": vendas, "compras": compras, "entradas": entradas, "saidas": saidas,
        "saldo": entradas - saidas, "despesas": despesas, "qtd_vendas": qtd_vendas,
        "qtd_compras": qtd_compras, "receber_aberto": receber, "pagar_aberto": pagar,
    }


def close_year(year: int, notes: str = "") -> dict:
    """Registra um snapshot de encerramento; nunca apaga nem move dados históricos."""
    if year > date.today().year:
        raise ValueError("Não é possível fechar um exercício futuro.")
    summary = year_summary(year)
    with connect() as conn:
        existing = conn.execute("SELECT fechado_em FROM annual_closings WHERE ano=?", (year,)).fetchone()
        if existing:
            raise ValueError(f"O exercício {year} já foi fechado em {existing[0]}.")
        stamp = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO annual_closings(ano,fechado_em,resumo_json,observacoes) VALUES (?,?,?,?)",
            (year, stamp, json.dumps(summary, ensure_ascii=False), str(notes or "")[:2000]),
        )
        conn.execute(
            "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",
            (stamp, "YEAR_CLOSE", "exercicio", year, f"Fechamento anual {year}"),
        )
    return summary


def closing_info(year: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT ano,fechado_em,resumo_json,observacoes FROM annual_closings WHERE ano=?", (year,)).fetchone()
    if not row:
        return None
    return {
        "ano": int(row[0]), "fechado_em": row[1], "resumo": json.loads(row[2]), "observacoes": row[3] or ""
    }


def install_annual_order_patch() -> None:
    """Aplica a sequência anual sem alterar a API pública existente da camada profissional."""
    from . import professional, services

    def register_sale_annual(*args) -> int:
        if len(args) != 10:
            raise TypeError("register_sale espera 10 argumentos")
        entrega_flag = False
        status_pedido = ""
        if services._looks_date(args[0]):
            data_venda, cliente, produto, qtd, preco, desconto, forma, recebido, status_pedido, entrega_flag = args
            vencimento = data_venda
            observacoes = ""
        else:
            cliente, produto, qtd, preco, desconto, data_venda, forma, recebido, vencimento, observacoes = args
        qtd = float(qtd or 0); preco = float(preco or 0); desconto = float(desconto or 0); recebido = float(recebido or 0)
        total = max(0.0, qtd * preco - desconto); recebido = min(max(recebido, 0.0), total)
        status = "Pago" if total > 0 and recebido >= total else ("Parcial" if recebido > 0 else "Pendente")
        with connect() as conn:
            pedido = next_order_number(conn, data_venda)
            cur = conn.execute(
                "INSERT INTO vendas(pedido,cliente,produto,qtd_kg,preco_kg,desconto,valor_total,data_venda,forma_pagamento,status_pagamento,valor_recebido,vencimento,observacoes,status_pedido,entrega) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (pedido,cliente,produto,qtd,preco,desconto,total,data_venda,forma,status,recebido,vencimento,observacoes,status_pedido,1 if entrega_flag else 0),
            )
            vid = cur.lastrowid
            if recebido > 0:
                conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id,categoria) VALUES (?,?,?,?,?,?,?,?)", (data_venda,f"Venda {pedido} - recebimento","Entrada",recebido,forma,"venda",vid,"Venda"))
            if total - recebido > 0:
                conn.execute("INSERT INTO contas_receber(cliente,descricao,valor,valor_recebido,vencimento,status,origem_tipo,origem_id,forma_pagamento) VALUES (?,?,?,?,?,?,?,?,?)", (cliente,f"Venda {pedido}",total,recebido,vencimento or data_venda,status,"venda",vid,forma))
            if entrega_flag:
                conn.execute("INSERT INTO entregas(pedido,cliente,data_ent,status,origem_id) VALUES (?,?,?,?,?)", (pedido,cliente,data_venda,status_pedido or "Aguardando",vid))
            conn.execute("INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)", (datetime.now().isoformat(timespec="seconds"),"CREATE","venda",vid,pedido))
            return vid

    services.register_sale = register_sale_annual
    professional.register_sale = register_sale_annual
