from __future__ import annotations

import pandas as pd


def _period_df(ui, table: str, date_cols: tuple[str, ...], year: int, month: int | None = None) -> pd.DataFrame:
    """Lê a tabela e filtra pelo primeiro campo de data existente, aceitando ISO e formato brasileiro."""
    try:
        df = ui.query_df(f"SELECT * FROM {table}")
    except Exception:
        return pd.DataFrame()
    if df.empty:
        return df

    date_col = next((c for c in date_cols if c in df.columns), None)
    if not date_col:
        return pd.DataFrame(columns=df.columns)

    raw = df[date_col].fillna("").astype(str).str.strip()
    try:
        dt = pd.to_datetime(raw, errors="coerce", format="mixed", dayfirst=True)
    except TypeError:
        dt = pd.to_datetime(raw, errors="coerce", dayfirst=True)

    mask = dt.dt.year.eq(int(year))
    if month is not None:
        mask &= dt.dt.month.eq(int(month))
    return df.loc[mask].copy()


def _num(series) -> pd.Series:
    """Converte número salvo como float ou texto BR (R$ 1.234,56) sem zerar silenciosamente."""
    if series is None:
        return pd.Series(dtype=float)
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0.0)
    s = series.fillna("").astype(str).str.strip()
    s = s.str.replace("R$", "", regex=False).str.replace(" ", "", regex=False)
    br_mask = s.str.contains(",", regex=False)
    s.loc[br_mask] = s.loc[br_mask].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _col(df: pd.DataFrame, *names: str, default=0.0) -> pd.Series:
    for name in names:
        if name in df.columns:
            return _num(df[name])
    return pd.Series([default] * len(df), index=df.index, dtype=float)


def _text_col(df: pd.DataFrame, *names: str) -> pd.Series:
    for name in names:
        if name in df.columns:
            return df[name].fillna("").astype(str).str.strip()
    return pd.Series([""] * len(df), index=df.index, dtype=str)


def _norm_text(series: pd.Series) -> pd.Series:
    return (
        series.astype(str).str.strip().str.lower()
        .str.replace("á", "a", regex=False).str.replace("à", "a", regex=False)
        .str.replace("ã", "a", regex=False).str.replace("â", "a", regex=False)
        .str.replace("é", "e", regex=False).str.replace("ê", "e", regex=False)
        .str.replace("í", "i", regex=False).str.replace("ó", "o", regex=False)
        .str.replace("ô", "o", regex=False).str.replace("õ", "o", regex=False)
        .str.replace("ú", "u", regex=False).str.replace("ç", "c", regex=False)
    )


def _open_balance(df: pd.DataFrame, paid_col: str) -> float:
    if df.empty:
        return 0.0
    status = _norm_text(_text_col(df, "status", "status_pagamento"))
    active = df.loc[status.isin(["pendente", "parcial"])].copy()
    if active.empty:
        return 0.0
    total = _col(active, "valor_total", "valor", "total")
    paid = _col(active, paid_col)
    return float((total - paid).clip(lower=0).sum())


def metrics_for_period(ui, year: int, month: int | None = None) -> dict:
    """Calcula exclusivamente os cartões do Painel Geral para o mês/ano selecionado."""
    vendas_df = _period_df(ui, "vendas", ("data", "data_venda"), year, month)
    compras_df = _period_df(ui, "compras", ("data", "data_compra"), year, month)
    despesas_df = _period_df(ui, "despesas", ("data", "data_desp", "data_despesa"), year, month)
    financeiro_df = _period_df(ui, "financeiro", ("data", "data_mov", "data_movimento"), year, month)
    receber_df = _period_df(ui, "contas_receber", ("vencimento", "data_vencimento"), year, month)
    pagar_df = _period_df(ui, "contas_pagar", ("vencimento", "data_vencimento"), year, month)

    vendas_total = float(_col(vendas_df, "valor_total", "total").sum()) if not vendas_df.empty else 0.0
    pedidos = int(len(vendas_df))

    entradas_fin = saidas_fin = 0.0
    if not financeiro_df.empty:
        tipos = _norm_text(_text_col(financeiro_df, "tipo"))
        valores = _col(financeiro_df, "valor")
        entradas_fin = float(valores[tipos.eq("entrada")].sum())
        saidas_fin = float(valores[tipos.eq("saida")].sum())

    entradas_operacionais = 0.0
    if not vendas_df.empty:
        recebido = _col(vendas_df, "valor_recebido")
        total_venda = _col(vendas_df, "valor_total", "total")
        status_pg = _norm_text(_text_col(vendas_df, "status_pagamento"))
        valores_entrada = recebido.where(recebido.gt(0), total_venda.where(status_pg.eq("pago"), 0.0))
        entradas_operacionais = float(valores_entrada.sum())

    saidas_compras = 0.0
    if not compras_df.empty:
        status_compra = _norm_text(_text_col(compras_df, "status_pagamento"))
        total_compra = _col(compras_df, "valor_total", "total")
        saidas_compras = float(total_compra.where(status_compra.eq("pago"), 0.0).sum())

    saidas_despesas = 0.0
    if not despesas_df.empty:
        status_desp = _norm_text(_text_col(despesas_df, "status", "pago"))
        valor_desp = _col(despesas_df, "valor", "valor_total")
        pago_mask = status_desp.isin(["pago", "sim", "1", "true"])
        saidas_despesas = float(valor_desp.where(pago_mask, 0.0).sum())

    saidas_operacionais = saidas_compras + saidas_despesas

    # Se o financeiro do período tiver lançamentos válidos, ele prevalece.
    # Caso contrário, usa os registros operacionais, exatamente como a recuperação do painel principal.
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
