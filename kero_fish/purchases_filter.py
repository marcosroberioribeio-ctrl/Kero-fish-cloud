from __future__ import annotations

from datetime import date


def install_purchases_filter(ui) -> None:
    """Adiciona filtro por mês e ano à listagem de Compras sem alterar o cadastro."""
    st = ui.st

    def compras_filtradas() -> None:
        ui.page_header("📦 Compras", "Entrada de mercadoria integrada ao estoque e ao contas a pagar.")

        # Cadastro de compra preservado exatamente como no fluxo atual.
        with st.form("nova_compra"):
            c1, c2, c3 = st.columns(3)
            data = c1.date_input("Data", date.today())
            fornecedor = c2.text_input("Fornecedor *")
            produto = c3.text_input("Produto *")
            c4, c5, c6 = st.columns(3)
            qtd = c4.number_input("Quantidade", 0.0, step=.01)
            custo = c5.number_input("Custo unitário", 0.0, step=.01)
            pgto = c6.selectbox("Pagamento", ["A prazo", "PIX", "Dinheiro", "Cartão", "Transferência"])
            lote = st.text_input("Lote")
            validade = st.text_input("Validade")
            local = st.text_input("Local de estoque")
            pago = st.checkbox("Compra já paga")
            if st.form_submit_button("Registrar compra", type="primary"):
                try:
                    ui.register_purchase_safe(data.isoformat(), fornecedor, produto, qtd, custo, lote, validade, local, pgto, "Pago" if pago else "Pendente")
                    st.success("Compra registrada, validada e integrada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        st.markdown("### 📅 Consultar compras por período")
        nomes_meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]

        try:
            anos_df = ui.query_df(
                "SELECT DISTINCT CAST(substr(data,1,4) AS INTEGER) ano FROM compras "
                "WHERE length(COALESCE(data,''))>=4 ORDER BY ano DESC"
            )
            anos = [int(a) for a in anos_df["ano"].tolist() if int(a) > 0] if not anos_df.empty else []
        except Exception:
            anos = []
        if date.today().year not in anos:
            anos.insert(0, date.today().year)
        anos = sorted(set(anos), reverse=True)

        f1, f2 = st.columns(2)
        ano = int(f1.selectbox("Ano", anos, index=anos.index(date.today().year) if date.today().year in anos else 0, key="compras_filtro_ano"))
        mes = int(f2.selectbox(
            "Mês",
            list(range(1, 13)),
            index=date.today().month - 1,
            format_func=lambda m: nomes_meses[m - 1],
            key="compras_filtro_mes",
        ))

        ym = f"{ano:04d}-{mes:02d}"
        st.caption(f"Exibindo compras de {nomes_meses[mes-1]}/{ano}")
        sql = (
            "SELECT id,data,fornecedor,produto,quantidade,custo_unitario,total,lote,validade,local_estoque,"
            "forma_pagamento,status_pagamento,vencimento FROM compras "
            f"WHERE substr(data,1,7)='{ym}' ORDER BY data DESC,id DESC"
        )
        ui.editable_grid(
            "compras",
            sql,
            ["data", "fornecedor", "produto", "quantidade", "custo_unitario", "total", "lote", "validade", "local_estoque", "forma_pagamento", "status_pagamento", "vencimento"],
            ["id"],
            f"compras_{ano}_{mes}",
        )

    ui.compras = compras_filtradas
