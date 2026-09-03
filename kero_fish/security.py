from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta


_BOOTSTRAP_USERS = {
    "roberio": {
        "display_name": "Robério",
        "role": "ADMIN_TOTAL",
        "salt": "de0370d2e1875b3121e7401523c2d9ca",
        "password_hash": "706f6143d8e7908a03be7d2bb985148e00e3f70800b58f76e2031b86b57d1a20",
    },
    "marines": {
        "display_name": "Marinês",
        "role": "ADMIN_TOTAL",
        "salt": "4cf27ba4421df4e5c2dbaf669b673be2",
        "password_hash": "8c48cc0d7c03bb6d44fc995690da80105d7e0f21bd5ca2b11b19410332165850",
    },
    "arruda": {
        "display_name": "Arruda",
        "role": "SOCIO",
        "salt": "41453e4fd50743c13a4b2beeca235b31",
        "password_hash": "1999a71eb92ef10ea68f821f7266c4ad81bf9d650a4b7f52c13ec385e1a3f590",
    },
    "eliete": {
        "display_name": "Eliete",
        "role": "SOCIO",
        "salt": "8a29f2cc1c9838f15999043b7781ecd0",
        "password_hash": "1a73dc2e9f2e65695faa531240d6b7d49feb492022ae6a5283d46351536ff96c",
    },
}


def _hash_password(password: str, salt_hex: str) -> str:
    return hashlib.scrypt(
        str(password).encode("utf-8"),
        salt=bytes.fromhex(salt_hex),
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    ).hex()


def verify_password(password: str, salt_hex: str, expected_hash: str) -> bool:
    try:
        return hmac.compare_digest(_hash_password(password, salt_hex), str(expected_hash))
    except Exception:
        return False


def _new_password_material(password: str) -> tuple[str, str]:
    salt = os.urandom(16).hex()
    return salt, _hash_password(password, salt)


