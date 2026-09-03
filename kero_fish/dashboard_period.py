from __future__ import annotations

import pandas as pd


def _period_df(ui, table: str, date_col: str, year: int, month: int | None = None) -> pd.DataFrame:
    """Lê e filtra datas de forma robusta, aceitando ISO e formato brasileiro."""
    try:
        df = ui.query_df(f"SELECT * FROM {table}")
    except Exception:
        return pd.DataFrame()
    if df.empty or date_col not in df.columns:
        return pd.DataFrame(columns=df.columns)
    try:
        try:
            dt = pd.to_datetime(df[date_col], errors="coerce", format="mixed", dayfirst=True)
        except TypeError:
            dt = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
        mask = dt.dt.year.eq(int(year))
        if month is not None:
            mask &= dt.dt.month.eq(int(month))
        return df.loc[mask].copy()
    except Exception:
        return pd.DataFrame(columns=df.columns)


def _num(series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _col(df: pd.DataFrame, *names: str, default=0.0) -> pd.Series:
    for name in names:
        if name in df.columns:
            return _num(df[name])
    return pd.Series([default] * len(df), index=df.index, dtype=float)


def _text_col(df: pd.DataFrame, name: str) -> pd.Series:
    if name not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype=str)
    return df[name].fillna("").astype(str).str.strip()


def _open_balance(df: pd.DataFrame, paid_col: str) -> float:
    if df.empty:
        return 0.0
    status = _text_col(df, "status").str.lower()
    active = df.loc[status.isin(["pendente", "parcial"])].copy()
    if active.empty:
        return 0.0
    total = _col(active, "valor_total", "valor")
    paid = _col(active, paid_col)
    return float((total - paid).clip(lower=0).sum())


def metrics_for_period(ui, year: int, month: int | None = None) -> dict:
    """Calcula somente os cartões do Painel Geral para o mês/ano escolhido.

    Mantém a mesma regra de recuperação do painel principal: quando o razão financeiro
    não representa os lançamentos históricos, os valores são recompostos a partir de
    vendas recebidas, compras pagas e despesas pagas, sem alterar nenhum registro.
    """
    vendas_df = _period_df(ui, "vendas", "data", year, month)
    compras_df = _period_df(ui, "compras", "data", year, month)
    despesas_df = _period_df(ui, "despesas", "data", year, month)
    financeiro_df = _period_df(ui, "financeiro", "data", year, month)
    receber_df = _period_df(ui, "contas_receber", "vencimento", year, month)
    pagar_df = _period_df(ui, "contas_pagar", "vencimento", year, month)

    # Vendas e quantidade registradas no período.
    vendas_total = float(_col(vendas_df, "valor_total", "total").sum()) if not vendas_df.empty else 0.0
    pedidos = int(len(vendas_df))

    # Entradas pelo razão financeiro, quando ele contém dados válidos.
    entradas_fin = 0.0
    saidas_fin = 0.0
    if not financeiro_df.empty:
        tipos = _text_col(financeiro_df, "tipo").str.lower()
        tipos_norm = tipos.str.replace("í", "i", regex=False).str.replace("ã", "a", regex=False)
        valores_fin = _col(financeiro_df, "valor")
        entradas_fin = float(valores_fin[tipos_norm.eq("entrada")].sum())
        saidas_fin = float(valores_fin[tipos_norm.eq("saida")].sum())

    # Recuperação operacional das entradas: valor recebido; se não houver, venda marcada como paga.
    entradas_operacionais = 0.0
    if not vendas_df.empty:
        recebido = _col(vendas_df, "valor_recebido")
        total_venda = _col(vendas_df, "valor_total", "total")
        status_pg = _text_col(vendas_df, "status_pagamento").str.lower()
        valores_entrada = recebido.where(recebido.gt(0), total_venda.where(status_pg.eq("pago"), 0.0))
        entradas_operacionais = float(valores_entrada.sum())

    # Recuperação operacional das saídas: compras pagas + despesas pagas.
    saidas_compras = 0.0
    if not compras_df.empty:
        status_compra = _text_col(compras_df, "status_pagamento").str.lower()
        total_compra = _col(compras_df, "valor_total", "total")
        saidas_compras = float(total_compra.where(status_compra.eq("pago"), 0.0).sum())

    saidas_despesas = 0.0
    if not despesas_df.empty:
        status_desp = _text_col(despesas_df, "status").str.lower()
        valor_desp = _col(despesas_df, "valor")
        saidas_despesas = float(valor_desp.where(status_desp.eq("pago"), 0.0).sum())
    saidas_operacionais = saidas_compras + saidas_despesas

    # Mesma política do painel recuperado: usa o financeiro se houver valor real;
    # caso esteja vazio/zerado, recompõe pelos registros operacionais do próprio período.
    entradas = entradas_fin if abs(entradas_fin) > 0.000001 else entradas_operacionais
    saidas = saidas_fin if abs(saidas_fin) > 0.000001 else saidas_operacionais

    receber = _open_balance(receber_df, "valor_recebido")
    pagar = _open_balance(pagar_df, "valor_pago")

    return {
        "entradas": float(entradas),
        "saidas": float(saidas),
        "saldo": float(entradas - saidas),
        "receber": float(receber),
        "pagar": float(pagar),
        "vendas": float(vendas_total),
        "pedidos": pedidos,
    }
