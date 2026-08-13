import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==========================================
# CONFIGURAÃ‡ÃƒO DA PÃGINA
# ==========================================
st.set_page_config(
    page_title="Kero Fish - ERP de Gest\u00e3o",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# BANCO DE DADOS (PERSISTÃŠNCIA SQLITE)
# ==========================================
def init_db():
    conn = sqlite3.connect("kerofish.db")
    c = conn.cursor()
    
    # Tabela de Clientes
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            cidade TEXT,
            data_cad TEXT
        )
    ''')
    
    # Recria a tabela de produtos para apagar textos corrompidos anteriores
    c.execute("DROP TABLE IF EXISTS produtos")
    
    # Tabela de Produtos
    c.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            categoria TEXT NOT NULL,
            unidade TEXT DEFAULT 'kg',
            preco_padrao REAL DEFAULT 0.0
        )
    ''')
    
    # Tabela de Estoque
    c.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            tipo_mov TEXT,
            quantidade REAL,
            observacao TEXT,
            data_mov TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    # Tabela de Vendas e DevoluÃ§Ãµes
    c.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_operacao TEXT,
            cliente_id INTEGER,
            produto_id INTEGER,
            quantidade REAL,
            valor_unitario REAL,
            valor_total REAL,
            data_venda TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')

    # Tabela de Despesas Financeiras
    c.execute('''
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            categoria TEXT,
            valor REAL,
            data_despesa TEXT
        )
    ''')

    # Tabela de Checklists de SeguranÃ§a
    c.execute('''
        CREATE TABLE IF NOT EXISTS checklists_seguranca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            responsavel TEXT,
            temperatura_freezer REAL,
            higiene_ok TEXT,
            data_registro TEXT
        )
    ''')

    # Carga Inicial de Produtos PadrÃ£o da Kero Fish (Com Unicode Protegido)
    produtos_iniciais = [
        ("Camar\u00e3o P", "Camar\u00e3o", "kg", 0.0),
        ("Camar\u00e3o M", "Camar\u00e3o", "kg", 0.0),
        ("Camar\u00e3o G", "Camar\u00e3o", "kg", 0.0),
        ("Camar\u00e3o GG", "Camar\u00e3o", "kg", 0.0),
        ("Pargo", "Peixe", "kg", 0.0),
        ("Salm\u00e3o", "Peixe", "kg", 0.0),
        ("Til\u00e1pia", "Peixe", "kg", 0.0),
        ("Atum", "Peixe", "kg", 0.0),
        ("Sardinha", "Peixe", "kg", 0.0),
        ("Castanha de Caju", "Produtos Regionais", "un/kg", 0.0),
        ("Caju\u00edna", "Produtos Regionais", "garrafa", 0.0),
        ("Temperos", "Produtos Regionais", "pacote", 0.0),
        ("Manteiga da Terra", "Produtos Regionais", "garrafa", 0.0),
        ("Queijo", "Produtos Regionais", "kg", 0.0),
    ]
    for p in produtos_iniciais:
        c.execute("INSERT OR IGNORE INTO produtos (nome, categoria, unidade, preco_padrao) VALUES (?, ?, ?, ?)", p)

    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect("kerofish.db")

# ==========================================
# BARRA LATERAL (NAVEGAÃ‡ÃƒO E IDENTIDADE)
# ==========================================
try:
    st.sidebar.image("Screenshot_20260813_084749_WhatsApp.jpg", use_container_width=True)
except Exception:
    st.sidebar.title("Kero Fish")

st.sidebar.title("Kero Fish ERP")
st.sidebar.caption("Sistema Integrado de Gest\u00e3o Comercial")

