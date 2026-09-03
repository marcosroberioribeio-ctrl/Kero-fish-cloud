from __future__ import annotations


def install_dashboard_recovery(ui) -> None:
    """Recupera indicadores a partir dos registros operacionais quando o financeiro não representa os dados.

    Camada somente de leitura: não insere, apaga ou altera registros. Se o razão financeiro
    estiver vazio OU existir com valores zerados, o painel recompõe os indicadores usando
    vendas, compras e despesas que continuam presentes no banco.
    """
    original = ui.dashboard_metrics
    if getattr(original, "_kero_recovery_wrapped", False):
        return

    def _scalar(conn, sql: str, default=0.0):
        try:
            row = conn.execute(sql).fetchone()
            return row[0] if row and row[0] is not None else default
        except Exception:
            return default

    def dashboard_metrics_recovered():
        try:
            base = dict(original())
        except Exception:
            base = {
                "entradas": 0.0,
                "saidas": 0.0,
                "saldo": 0.0,
                "receber": 0.0,
                "pagar": 0.0,
                "vendas": 0.0,
                "compras": 0.0,
                "qtd_vendas": 0,
                "qtd_compras": 0,
            }

        try:
            with ui.connect() as conn:
                qtd_vendas = int(_scalar(conn, "SELECT COUNT(*) FROM vendas", 0))
                qtd_compras = int(_scalar(conn, "SELECT COUNT(*) FROM compras", 0))

                vendas_total = float(_scalar(conn, "SELECT COALESCE(SUM(COALESCE(NULLIF(valor_total,0),total,0)),0) FROM vendas", 0.0))
                compras_total = float(_scalar(conn, "SELECT COALESCE(SUM(COALESCE(NULLIF(valor_total,0),total,0)),0) FROM compras", 0.0))

                entradas_operacionais = float(_scalar(conn, """
                    SELECT COALESCE(SUM(
                        CASE
                          WHEN COALESCE(valor_recebido,0) > 0 THEN valor_recebido
                          WHEN status_pagamento='Pago' THEN COALESCE(NULLIF(valor_total,0),total,0)
                          ELSE 0
                        END
                    ),0) FROM vendas
                """, 0.0))
                saidas_compras = float(_scalar(conn, """
                    SELECT COALESCE(SUM(
                        CASE WHEN status_pagamento='Pago'
                             THEN COALESCE(NULLIF(valor_total,0),total,0)
                             ELSE 0 END
                    ),0) FROM compras
                """, 0.0))
                saidas_despesas = float(_scalar(conn, """
                    SELECT COALESCE(SUM(CASE WHEN status='Pago' THEN valor ELSE 0 END),0)
                    FROM despesas
                """, 0.0))
                saidas_operacionais = saidas_compras + saidas_despesas

                # Se o financeiro estiver ausente, vazio ou zerado, mas houver operação real,
                # usa os registros mestres para EXIBIÇÃO dos cartões.
                if (float(base.get("entradas", 0) or 0) == 0 and entradas_operacionais > 0):
                    base["entradas"] = entradas_operacionais
                if (float(base.get("saidas", 0) or 0) == 0 and saidas_operacionais > 0):
                    base["saidas"] = saidas_operacionais
                base["saldo"] = float(base.get("entradas", 0) or 0) - float(base.get("saidas", 0) or 0)

                if qtd_vendas > 0:
                    base["vendas"] = vendas_total
                    base["qtd_vendas"] = qtd_vendas
                if qtd_compras > 0:
                    base["compras"] = compras_total
                    base["qtd_compras"] = qtd_compras

                if float(base.get("receber", 0) or 0) == 0:
                    base["receber"] = float(_scalar(conn, """
                        SELECT COALESCE(SUM(
                          CASE WHEN status_pagamento IN ('Pendente','Parcial')
                               THEN MAX(COALESCE(NULLIF(valor_total,0),total,0)-COALESCE(valor_recebido,0),0)
                               ELSE 0 END
                        ),0) FROM vendas
                    """, 0.0))
                if float(base.get("pagar", 0) or 0) == 0:
                    base["pagar"] = float(_scalar(conn, """
                        SELECT COALESCE(SUM(
                          CASE WHEN status_pagamento IN ('Pendente','Parcial')
                               THEN COALESCE(NULLIF(valor_total,0),total,0)
                               ELSE 0 END
                        ),0) FROM compras
                    """, 0.0))
        except Exception:
            pass

        return base

    dashboard_metrics_recovered._kero_recovery_wrapped = True
    ui.dashboard_metrics = dashboard_metrics_recovered
