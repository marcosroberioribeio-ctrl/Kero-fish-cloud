from __future__ import annotations

from contextlib import contextmanager


def install_audit_context(ui) -> None:
    """Faz toda conexão SQLite conhecer o usuário da sessão e completa a auditoria automaticamente."""
    from . import annual, db, importer, professional, services

    if getattr(db, "_kero_audit_context_installed", False):
        return

    original_connect = db.connect

    @contextmanager
    def contextual_connect():
        with original_connect() as conn:
            conn.create_function(
                "kero_current_user",
                0,
                lambda: str(ui.st.session_state.get("auth_username", "system") or "system"),
            )
            yield conn

    db.connect = contextual_connect
    ui.connect = contextual_connect
    annual.connect = contextual_connect
    importer.connect = contextual_connect
    professional.connect = contextual_connect
    services.connect = contextual_connect
    db._kero_audit_context_installed = True

    with contextual_connect() as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(audit_log)")}
        if "username" not in cols:
            conn.execute("ALTER TABLE audit_log ADD COLUMN username TEXT DEFAULT ''")
        conn.executescript(
            """
            DROP TRIGGER IF EXISTS trg_audit_actor_ai;
            CREATE TRIGGER trg_audit_actor_ai
            AFTER INSERT ON audit_log
            WHEN COALESCE(NEW.username,'')=''
            BEGIN
              UPDATE audit_log SET username=kero_current_user() WHERE id=NEW.id;
            END;
            """
        )