menu = st.sidebar.radio(
    "M\u00f3dulos do Sistema",
    [
        "Dashboard", 
        "Cadastros", 
        "Controle de Estoque", 
        "Vendas e Devolu\u00e7\u00f5es", 
        "Financeiro e Despesas",
        "Seguran\u00e7a e Boas Pr\u00e1ticas"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Atendimento / Vendas:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("**Instagram:** @kerofish")

# ==========================================
# MÃ“DULO 1: DASHBOARD GERENCIAL
# ==========================================
if menu == "Dashboard":
    st.title("Painel de Controle Gerencial")
    st.caption("Vis\u00e3o geral em tempo real da performance do seu neg\u00f3cio.")
    st.markdown("---")

    conn = get_connection()
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    df_despesas = pd.read_sql_query("SELECT * FROM despesas", conn)
    df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()

    faturamento_bruto = df_vendas[df_vendas['tipo_operacao'] == 'Venda']['valor_total'].sum() if not df_vendas.empty else 0.0
    devolucoes_total = abs(df_vendas[df_vendas['tipo_operacao'] == 'Devolucao']['valor_total'].sum()) if not df_vendas.empty else 0.0
    faturamento_liquido = faturamento_bruto - devolucoes_total
    total_despesas = df_despesas['valor'].sum() if not df_despesas.empty else 0.0
    lucro_liquido = faturamento_liquido - total_despesas

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento L\u00edquido", f"R$ {faturamento_liquido:,.2f}")
    col2.metric("Total de Despesas", f"R$ {total_despesas:,.2f}")
    col3.metric("Lucro L\u00edquido Real", f"R$ {lucro_liquido:,.2f}")
    col4.metric("Base de Clientes", len(df_clientes))

    st.markdown("---")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("\u00daltimas Vendas Realizadas")
        if not df_vendas.empty:
            conn = get_connection()
            recents = pd.read_sql_query("""
                SELECT v.data_venda as 'Data', c.nome as 'Cliente', p.nome as 'Produto', v.quantidade as 'Qtd', v.valor_total as 'Total (R$)'
                FROM vendas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                LEFT JOIN produtos p ON v.produto_id = p.id
                ORDER BY v.id DESC LIMIT 5
            """, conn)
            conn.close()
            st.dataframe(recents, use_container_width=True)
        else:
            st.info("Nenhuma venda cadastrada at\u00e9 o momento.")

    with col_g2:
        st.subheader("Resumo Geral de Vendas por Categoria")
        if not df_vendas.empty:
            conn = get_connection()
            cat_summary = pd.read_sql_query("""
                SELECT p.categoria as 'Categoria', SUM(v.quantidade) as 'Qtd Vendida (kg/un)', SUM(v.valor_total) as 'Total Faturado (R$)'
                FROM vendas v
                JOIN produtos p ON v.produto_id = p.id
                WHERE v.tipo_operacao = 'Venda'
                GROUP BY p.categoria
            """, conn)
            conn.close()
            st.dataframe(cat_summary, use_container_width=True)
        else:
            st.info("Aguardando primeiros lan\u00e7amentos comerciais.")

# ==========================================
# MÃ“DULO 2: CADASTROS GERAIS
# ==========================================
elif menu == "Cadastros":
    st.title("Gest\u00e3o de Cadastros")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Cadastrar Cliente", "Cadastrar Novo Produto"])

    with tab1:
        st.subheader("Novo Cliente")
        with st.form("form_novo_cliente", clear_on_submit=True):
            col_c1, col_c2, col_c3 = st.columns(3)
            nome_cli = col_c1.text_input("Nome / Raz\u00e3o Social *")
            tel_cli = col_c2.text_input("Telefone / WhatsApp")
            cid_cli = col_c3.text_input("Cidade / Bairro")
            
            submit_cli = st.form_submit_button("Salvar Cliente")
            if submit_cli:
                if nome_cli:
                    conn = get_connection()
                    c = conn.cursor()
                    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)",
                              (nome_cli, tel_cli, cid_cli, data_hoje))
                    conn.commit()
                    conn.close()
                    st.success(f"Cliente '{nome_cli}' cadastrado com sucesso!")
                else:
                    st.error("Informe pelo menos o nome do cliente.")

        st.markdown("---")
        st.subheader("Clientes Cadastrados")
        conn = get_connection()
        df_cli = pd.read_sql_query("SELECT id as ID, nome as Nome, telefone as Telefone, cidade as Cidade, data_cad as 'Data Cadastro' FROM clientes ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_cli, use_container_width=True)

    with tab2:
        st.subheader("Novo Produto")
        with st.form("form_novo_prod", clear_on_submit=True):
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            nome_prod = col_p1.text_input("Nome do Produto *")
            cat_prod = col_p2.selectbox("Categoria", ["Camar\u00e3o", "Peixe", "Produtos Regionais", "Outros"])
            unid_prod = col_p3.selectbox("Unidade de Medida", ["kg", "unidade", "garrafa", "pacote", "caixa"])
            preco_padrao = col_p4.number_input("Pre\u00e7o Sugerido (R$)", min_value=0.0, step=1.0)
            
            submit_prod = st.form_submit_button("Salvar Produto")
            if submit_prod:
                if nome_prod:
                    try:
                        conn = get_connection()
                        c = conn.cursor()
                        c.execute("INSERT INTO produtos (nome, categoria, unidade, preco_padrao) VALUES (?, ?, ?, ?)",
                                  (nome_prod, cat_prod, unid_prod, preco_padrao))
                        conn.commit()
                        conn.close()
                        st.success(f"Produto '{nome_prod}' cadastrado com sucesso!")
                    except Exception:
                        st.error("Erro: Produto com esse nome j\u00e1 existe.")
                else:
                    st.error("Informe o nome do produto.")

        st.markdown("---")
        st.subheader("Produtos no Cat\u00e1logo")
        conn = get_connection()
        df_p = pd.read_sql_query("SELECT id as ID, nome as Produto, categoria as Categoria, unidade as Unidade, preco_padrao as 'Pre\u00e7o Sugerido (R$)' FROM produtos ORDER BY categoria, nome", conn)
        conn.close()
        st.dataframe(df_p, use_container_width=True)

# ==========================================
# MÃ“DULO 3: CONTROLE DE ESTOQUE
# ==========================================
elif menu == "Controle de Estoque":
    st.title("Controle de Estoque e Almoxarifado")
    st.markdown("---")

    conn = get_connection()
    df_produtos = pd.read_sql_query("SELECT id, nome, unidade FROM produtos ORDER BY nome", conn)
    conn.close()

    dict_produtos = {row['nome']: row['id'] for _, row in df_produtos.iterrows()}

    st.subheader("Entrada / Ajuste Manual de Estoque")
    with st.form("form_estoque", clear_on_submit=True):
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        prod_selecionado = col_e1.selectbox("Produto", list(dict_produtos.keys())) if dict_produtos else None
        tipo_mov = col_e2.selectbox("Tipo de Movimenta\u00e7\u00e3o", ["Entrada (Compra / Produ\u00e7\u00e3o)", "Sa\u00edda (Perda / Avaria / Ajuste)"])
        qtd_mov = col_e3.number_input("Quantidade", min_value=0.1, step=0.5)
        obs_mov = col_e4.text_input("Observa\u00e7\u00e3o / Fornecedor")

        btn_est = st.form_submit_button("Registrar Movimenta\u00e7\u00e3o")
        if btn_est and prod_selecionado:
            prod_id = dict_produtos[prod_selecionado]
            fator = 1 if "Entrada" in tipo_mov else -1
            qtd_final = qtd_mov * fator
            data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO estoque (produto_id, tipo_mov, quantidade, observacao, data_mov) VALUES (?, ?, ?, ?, ?)",
                      (prod_id, tipo_mov, qtd_final, obs_mov, data_hoje))
            conn.commit()
            conn.close()
            st.success(f"Movimenta\u00e7\u00e3o de {qtd_mov} em '{prod_selecionado}' registrada com sucesso!")

    st.markdown("---")
    st.subheader("Saldo Atual e Posi\u00e7\u00e3o do Estoque Real")

    conn = get_connection()
    query_saldo = """
        SELECT 
            p.nome as Produto,
            p.categoria as Categoria,
            p.unidade as Unidade,
            COALESCE(SUM(e.quantidade), 0) as 'Entradas/Ajustes',
            COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'Venda'), 0) -
            COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'Devolucao'), 0) as 'Total Vendido',
            (COALESCE(SUM(e.quantidade), 0) - 
            (COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'Venda'), 0) -
             COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'Devolucao'), 0))) as 'Saldo Atual'
        FROM produtos p
        LEFT JOIN estoque e ON p.id = e.produto_id
        GROUP BY p.id
        ORDER BY p.categoria, p.nome
    """
    df_saldo = pd.read_sql_query(query_saldo, conn)
    conn.close()

    st.dataframe(df_saldo, use_container_width=True)

