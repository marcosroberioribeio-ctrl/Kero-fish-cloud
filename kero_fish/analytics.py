from __future__ import annotations

from datetime import date

import pandas as pd


def _money(value) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def install_management_analytics(ui) -> None:
    original_reports = ui.relatorios

    def reports_with_analytics():
        original_reports()
        st = ui.st
        st.markdown("---")
        st.markdown("## 🧠 Análise Executiva")
        st.caption("Leitura gerencial integrada de resultado, caixa, recebíveis, obrigações, margem e estoque.")

        years = []
        with ui.connect() as conn:
            for row in conn.execute("SELECT DISTINCT substr(COALESCE(NULLIF(data_venda,''),data),1,4) ano FROM vendas WHERE COALESCE(NULLIF(data_venda,''),data)<>''"):
                if str(row[0] or "").isdigit():
                    years.append(int(row[0]))
        years = sorted(set(years) | {date.today().year}, reverse=True)
        year = st.selectbox("Ano da análise executiva", years, key="analytics_year")
        start, end = f"{year}-01-01", f"{year}-12-31"

        with ui.connect() as conn:
            revenue = float(conn.execute(
                "SELECT COALESCE(SUM(valor_total),0) FROM vendas WHERE data_venda BETWEEN ? AND ? AND upper(COALESCE(status_pedido,''))<>'CANCELADO'",
                (start,end),
            ).fetchone()[0] or 0)
            orders = int(conn.execute(
                "SELECT COUNT(*) FROM vendas WHERE data_venda BETWEEN ? AND ? AND upper(COALESCE(status_pedido,''))<>'CANCELADO'",
                (start,end),
            ).fetchone()[0] or 0)
            cmv = float(conn.execute(
                """
                SELECT COALESCE(SUM(v.qtd_kg*COALESCE(p.custo_medio,0)),0)
                FROM vendas v LEFT JOIN produtos p ON lower(p.nome)=lower(v.produto)
                WHERE v.data_venda BETWEEN ? AND ? AND upper(COALESCE(v.status_pedido,''))<>'CANCELADO'
                """,
                (start,end),
            ).fetchone()[0] or 0)
            expenses = float(conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM despesas WHERE data_desp BETWEEN ? AND ?",
                (start,end),
            ).fetchone()[0] or 0)
            cash_in = float(conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Entrada' AND data_mov BETWEEN ? AND ?",
                (start,end),
            ).fetchone()[0] or 0)
            cash_out = float(conn.execute(
                "SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Saída' AND data_mov BETWEEN ? AND ?",
                (start,end),
            ).fetchone()[0] or 0)
            recv = float(conn.execute("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_recebido,0),0)),0) FROM contas_receber WHERE status IN ('Pendente','Parcial')").fetchone()[0] or 0)
            pay = float(conn.execute("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_pago,0),0)),0) FROM contas_pagar WHERE status IN ('Pendente','Parcial')").fetchone()[0] or 0)
            overdue_recv = float(conn.execute("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_recebido,0),0)),0) FROM contas_receber WHERE status IN ('Pendente','Parcial') AND vencimento<>'' AND vencimento<?", (date.today().isoformat(),)).fetchone()[0] or 0)
            overdue_pay = float(conn.execute("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_pago,0),0)),0) FROM contas_pagar WHERE status IN ('Pendente','Parcial') AND vencimento<>'' AND vencimento<?", (date.today().isoformat(),)).fetchone()[0] or 0)

            top_clients = pd.read_sql_query(
                """
                SELECT cliente AS Cliente,COUNT(*) AS Pedidos,SUM(valor_total) AS Faturamento
                FROM vendas WHERE data_venda BETWEEN ? AND ? AND upper(COALESCE(status_pedido,''))<>'CANCELADO'
                GROUP BY cliente ORDER BY SUM(valor_total) DESC LIMIT 10
                """,
                conn, params=(start,end),
            )
            low_margin = pd.read_sql_query(
                """
                SELECT nome AS Produto,categoria AS Categoria,custo_medio AS Custo,preco_venda AS Venda,
                       (preco_venda-custo_medio) AS Margem
                FROM produtos WHERE ativo=1 AND preco_venda>0
                ORDER BY (preco_venda-custo_medio) ASC LIMIT 10
                """,
                conn,
            )

        gross_profit = revenue - cmv
        gross_margin = (gross_profit / revenue * 100) if revenue else 0.0
        managerial_result = gross_profit - expenses
        ticket = revenue / orders if orders else 0.0
        projected_cash = (cash_in - cash_out) + recv - pay

        k1,k2,k3,k4,k5 = st.columns(5)
        k1.metric("Faturamento", _money(revenue))
        k2.metric("Lucro bruto", _money(gross_profit))
        k3.metric("Margem bruta", f"{gross_margin:.1f}%".replace(".",","))
        k4.metric("Resultado gerencial", _money(managerial_result))
        k5.metric("Ticket médio", _money(ticket))

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Saldo realizado", _money(cash_in-cash_out))
        c2.metric("Receber em aberto", _money(recv))
        c3.metric("Pagar em aberto", _money(pay))
        c4.metric("Caixa projetado", _money(projected_cash))

        if overdue_recv > 0:
            st.warning(f"Recebimentos vencidos em aberto: {_money(overdue_recv)}")
        if overdue_pay > 0:
            st.warning(f"Pagamentos vencidos em aberto: {_money(overdue_pay)}")
        if managerial_result < 0 and revenue > 0:
            st.error("O resultado gerencial do exercício está negativo. Revise preços, CMV e despesas.")
        elif revenue > 0:
            st.success("Resultado gerencial positivo no exercício selecionado.")

        t1,t2,t3 = st.tabs(["DRE gerencial","Clientes","Margens de produtos"])
        with t1:
            dre = pd.DataFrame([
                {"Linha":"Faturamento","Valor":revenue},
                {"Linha":"(-) CMV estimado","Valor":-cmv},
                {"Linha":"Lucro bruto","Valor":gross_profit},
                {"Linha":"(-) Despesas","Valor":-expenses},
                {"Linha":"Resultado gerencial","Valor":managerial_result},
            ])
            dre["Valor"] = dre["Valor"].map(_money)
            st.dataframe(dre, hide_index=True, use_container_width=True)
            st.caption("DRE gerencial simplificada para decisão interna; não substitui escrituração contábil/fiscal.")
        with t2:
            if top_clients.empty:
                st.info("Sem vendas no período.")
            else:
                top_clients["Faturamento"] = top_clients["Faturamento"].map(_money)
                st.dataframe(top_clients, hide_index=True, use_container_width=True)
        with t3:
            if low_margin.empty:
                st.info("Sem produtos ativos com preço cadastrado.")
            else:
                for col in ["Custo","Venda","Margem"]:
                    low_margin[col] = low_margin[col].map(_money)
                st.dataframe(low_margin, hide_index=True, use_container_width=True)

    ui.relatorios = reports_with_analytics
