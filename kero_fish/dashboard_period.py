from __future__ import annotations

import pandas as pd


def _sum_period(ui, table: str, value_expr: str, date_col: str, year: int, month: int | None = None, extra: str = "") -> float:
    try:
        where = f"substr({date_col},1,4)=?"
        params = [f"{year:04d}"]
        if month is not None:
            where += f" AND substr({date_col},6,2)=?"
            params.append(f"{month:02d}")
        if extra:
            where += f" AND ({extra})"
        with ui.connect() as conn:
            row = conn.execute(f"SELECT COALESCE(SUM({value_expr}),0) FROM {table} WHERE {where}", params).fetchone()
        return float(row[0] or 0.0)
    except Exception:
        return 0.0


def metrics_for_period(ui, year: int, month: int | None = None) -> dict:
    """Calcula somente os cartões do Painel Geral para mês/ano escolhido."""
    entradas = _sum_period(ui, "financeiro", "valor", "data", year, month, "lower(tipo)='entrada'")
    saidas = _sum_period(ui, "financeiro", "valor", "data", year, month, "lower(tipo)='saida'")

    # Pendências do período: usa vencimento da obrigação, sem alterar qualquer lançamento.
    receber = _sum_period(ui, "contas_receber", "MAX(COALESCE(valor_total,0)-COALESCE(valor_recebido,0),0)", "vencimento", year, month)
    pagar = _sum_period(ui, "contas_pagar", "MAX(COALESCE(valor_total,0)-COALESCE(valor_pago,0),0)", "vencimento", year, month)

    vendas = _sum_period(ui, "vendas", "COALESCE(total,0)", "data", year, month)
    try:
        where = "substr(data,1,4)=?"
        params = [f"{year:04d}"]
        if month is not None:
            where += " AND substr(data,6,2)=?"
            params.append(f"{month:02d}")
        with ui.connect() as conn:
            pedidos = int(conn.execute(f"SELECT COUNT(*) FROM vendas WHERE {where}", params).fetchone()[0] or 0)
    except Exception:
        pedidos = 0

    return {
        "entradas": entradas,
        "saidas": saidas,
        "saldo": entradas - saidas,
        "receber": receber,
        "pagar": pagar,
        "vendas": vendas,
        "pedidos": pedidos,
    }