# ==========================================
# MÃ“DULO 4: VENDAS & DEVOLUÃ‡Ã•ES
# ==========================================
elif menu == "Vendas e Devolu\u00e7\u00f5es":
    st.title("Frente de Vendas e Devolu\u00e7\u00f5es")
    st.markdown("---")

    conn = get_connection()
    df_cli = pd.read_sql_query("SELECT id, nome FROM clientes ORDER BY nome", conn)
    df_prod = pd.read_sql_query("SELECT id, nome, preco_padrao FROM produtos ORDER BY nome", conn)
    conn.close()

    dict_cli = {row['nome']: row['id'] for _, row in df_cli.iterrows()}
    dict_cli["Cliente Avulso / Balc\u00e3o"] = None
    dict_prod = {row['nome']: (row['id'], row['preco_padrao']) for _, row in df_prod.iterrows()}

    tab_venda, tab_devolucao = st.tabs(["Lan\u00e7ar Nova Venda", "Registrar Devolu\u00e7\u00e3o / Estorno"])

    with tab_venda:
        with st.form("form_venda", clear_on_submit=True):
            col_v1, col_v2 = st.columns(2)
            cli_sel = col_v1.selectbox("Cliente", list(dict_cli.keys()))
            prod_sel = col_v2.selectbox("Produto Vendido", list(dict_prod.keys())) if dict_prod else None

            col_v3, col_v4 = st.columns(2)
            qtd_venda = col_v3.number_input("Quantidade Vendida", min_value=0.1, step=0.5)
            preco_sugerido = dict_prod[prod_sel][1] if (prod_sel and prod_sel in dict_prod) else 0.0
            preco_unit = col_v4.number_input("Pre\u00e7o Unit\u00e1rio / kg (R$)", min_value=0.0, value=float(preco_sugerido), step=1.0)

            sub_venda = st.form_submit_button("Finalizar e Registrar Venda")
            if sub_venda and prod_sel:
                prod_id = dict_prod[prod_sel][0]
                cli_id = dict_cli[cli_sel]
                valor_total = qtd_venda * preco_unit
                data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO vendas (tipo_operacao, cliente_id, produto_id, quantidade, valor_unitario, valor_total, data_venda)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("Venda", cli_id, prod_id, qtd_venda, preco_unit, valor_total, data_hoje))
                conn.commit()
                conn.close()

                st.success(f"Venda efetuada com sucesso! Total: R$ {valor_total:,.2f}")

    with tab_devolucao:
        st.info("A devolu\u00e7\u00e3o abate o valor faturado do sistema e retorna a mercadoria para o saldo de estoque.")
        with st.form("form_dev", clear_on_submit=True):
            col_d1, col_d2 = st.columns(2)
            cli_dev_sel = col_d1.selectbox("Cliente que Devolveu", list(dict_cli.keys()), key="dev_cli")
            prod_dev_sel = col_d2.selectbox("Produto Devolvido", list(dict_prod.keys()), key="dev_prod") if dict_prod else None

            col_d3, col_d4 = st.columns(2)
            qtd_dev = col_d3.number_input("Quantidade Devolvida", min_value=0.1, step=0.5)
            valor_dev = col_d4.number_input("Valor Total Estornado (R$)", min_value=0.0, step=1.0)

            sub_dev = st.form_submit_button("Confirmar Estorno / Devolu\u00e7\u00e3o")
            if sub_dev and prod_dev_sel:
                prod_id = dict_prod[prod_dev_sel][0]
                cli_id = dict_cli[cli_dev_sel]
                data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO vendas (tipo_operacao, cliente_id, produto_id, quantidade, valor_unitario, valor_total, data_venda)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("Devolucao", cli_id, prod_id, qtd_dev, 0, -valor_dev, data_hoje))
                conn.commit()
                conn.close()

                st.warning(f"Devolu\u00e7\u00e3o de R$ {valor_dev:,.2f} em '{prod_dev_sel}' registrada!")

    st.markdown("---")
    st.subheader("Hist\u00f3rico Comercial Recente")
    conn = get_connection()
    df_hist_vendas = pd.read_sql_query("""
        SELECT 
            v.id as 'ID',
            v.data_venda as 'Data/Hora',
            v.tipo_operacao as 'Opera\u00e7\u00e3o',
            COALESCE(c.nome, 'Cliente Avulso') as 'Cliente',
            p.nome as 'Produto',
            v.quantidade as 'Qtd',
            v.valor_unitario as 'Pre\u00e7o Un. (R$)',
            v.valor_total as 'Valor Total (R$)'
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.id DESC
    """, conn)
    conn.close()
    st.dataframe(df_hist_vendas, use_container_width=True)

