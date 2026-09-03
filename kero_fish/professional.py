from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from .db import BACKUP_DIR, DB_PATH, connect
from .services import register_purchase, register_sale, scalar


@dataclass(frozen=True)
class HealthReport:
    database_ok: bool
    integrity: str
    foreign_key_issues: int
    database_size_mb: float
    backups: int
    last_backup: str
    negative_stock_items: int
    overdue_payables: int
    overdue_receivables: int


def audit_event(action: str, entity_type: str = "system", entity_id: int | None = None, detail: str = "") -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), action, entity_type, entity_id, detail[:2000]),
        )


def _integrity_for(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, "arquivo não encontrado"
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        result = str(row[0]) if row else "sem resposta"
        return result.lower() == "ok", result
    finally:
        conn.close()


def safe_backup(reason: str = "manual") -> Path | None:
    """Cria snapshot consistente usando a API de backup do SQLite, inclusive com WAL ativo."""
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = BACKUP_DIR / f"kerofish_{reason}_{stamp}.db"

    source = sqlite3.connect(DB_PATH, timeout=30)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
        destination.commit()
    finally:
        destination.close()
        source.close()

    ok, detail = _integrity_for(target)
    if not ok:
        target.unlink(missing_ok=True)
        raise RuntimeError(f"Backup descartado: falha de integridade ({detail}).")

    audit_event("BACKUP", "database", None, f"{target.name} | reason={reason}")
    return target


def restore_backup(backup_path: str | Path) -> Path:
    """Restaura com verificação prévia e cria snapshot de emergência antes da troca."""
    source_path = Path(backup_path)
    if source_path.parent.resolve() != BACKUP_DIR.resolve():
        raise ValueError("O arquivo de restauração deve estar na pasta oficial de backups.")

    ok, detail = _integrity_for(source_path)
    if not ok:
        raise RuntimeError(f"Backup inválido: {detail}")

    emergency = safe_backup("pre_restore")
    if emergency is None:
        raise RuntimeError("Não foi possível criar o backup de emergência.")

    source = sqlite3.connect(source_path, timeout=30)
    destination = sqlite3.connect(DB_PATH, timeout=30)
    try:
        source.backup(destination)
        destination.commit()
    finally:
        destination.close()
        source.close()

    ok_after, detail_after = _integrity_for(DB_PATH)
    if not ok_after:
        rollback_source = sqlite3.connect(emergency, timeout=30)
        rollback_destination = sqlite3.connect(DB_PATH, timeout=30)
        try:
            rollback_source.backup(rollback_destination)
            rollback_destination.commit()
        finally:
            rollback_destination.close()
            rollback_source.close()
        raise RuntimeError(f"Restauração revertida: integridade final falhou ({detail_after}).")

    audit_event("RESTORE", "database", None, source_path.name)
    return emergency


def _stock_available(product: str) -> float:
    product = product.strip()
    purchases = float(scalar("SELECT COALESCE(SUM(qtd),0) FROM compras WHERE lower(produto)=lower(?)", (product,)))
    sales = float(scalar("SELECT COALESCE(SUM(qtd_kg),0) FROM vendas WHERE lower(produto)=lower(?)", (product,)))
    adjustments = float(
        scalar(
            """
            SELECT COALESCE(SUM(
                CASE
                    WHEN upper(COALESCE(tipo,'')) IN ('AJUSTE_ENTRADA','AJUSTE ENTRADA') THEN ABS(COALESCE(quantidade,0))
                    WHEN upper(COALESCE(tipo,'')) IN ('AJUSTE_SAIDA','AJUSTE SAÍDA','AJUSTE SAIDA','PERDA') THEN -ABS(COALESCE(quantidade,0))
                    WHEN lower(COALESCE(origem_tipo,''))='manual' THEN COALESCE(quantidade,0)
                    ELSE 0
                END
            ),0)
            FROM movimentos_estoque WHERE lower(produto)=lower(?)
            """,
            (product,),
        )
    )
    return purchases - sales + adjustments


def register_purchase_safe(data_compra, fornecedor, produto, qtd, preco, lote, validade, local_estoque, forma, status) -> int:
    fornecedor = str(fornecedor or "").strip()
    produto = str(produto or "").strip()
    qtd = float(qtd or 0)
    preco = float(preco or 0)
    if not fornecedor:
        raise ValueError("Informe o fornecedor.")
    if not produto:
        raise ValueError("Informe o produto.")
    if qtd <= 0:
        raise ValueError("A quantidade da compra deve ser maior que zero.")
    if preco < 0:
        raise ValueError("O custo unitário não pode ser negativo.")
    rid = register_purchase(data_compra, fornecedor, produto, qtd, preco, lote, validade, local_estoque, forma, status)
    audit_event("BUSINESS_VALIDATION_OK", "compra", rid, "Compra validada pela camada profissional")
    return rid


def register_sale_safe(data_venda, cliente, produto, qtd, preco, desconto, forma, recebido, status_pedido, entrega_flag) -> int:
    cliente = str(cliente or "").strip()
    produto = str(produto or "").strip()
    qtd = float(qtd or 0)
    preco = float(preco or 0)
    desconto = float(desconto or 0)
    recebido = float(recebido or 0)
    if not cliente:
        raise ValueError("Informe o cliente.")
    if not produto:
        raise ValueError("Informe o produto.")
    if qtd <= 0:
        raise ValueError("A quantidade da venda deve ser maior que zero.")
    if preco < 0 or desconto < 0 or recebido < 0:
        raise ValueError("Preço, desconto e valor recebido não podem ser negativos.")
    total = max(0.0, qtd * preco - desconto)
    if recebido > total:
        raise ValueError("O valor recebido não pode ser maior que o total da venda.")
    available = _stock_available(produto)
    if qtd > available + 1e-9:
        raise ValueError(f"Estoque insuficiente para {produto}. Disponível: {available:.3f}.")
    rid = register_sale(data_venda, cliente, produto, qtd, preco, desconto, forma, recebido, status_pedido, entrega_flag)
    audit_event("BUSINESS_VALIDATION_OK", "venda", rid, f"Estoque anterior={available:.3f}")
    return rid


def health_report() -> HealthReport:
    db_ok, integrity = _integrity_for(DB_PATH)
    fk_issues = 0
    if DB_PATH.exists():
        with connect() as conn:
            fk_issues = len(conn.execute("PRAGMA foreign_key_check").fetchall())

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backups = sorted(BACKUP_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    last_backup = datetime.fromtimestamp(backups[0].stat().st_mtime).strftime("%d/%m/%Y %H:%M") if backups else "Nunca"

    today = datetime.now().strftime("%Y-%m-%d")
    negative_stock = 0
    try:
        products = pd.read_sql_query("SELECT nome FROM produtos WHERE ativo=1", sqlite3.connect(DB_PATH)) if DB_PATH.exists() else pd.DataFrame()
        negative_stock = sum(1 for p in products.get("nome", []) if _stock_available(str(p)) < -1e-9)
    except Exception:
        negative_stock = -1

    overdue_payables = int(scalar("SELECT COUNT(*) FROM contas_pagar WHERE status IN ('Pendente','Parcial') AND vencimento<>'' AND vencimento<?", (today,)))
    overdue_receivables = int(scalar("SELECT COUNT(*) FROM contas_receber WHERE status IN ('Pendente','Parcial') AND vencimento<>'' AND vencimento<?", (today,)))

    return HealthReport(
        database_ok=db_ok and fk_issues == 0,
        integrity=integrity,
        foreign_key_issues=fk_issues,
        database_size_mb=round(DB_PATH.stat().st_size / (1024 * 1024), 2) if DB_PATH.exists() else 0.0,
        backups=len(backups),
        last_backup=last_backup,
        negative_stock_items=negative_stock,
        overdue_payables=overdue_payables,
        overdue_receivables=overdue_receivables,
    )


def recent_audit(limit: int = 500) -> pd.DataFrame:
    limit = max(1, min(int(limit), 5000))
    with connect() as conn:
        return pd.read_sql_query(
            f"SELECT id,event_time,action,entity_type,entity_id,detail FROM audit_log ORDER BY id DESC LIMIT {limit}",
            conn,
        )
