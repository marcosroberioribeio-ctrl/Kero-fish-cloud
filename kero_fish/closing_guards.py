from __future__ import annotations


def install_closing_guards(ui) -> None:
    """Protege exercícios fechados inclusive contra mudança de data para ano já encerrado."""
    specs = {
        "vendas": "COALESCE(NULLIF({alias}.data_venda,''),{alias}.data)",
        "compras": "COALESCE(NULLIF({alias}.data_compra,''),{alias}.data)",
        "despesas": "COALESCE(NULLIF({alias}.data_desp,''),{alias}.data)",
        "financeiro": "COALESCE(NULLIF({alias}.data_mov,''),{alias}.data)",
        "entregas": "{alias}.data_ent",
    }
    with ui.connect() as conn:
        for table, expr in specs.items():
            old_expr = expr.format(alias="OLD")
            new_expr = expr.format(alias="NEW")
            conn.executescript(
                f"""
                DROP TRIGGER IF EXISTS trg_lock_{table}_bu;
                DROP TRIGGER IF EXISTS trg_lock_{table}_bd;
                DROP TRIGGER IF EXISTS trg_lock_{table}_bi;

                CREATE TRIGGER trg_lock_{table}_bu BEFORE UPDATE ON {table}
                WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr({old_expr},1,4) AS INTEGER))
                  OR EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr({new_expr},1,4) AS INTEGER))
                BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de alterar este registro.'); END;

                CREATE TRIGGER trg_lock_{table}_bd BEFORE DELETE ON {table}
                WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr({old_expr},1,4) AS INTEGER))
                BEGIN SELECT RAISE(ABORT,'Exercício fechado: registro protegido.'); END;

                CREATE TRIGGER trg_lock_{table}_bi BEFORE INSERT ON {table}
                WHEN EXISTS(SELECT 1 FROM annual_closings WHERE ano=CAST(substr({new_expr},1,4) AS INTEGER))
                BEGIN SELECT RAISE(ABORT,'Exercício fechado: reabra o ano antes de lançar este registro.'); END;
                """
            )