# ==========================================
# MÃ“DULO 5: FINANCEIRO & DESPESAS
# ==========================================
elif menu == "Financeiro e Despesas":
    st.title("Gest\u00e3o Financeira e Fluxo de Caixa")
    st.markdown("---")

    tab_f1, tab_f2 = st.tabs(["Registrar Despesa / Custo", "Relat\u00f3rio Financeiro e Exporta\u00e7\u00e3o"])

    with tab_f1:
        st.subheader("Lan\u00e7amento de Despesas Operacionais (Embalagem, Frete, Energia, etc.)")
        with st.form("form_despesa", clear_on_submit=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            desc_desp = col_f1.text_input("Descri\u00e7\u00e3o da Despesa *")
            cat_desp = col_f2.selectbox("Categoria", ["Frete / Transporte", "Embalagem", "Energia / \u00c1gua", "Insumos", "Sal\u00e1rios / Pr\u00f3-labore", "Outros"])
            valor_desp = col_f3.number_input("Valor da Despesa (R$)", min_value=0.1, step=5.0)

            sub_desp = st.form_submit_button("Lan\u00e7ar Despesa")
            if sub_desp:
                if desc_desp:
                    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO despesas (descricao, categoria, valor, data_despesa) VALUES (?, ?, ?, ?)",
                              (desc_desp, cat_desp, valor_desp, data_hoje))
                    conn.commit()
                    conn.close()
                    st.success(f"Despesa '{desc_desp}' de R$ {valor_desp:,.2f} lan\u00e7ada!")
                else:
                    st.error("Informe a descri\u00e7\u00e3o da despesa.")

    with tab_f2:
        st.subheader("Relat\u00f3rio de Sa\u00eddas e Custos")
        conn = get_connection()
        df_despesas_lista = pd.read_sql_query("SELECT id as ID, data_despesa as Data, descricao as Descri\u00e7\u00e3o, categoria as Categoria, valor as 'Valor (R$)' FROM despesas ORDER BY id DESC", conn)
        conn.close()

        st.dataframe(df_despesas_lista, use_container_width=True)

        if not df_despesas_lista.empty:
            csv = df_despesas_lista.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Baixar Relat\u00f3rio de Despesas (CSV/Excel)",
                data=csv,
                file_name="despesas_kerofish.csv",
                mime="text/csv"
            )