def ensure_security_schema(ui) -> None:
    with ui.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'SOCIO',
                is_partner INTEGER NOT NULL DEFAULT 1,
                active INTEGER NOT NULL DEFAULT 1,
                must_change_password INTEGER NOT NULL DEFAULT 1,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT DEFAULT '',
                last_login TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            """
        )
        audit_cols = {row[1] for row in conn.execute("PRAGMA table_info(audit_log)")}
        if "username" not in audit_cols:
            conn.execute("ALTER TABLE audit_log ADD COLUMN username TEXT DEFAULT ''")

        now = datetime.now().isoformat(timespec="seconds")
        for username, cfg in _BOOTSTRAP_USERS.items():
            conn.execute(
                """
                INSERT OR IGNORE INTO users(
                    username,display_name,password_salt,password_hash,role,is_partner,active,
                    must_change_password,failed_attempts,locked_until,last_login,created_at,updated_at
                ) VALUES (?,?,?,?,?,1,1,1,0,'','',?,?)
                """,
                (username, cfg["display_name"], cfg["salt"], cfg["password_hash"], cfg["role"], now, now),
            )


def _audit(ui, action: str, detail: str = "", entity_type: str = "security", entity_id=None, username: str = "") -> None:
    actor = username or str(ui.st.session_state.get("auth_username", "system") or "system")
    with ui.connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail,username) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), action, entity_type, entity_id, str(detail)[:2000], actor),
        )


def _load_user(ui, username: str):
    with ui.connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username=?",
            (str(username or "").strip().lower(),),
        ).fetchone()


def _authenticate(ui, username: str, password: str) -> tuple[bool, str]:
    username = str(username or "").strip().lower()
    row = _load_user(ui, username)
    if not row or not int(row["active"] or 0):
        return False, "Usuário ou senha inválidos."

    locked_until = str(row["locked_until"] or "")
    if locked_until:
        try:
            if datetime.fromisoformat(locked_until) > datetime.now():
                return False, "Acesso temporariamente bloqueado. Aguarde alguns minutos e tente novamente."
        except ValueError:
            pass

    if not verify_password(password, row["password_salt"], row["password_hash"]):
        attempts = int(row["failed_attempts"] or 0) + 1
        lock = ""
        if attempts >= 5:
            lock = (datetime.now() + timedelta(minutes=15)).isoformat(timespec="seconds")
            attempts = 0
        with ui.connect() as conn:
            conn.execute("UPDATE users SET failed_attempts=?,locked_until=?,updated_at=? WHERE id=?", (attempts, lock, datetime.now().isoformat(timespec="seconds"), row["id"]))
        return False, "Usuário ou senha inválidos."

    now = datetime.now().isoformat(timespec="seconds")
    with ui.connect() as conn:
        conn.execute("UPDATE users SET failed_attempts=0,locked_until='',last_login=?,updated_at=? WHERE id=?", (now, now, row["id"]))
    ui.st.session_state["auth_username"] = row["username"]
    ui.st.session_state["auth_display_name"] = row["display_name"]
    ui.st.session_state["auth_role"] = row["role"]
    ui.st.session_state["auth_must_change"] = bool(row["must_change_password"])
    _audit(ui, "LOGIN", "Login efetuado", "usuario", int(row["id"]), row["username"])
    return True, ""


def _logout(ui) -> None:
    username = str(ui.st.session_state.get("auth_username", "") or "")
    if username:
        _audit(ui, "LOGOUT", "Logout efetuado", "usuario", None, username)
    for key in ["auth_username", "auth_display_name", "auth_role", "auth_must_change"]:
        ui.st.session_state.pop(key, None)
    ui.st.rerun()


def _change_password(ui, username: str, current_password: str, new_password: str, confirm: str) -> tuple[bool, str]:
    row = _load_user(ui, username)
    if not row or not verify_password(current_password, row["password_salt"], row["password_hash"]):
        return False, "A senha atual está incorreta."
    if len(new_password) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres."
    if new_password != confirm:
        return False, "A confirmação da nova senha não confere."
    if verify_password(new_password, row["password_salt"], row["password_hash"]):
        return False, "A nova senha precisa ser diferente da senha atual."
    salt, password_hash = _new_password_material(new_password)
    now = datetime.now().isoformat(timespec="seconds")
    with ui.connect() as conn:
        conn.execute(
            "UPDATE users SET password_salt=?,password_hash=?,must_change_password=0,updated_at=? WHERE id=?",
            (salt, password_hash, now, row["id"]),
        )
    ui.st.session_state["auth_must_change"] = False
    _audit(ui, "PASSWORD_CHANGE", "Senha alterada pelo próprio usuário", "usuario", int(row["id"]), username)
    return True, "Senha alterada com segurança."


def _login_screen(ui) -> None:
    st = ui.st
    st.markdown(
        """
        <style>
        [data-testid='stSidebar']{display:none!important}
        .kf-login-wrap{max-width:470px;margin:8vh auto 0;padding:28px 30px;border:1px solid #315d80;border-radius:22px;background:linear-gradient(145deg,#0c3454,#08233c);box-shadow:0 24px 70px #0008;text-align:center}
        .kf-login-title{font-size:31px;font-weight:900;color:#f7c44d}.kf-login-sub{font-size:15px;color:#d8e8f4;margin-top:6px;margin-bottom:14px}
        </style>
        <div class='kf-login-wrap'><div class='kf-login-title'>Kero Fish ERP</div><div class='kf-login-sub'>Acesso seguro • V12.1 Profissional</div></div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c2:
        with st.form("kf_login_form"):
            username = st.text_input("Usuário", placeholder="Digite seu usuário").strip().lower()
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", type="primary", use_container_width=True)
        if submitted:
            ok, msg = _authenticate(ui, username, password)
            if ok:
                st.rerun()
            else:
                st.error(msg)


def _mandatory_password_screen(ui) -> None:
    st = ui.st
    username = st.session_state["auth_username"]
    display = st.session_state.get("auth_display_name", username)
    st.markdown(f"## 🔐 Primeiro acesso — {display}")
    st.info("Sua senha atual é provisória. Cadastre agora uma senha pessoal antes de usar o ERP.")
    with st.form("kf_first_password_change"):
        current = st.text_input("Senha provisória atual", type="password")
        new = st.text_input("Nova senha", type="password")
        confirm = st.text_input("Confirmar nova senha", type="password")
        submitted = st.form_submit_button("Salvar nova senha", type="primary")
    if submitted:
        ok, msg = _change_password(ui, username, current, new, confirm)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)
    if st.button("Sair", key="logout_first_access"):
        _logout(ui)


def _reset_to_initial(ui, username: str) -> None:
    cfg = _BOOTSTRAP_USERS[username]
    with ui.connect() as conn:
        conn.execute(
            "UPDATE users SET password_salt=?,password_hash=?,must_change_password=1,failed_attempts=0,locked_until='',updated_at=? WHERE username=?",
            (cfg["salt"], cfg["password_hash"], datetime.now().isoformat(timespec="seconds"), username),
        )
    _audit(ui, "PASSWORD_RESET", f"Senha provisória redefinida para {username}", "usuario", None)


def users_page(ui) -> None:
    st = ui.st
    if st.session_state.get("auth_role") != "ADMIN_TOTAL":
        st.error("Somente os Administradores Principais podem gerenciar usuários.")
        return
    ui.page_header("👤 Usuários e Acessos", "Controle de acesso individual dos quatro sócios, senhas e segurança.")
    with ui.connect() as conn:
        rows = conn.execute("SELECT id,username,display_name,role,is_partner,active,must_change_password,last_login FROM users ORDER BY id").fetchall()
    for row in rows:
        role_label = "Administrador Principal" if row["role"] == "ADMIN_TOTAL" else "Sócio"
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([1.5, 1.2, 1, 1.2])
            c1.markdown(f"**{row['display_name']}**  \n`{row['username']}`")
            c2.write(role_label)
            c3.write("Ativo" if row["active"] else "Bloqueado")
            c4.write("Troca pendente" if row["must_change_password"] else "Senha definida")
            b1, b2 = st.columns(2)
            if b1.button("Redefinir senha provisória", key=f"reset_{row['username']}", use_container_width=True):
                _reset_to_initial(ui, row["username"])
                st.success(f"Senha provisória de {row['display_name']} redefinida. A troca será exigida no próximo acesso.")
                st.rerun()
            cannot_block_self = row["username"] == st.session_state.get("auth_username")
            label = "Ativar usuário" if not row["active"] else "Bloquear usuário"
            if b2.button(label, key=f"active_{row['username']}", disabled=cannot_block_self, use_container_width=True):
                new_value = 0 if row["active"] else 1
                with ui.connect() as conn:
                    conn.execute("UPDATE users SET active=?,updated_at=? WHERE id=?", (new_value, datetime.now().isoformat(timespec="seconds"), row["id"]))
                _audit(ui, "USER_STATUS", f"{row['username']} active={new_value}", "usuario", int(row["id"]))
                st.rerun()


def _secure_sidebar(ui, logo):
    st = ui.st
    pages = [
        "▦  Painel Geral", "◫  Produtos", "♟  Fornecedores", "🛒  Compras", "◈  Estoque",
        "♙  Clientes", "🛍  Vendas", "◉  Financeiro", "▤  Despesas", "▣  Contas a Pagar",
        "▧  Contas a Receber", "▰  Entregas", "▥  Relatórios", "⇩  Importar Planilha",
        "⌕  Auditoria", "◉  Diagnóstico", "☁  Backup",
    ]
    if st.session_state.get("auth_role") == "ADMIN_TOTAL":
        pages.append("👤  Usuários e Acessos")
    mapping = {p: p.split("  ", 1)[1] for p in pages}
    with st.sidebar:
        if logo.exists():
            st.image(str(logo), width=175)
        st.markdown(f"<div class='brand-version'><b>PREMIUM</b><span>v{ui.__version__}</span></div>", unsafe_allow_html=True)
        selected = st.radio("Navegação", pages, label_visibility="collapsed")
        display = st.session_state.get("auth_display_name", st.session_state.get("auth_username", ""))
        role = "Administrador Principal" if st.session_state.get("auth_role") == "ADMIN_TOTAL" else "Sócio"
        st.markdown(f"<div class='user-card'>👤 &nbsp; <b>{display}</b><br><small>{role}</small></div>", unsafe_allow_html=True)
        if st.button("🔐 Alterar minha senha", use_container_width=True, key="sidebar_change_password"):
            st.session_state["show_password_change"] = True
        if st.button("↪ Sair", use_container_width=True, key="sidebar_logout"):
            _logout(ui)
        return mapping[selected]


def _optional_password_dialog(ui) -> None:
    st = ui.st
    if not st.session_state.get("show_password_change"):
        return
    with st.expander("🔐 Alterar minha senha", expanded=True):
        with st.form("kf_optional_password_change"):
            current = st.text_input("Senha atual", type="password", key="opt_cur")
            new = st.text_input("Nova senha", type="password", key="opt_new")
            confirm = st.text_input("Confirmar nova senha", type="password", key="opt_conf")
            c1, c2 = st.columns(2)
            save = c1.form_submit_button("Alterar senha", type="primary", use_container_width=True)
            cancel = c2.form_submit_button("Cancelar", use_container_width=True)
        if save:
            ok, msg = _change_password(ui, st.session_state["auth_username"], current, new, confirm)
            if ok:
                st.session_state["show_password_change"] = False
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        if cancel:
            st.session_state["show_password_change"] = False
            st.rerun()


def install_security(ui) -> None:
    ensure_security_schema(ui)

    def run_secure():
        st = ui.st
        st.set_page_config(page_title=ui.APP_NAME, page_icon="🐟", layout="wide", initial_sidebar_state="expanded")
        st.markdown(ui.PREMIUM_CSS, unsafe_allow_html=True)

        if not st.session_state.get("auth_username"):
            _login_screen(ui)
            return

        row = _load_user(ui, st.session_state.get("auth_username"))
        if not row or not int(row["active"] or 0):
            for key in ["auth_username", "auth_display_name", "auth_role", "auth_must_change"]:
                st.session_state.pop(key, None)
            st.warning("Seu acesso não está ativo.")
            _login_screen(ui)
            return

        st.session_state["auth_display_name"] = row["display_name"]
        st.session_state["auth_role"] = row["role"]
        st.session_state["auth_must_change"] = bool(row["must_change_password"])
        if st.session_state["auth_must_change"]:
            _mandatory_password_screen(ui)
            return

        _, logo = ui._bootstrap()
        ui.sidebar = lambda current_logo: _secure_sidebar(ui, current_logo)
        page = ui.sidebar(logo)
        _optional_password_dialog(ui)

        display = st.session_state.get("auth_display_name", "")
        role_label = "Administrador Principal" if st.session_state.get("auth_role") == "ADMIN_TOTAL" else "Sócio"
        st.markdown(
            f"<style>.footerbar span:first-child{{font-size:0}}.footerbar span:first-child::after{{content:'👤 Usuário: {display}';font-size:14px}}"
            f".footerbar span:nth-child(2){{font-size:0}}.footerbar span:nth-child(2)::after{{content:'♙ Perfil: {role_label}';font-size:14px}}</style>",
            unsafe_allow_html=True,
        )

        if page == "Painel Geral": ui.painel()
        elif page == "Produtos": ui.produtos()
        elif page == "Fornecedores": ui.fornecedores()
        elif page == "Clientes": ui.clientes()
        elif page == "Compras": ui.compras()
        elif page == "Vendas": ui.vendas()
        elif page == "Estoque": ui.estoque()
        elif page == "Financeiro": ui.simple_page("💰 Financeiro", "Entradas e saídas realizadas.", "financeiro", "SELECT id,data,tipo,categoria,descricao,valor,forma_pagamento,origem,origem_id FROM financeiro ORDER BY data DESC,id DESC", ["data","tipo","categoria","descricao","valor","forma_pagamento","origem","origem_id"])
        elif page == "Despesas": ui.simple_page("🧾 Despesas", "Custos e despesas operacionais.", "despesas", "SELECT id,data,categoria,descricao,valor,forma_pagamento,pago,fornecedor,observacao FROM despesas ORDER BY data DESC,id DESC", ["data","categoria","descricao","valor","forma_pagamento","pago","fornecedor","observacao"])
        elif page == "Contas a Pagar": ui.simple_page("📤 Contas a Pagar", "Obrigações pendentes e pagas.", "contas_pagar", "SELECT id,descricao,fornecedor,valor_total,valor_pago,vencimento,status,forma_pagamento,origem,origem_id FROM contas_pagar ORDER BY status,vencimento", ["descricao","fornecedor","valor_total","valor_pago","vencimento","status","forma_pagamento"])
        elif page == "Contas a Receber": ui.simple_page("📥 Contas a Receber", "Recebíveis de vendas a prazo ou parcialmente pagas.", "contas_receber", "SELECT id,descricao,cliente,valor_total,valor_recebido,vencimento,status,forma_pagamento,origem,origem_id FROM contas_receber ORDER BY status,vencimento", ["descricao","cliente","valor_total","valor_recebido","vencimento","status","forma_pagamento"])
        elif page == "Entregas":
            # A camada de CEP já substituiu ui.run; reaproveitamos a função de página instalada via simple dispatcher.
            from .cep_ui import _entregas
            _entregas(ui)
        elif page == "Relatórios": ui.relatorios()
        elif page == "Importar Planilha": ui.importar()
        elif page == "Auditoria": ui.auditoria()
        elif page == "Diagnóstico": ui.diagnostico()
        elif page == "Backup": ui.backup()
        elif page == "Usuários e Acessos": users_page(ui)

    ui.run = run_secure
    ui.users_page = lambda: users_page(ui)
