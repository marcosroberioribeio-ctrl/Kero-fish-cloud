from __future__ import annotations

from datetime import date


def install_sales_filter(ui) -> None:
    """Adiciona filtro por mês e ano à listagem de Vendas sem alterar o cadastro."""
    st = ui.st

    def vendas_filtradas() -> None:
        ui.page_header("🧾 Vendas", "Pedidos com validação de estoque, recebimentos e entregas.")

        # Cadastro de venda preservado exatamente como no fluxo atual.
        with st.form("nova_venda"):
            c1, c2, c3 = st.columns(3)
            data = c1.date_input("Data", date.today())
            cliente = c2.text_input("Cliente *")
            produto = c3.text_input("Produto *")
            c4, c5, c6 = st.columns(3)
            qtd = c4.number_input("Quantidade", 0.0, step=.01)
            preco = c5.number_input("Preço unitário", 0.0, step=.01)
            desc = c6.number_input("Desconto", 0.0, step=.01)
            c7, c8, c9 = st.columns(3)
            forma = c7.selectbox("Pagamento", ["PIX", "Dinheiro", "Cartão", "Transferência", "A prazo"])
            recebido = c8.number_input("Valor recebido", 0.0, step=.01)
            entrega = c9.checkbox("Tem entrega")
            status = st.selectbox("Status do pedido", ["Em preparação", "Aguardando", "Saiu para entrega", "Entregue", "Cancelado"])
            if st.form_submit_button("Registrar venda", type="primary"):
                try:
                    ui.register_sale_safe(data.isoformat(), cliente, produto, qtd, preco, desc, forma, recebido, status, entrega)
                    st.success("Venda registrada, validada e integrada.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        st.markdown("### 📅 Consultar vendas por período")
        nomes_meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]

        try:
            anos_df = ui.query_df(
                "SELECT DISTINCT CAST(substr(COALESCE(NULLIF(data,''),data_venda),1,4) AS INTEGER) ano "
                "FROM vendas WHERE length(COALESCE(NULLIF(data,''),data_venda))>=4 ORDER BY ano DESC"
            )
            anos = [int(a) for a in anos_df["ano"].tolist() if int(a) > 0] if not anos_df.empty else []
        except Exception:
            anos = []
        if date.today().year not in anos:
            anos.insert(0, date.today().year)
        anos = sorted(set(anos), reverse=True)

        f1, f2 = st.columns(2)
        ano = int(f1.selectbox("Ano", anos, index=anos.index(date.today().year) if date.today().year in anos else 0, key="vendas_filtro_ano"))
        mes = int(f2.selectbox(
            "Mês",
            list(range(1, 13)),
            index=date.today().month - 1,
            format_func=lambda m: nomes_meses[m - 1],
            key="vendas_filtro_mes",
        ))

        ym = f"{ano:04d}-{mes:02d}"
        st.caption(f"Exibindo vendas de {nomes_meses[mes-1]}/{ano}")

        sql = (
            "SELECT id,pedido,data,cliente,produto,quantidade,preco_unitario,desconto,total,"
            "forma_pagamento,status_pagamento,valor_recebido,vencimento,status_pedido,entrega "
            "FROM vendas "
            f"WHERE substr(COALESCE(NULLIF(data,''),data_venda),1,7)='{ym}' "
            "ORDER BY data DESC,id DESC"
        )
        ui.editable_grid(
            "vendas",
            sql,
            ["data", "cliente", "produto", "quantidade", "preco_unitario", "desconto", "total", "forma_pagamento", "status_pagamento", "valor_recebido", "vencimento", "status_pedido", "entrega"],
            ["id", "pedido"],
            f"vendas_{ano}_{mes}",
        )

    ui.vendas = vendas_filtradas
