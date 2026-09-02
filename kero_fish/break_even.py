from __future__ import annotations

from datetime import date


def _money(value: float) -> str:
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _period_values(ui, year: int, month: int) -> tuple[float, float, float, float, int]:
    """Retorna faturamento, CMV, despesas variáveis, fixas e não classificadas."""
    ym = f"{year:04d}-{month:02d}"
    with ui.connect() as conn:
        revenue = conn.execute(
            """
            SELECT COALESCE(SUM(CASE WHEN COALESCE(valor_total,0)<>0 THEN valor_total ELSE COALESCE(total,0) END),0)
            FROM vendas
            WHERE substr(COALESCE(NULLIF(data_venda,''),data),1,7)=?
              AND upper(COALESCE(status_pedido,''))<>'CANCELADO'
            """,
            (ym,),
        ).fetchone()[0]

        cmv = conn.execute(
            """
            SELECT COALESCE(SUM(
                (CASE WHEN COALESCE(v.qtd_kg,0)<>0 THEN v.qtd_kg ELSE COALESCE(v.quantidade,0) END)
                * COALESCE(p.custo_medio,0)
            ),0)
            FROM vendas v
            LEFT JOIN produtos p ON lower(p.nome)=lower(v.produto)
            WHERE substr(COALESCE(NULLIF(v.data_venda,''),v.data),1,7)=?
              AND upper(COALESCE(v.status_pedido,''))<>'CANCELADO'
            """,
            (ym,),
        ).fetchone()[0]

        fixed = conn.execute(
            """
            SELECT COALESCE(SUM(valor),0)
            FROM despesas
            WHERE substr(COALESCE(NULLIF(data_desp,''),data),1,7)=?
              AND tipo_custo='Fixo'
            """,
            (ym,),
        ).fetchone()[0]

        variable_expenses = conn.execute(
            """
            SELECT COALESCE(SUM(valor),0)
            FROM despesas
            WHERE substr(COALESCE(NULLIF(data_desp,''),data),1,7)=?
              AND tipo_custo='Variável'
            """,
            (ym,),
        ).fetchone()[0]

        unclassified = conn.execute(
            """
            SELECT COUNT(*)
            FROM despesas
            WHERE substr(COALESCE(NULLIF(data_desp,''),data),1,7)=?
              AND COALESCE(tipo_custo,'Não classificado') NOT IN ('Fixo','Variável')
            """,
            (ym,),
        ).fetchone()[0]

    return float(revenue or 0), float(cmv or 0), float(variable_expenses or 0), float(fixed or 0), int(unclassified or 0)


def install_break_even(ui) -> None:
    """Acrescenta um painel gerencial de ponto de equilíbrio ao Financeiro."""
    st = ui.st
    original_simple = ui.simple_page

    def simple_with_break_even(title, subtitle, table, sql, editable):
        result = original_simple(title, subtitle, table, sql, editable)
        if table != "financeiro":
            return result

        st.markdown("---")
        st.markdown("### 📊 Ponto de Equilíbrio")
        st.caption(
            "Calculado a partir do faturamento, CMV e despesas classificadas como fixas ou variáveis no ERP. "
            "Os valores continuam editáveis para simulações gerenciais."
        )

        today = date.today()
        c1, c2 = st.columns(2)
        year = int(c1.number_input("Ano", min_value=2020, max_value=2100, value=today.year, step=1, key="be_year"))
        month = int(c2.selectbox(
            "Mês",
            list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda m: ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"][m-1],
            key="be_month",
        ))

        revenue, cmv, variable_expenses, fixed_suggested, unclassified = _period_values(ui, year, month)
        variable_suggested = cmv + variable_expenses

        if unclassified:
            st.warning(
                f"Há {unclassified} despesa(s) ainda sem classificação no período. "
                "Classifique-as em Despesas para aumentar a precisão do ponto de equilíbrio."
            )

        st.markdown("#### Base do cálculo")
        b1, b2, b3 = st.columns(3)
        fixed = float(b1.number_input(
            "Custos/despesas fixas",
            min_value=0.0,
            value=float(fixed_suggested),
            step=100.0,
            format="%.2f",
            key=f"be_fixed_{year}_{month}",
            help="Somatório das despesas classificadas como Fixo no período.",
        ))
        variable = float(b2.number_input(
            "Custos variáveis / CMV",
            min_value=0.0,
            value=float(variable_suggested),
            step=100.0,
            format="%.2f",
            key=f"be_variable_{year}_{month}",
            help="CMV das vendas + despesas classificadas como Variável.",
        ))
        revenue_input = float(b3.number_input(
            "Faturamento do período",
            min_value=0.0,
            value=float(revenue),
            step=100.0,
            format="%.2f",
            key=f"be_revenue_{year}_{month}",
        ))

        contribution = revenue_input - variable
        margin_ratio = (contribution / revenue_input) if revenue_input > 0 else 0.0
        break_even = (fixed / margin_ratio) if margin_ratio > 0 else 0.0
        safety = revenue_input - break_even if break_even > 0 else 0.0
        safety_pct = (safety / break_even * 100.0) if break_even > 0 else 0.0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Margem de contribuição", _money(contribution))
        k2.metric("Margem de contribuição %", f"{margin_ratio*100:.1f}%".replace(".", ","))
        k3.metric("Ponto de equilíbrio", _money(break_even) if break_even > 0 else "—")
        k4.metric("Margem de segurança", _money(safety) if break_even > 0 else "—")

        if revenue_input <= 0:
            st.info("Ainda não há faturamento suficiente no período para calcular o ponto de equilíbrio.")
        elif margin_ratio <= 0:
            st.error("A margem de contribuição está zerada ou negativa. Revise preços, CMV e custos variáveis.")
        elif revenue_input >= break_even:
            pct_text = f"{safety_pct:.1f}".replace(".", ",")
            st.success(f"Acima do ponto de equilíbrio em {_money(safety)} ({pct_text}% acima do mínimo necessário).")
        else:
            missing = break_even - revenue_input
            st.warning(f"Faltam {_money(missing)} de faturamento para atingir o ponto de equilíbrio deste período.")

        st.caption(
            "Critério: ponto de equilíbrio = custos fixos ÷ margem de contribuição percentual. "
            "Para uma operação com vários produtos, o indicador em faturamento (R$) é o mais útil para gestão."
        )
        return result

    ui.simple_page = simple_with_break_even
