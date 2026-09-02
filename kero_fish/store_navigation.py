from __future__ import annotations


def install_store_navigation(ui) -> None:
    """Acopla Pedidos Online ao menu autenticado sem alterar o núcleo de segurança."""
    from . import security

    original_reports = ui.relatorios

    def reports_or_online():
        if ui.st.session_state.get("_kf_store_online_selected"):
            return ui.pedidos_online()
        return original_reports()

    ui.relatorios = reports_or_online

    def store_sidebar(bound_ui, logo):
        st = bound_ui.st
        with bound_ui.connect() as conn:
            try:
                new_count = int(conn.execute("SELECT COUNT(*) FROM pedidos_online WHERE status='NOVO'").fetchone()[0] or 0)
            except Exception:
                new_count = 0

        online_label = f"🌐  Pedidos Online ({new_count})" if new_count else "🌐  Pedidos Online"
        pages = [
            "▦  Painel Geral", "🌐  " + online_label.split("  ", 1)[1],
            "◫  Produtos", "♟  Fornecedores", "🛒  Compras", "◈  Estoque",
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
            st.markdown(
                f"<div class='brand-version'><b>PREMIUM</b><span>v{bound_ui.__version__}</span></div>",
                unsafe_allow_html=True,
            )
            selected = st.radio("Navegação", pages, label_visibility="collapsed")
            display = st.session_state.get("auth_display_name", st.session_state.get("auth_username", ""))
            role = "Administrador Principal" if st.session_state.get("auth_role") == "ADMIN_TOTAL" else "Sócio"
            st.markdown(
                f"<div class='user-card'>👤 &nbsp; <b>{display}</b><br><small>{role}</small></div>",
                unsafe_allow_html=True,
            )
            if st.button("🔐 Alterar minha senha", use_container_width=True, key="sidebar_change_password"):
                st.session_state["show_password_change"] = True
            if st.button("↪ Sair", use_container_width=True, key="sidebar_logout"):
                security._logout(bound_ui)

        chosen = mapping[selected]
        is_online = chosen.startswith("Pedidos Online")
        st.session_state["_kf_store_online_selected"] = is_online
        return "Relatórios" if is_online else chosen

    security._secure_sidebar = store_sidebar