# ==========================================
# MÃ“DULO 6: SEGURANÃ‡A & BOAS PRÃTICAS
# ==========================================
elif menu == "Seguran\u00e7a e Boas Pr\u00e1ticas":
    st.title("Seguran\u00e7a, Boas Pr\u00e1ticas e Higiene")
    st.caption("Orienta\u00e7\u00f5es t\u00e9cnicas de conserva\u00e7\u00e3o de pescados e controle di\u00e1rio de rotina.")
    st.markdown("---")

    tab_s1, tab_s2, tab_s3 = st.tabs([
        "Conserva\u00e7\u00e3o e Higiene dos Pescados", 
        "Seguran\u00e7a dos Dados e Backup", 
        "Checklist Di\u00e1rio de Qualidade"
    ])

    with tab_s1:
        st.subheader("Boas Pr\u00e1ticas de Conserva\u00e7\u00e3o (Camar\u00e3o e Peixes)")
        st.markdown("""
        - **Cadeia do Frio:** O camar\u00e3o e peixes frescos devem ser mantidos sempre entre **0\u00b0C e 4\u00b0C** ou congelados a **-18\u00b0C ou mais frio**.
        - **Evitar Contamina\u00e7\u00e3o Cruzada:** Nunca armazene produtos brutos/sujos junto com produtos prontos para consumo.
        - **Regra FIFO / PEPS:** *Primeiro que Entra, Primeiro que Sai*. Venda sempre o lote mais antigo primeiro.
        - **Higiene dos Utens\u00edlios:** Lave e sanitize caixas t\u00e9rmicas, balan\u00e7as e facas a cada troca de lote ou in\u00edcio de expediente.
        """)

    with tab_s2:
        st.subheader("Seguran\u00e7a da Informa\u00e7\u00e3o e Backup")
        st.markdown("""
        - **Backup Semanal:** Como os dados ficam salvos em arquivo interno, exporte o relat\u00f3rio da aba **Financeiro** ao menos uma vez por semana.
        - **Privacidade dos Clientes:** Mantenha os dados de telefone e endere\u00e7o protegidos para uso exclusivo de vendas da Kero Fish.
        - **Acesso Limitado:** N\u00e3o forne\u00e7a o link de edi\u00e7\u00e3o do sistema para terceiros.
        """)

    with tab_s3:
        st.subheader("Registrar Controle de Qualidade Di\u00e1rio")
        with st.form("form_checklist", clear_on_submit=True):
            col_k1, col_k2, col_k3 = st.columns(3)
            resp = col_k1.text_input("Respons\u00e1vel pela Checagem")
            temp = col_k2.number_input("Temperatura do Freezer (\u00b0C)", value=-18.0, step=1.0)
            hig_ok = col_k3.selectbox("Higiene das Caixas/Freezers OK?", ["Sim", "N\u00e3o"])

            sub_chk = st.form_submit_button("Salvar Registro de Qualidade")
            if sub_chk:
                if resp:
                    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO checklists_seguranca (responsavel, temperatura_freezer, higiene_ok, data_registro) VALUES (?, ?, ?, ?)",
                              (resp, temp, hig_ok, data_hoje))
                    conn.commit()
                    conn.close()
                    st.success("Registro de qualidade e seguran\u00e7a salvo com sucesso!")
                else:
                    st.error("Informe o nome do respons\u00e1vel.")

        st.markdown("---")
        st.subheader("Hist\u00f3rico de Registros de Qualidade")
        conn = get_connection()
        df_chk = pd.read_sql_query("SELECT id as ID, data_registro as 'Data/Hora', responsavel as Respons\u00e1vel, temperatura_freezer as 'Temp (\u00b0C)', higiene_ok as 'Higiene OK' FROM checklists_seguranca ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_chk, use_container_width=True)
