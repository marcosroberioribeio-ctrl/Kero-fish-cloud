from __future__ import annotations


def install_consistency_guards(ui) -> None:
    from . import professional
    from .professional import safe_backup

    def stock_available(product: str) -> float:
        product = str(product or "").strip()
        if not product:
            return 0.0
        with ui.connect() as conn:
            purchases = conn.execute(
                "SELECT COALESCE(SUM(qtd),0) FROM compras WHERE lower(produto)=lower(?)",
                (product,),
            ).fetchone()[0]
            sales = conn.execute(
                """
                SELECT COALESCE(SUM(qtd_kg),0) FROM vendas
                WHERE lower(produto)=lower(?) AND upper(COALESCE(status_pedido,''))<>'CANCELADO'
                """,
                (product,),
            ).fetchone()[0]
            adjustments = conn.execute(
                """
                SELECT COALESCE(SUM(COALESCE(quantidade,0)),0)
                FROM movimentos_estoque
                WHERE lower(produto)=lower(?)
                  AND (
                    lower(COALESCE(NULLIF(origem_tipo,''),origem,'')) IN ('manual','ajuste')
                    OR upper(COALESCE(tipo,'')) IN ('AJUSTE_ENTRADA','AJUSTE ENTRADA','AJUSTE_SAIDA','AJUSTE SAÍDA','AJUSTE SAIDA','PERDA')
                  )
                """,
                (product,),
            ).fetchone()[0]
        return float(purchases or 0) - float(sales or 0) + float(adjustments or 0)

    professional._stock_available = stock_available

    # Toda importação iniciada pela interface usa snapshot SQLite validado.
    original_import = ui.import_excel
    def import_with_safe_backup(path, create_backup=True):
        if create_backup:
            safe_backup("pre_import")
        return original_import(path, create_backup=False)
    ui.import_excel = import_with_safe_backup
