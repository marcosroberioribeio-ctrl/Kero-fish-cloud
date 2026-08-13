import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# CONFIGURAÃ‡ÃƒO DA PÃGINA
# ==========================================
st.set_page_config(
    page_title="Kero Fish - ERP de GestÃ£o",
    page_icon="ðŸŸ",
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

    # Tabela de Termos/Checklist de SeguranÃ§a
    c.execute('''
        CREATE TABLE IF NOT EXISTS checklists_seguranca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            responsavel TEXT,
            temperatura_freezer REAL,
            higiene_ok TEXT,
            data_registro TEXT
        )
    ''')

    # Carga Inicial de Produtos PadrÃ£o da Kero Fish
    produtos_iniciais = [
        ("CamarÃ£o P", "CamarÃ£o", "kg", 0.0),
        ("CamarÃ£o M", "CamarÃ£o", "kg", 0.0),
        ("CamarÃ£o G", "CamarÃ£o", "kg", 0.0),
        ("CamarÃ£o GG", "CamarÃ£o", "kg", 0.0),
        ("Pargo", "Peixe", "kg", 0.0),
        ("SalmÃ£o", "Peixe", "kg", 0.0),
        ("TilÃ¡pia", "Peixe", "kg", 0.0),
        ("Atum", "Peixe", "kg", 0.0),
        ("Sardinha", "Peixe", "kg", 0.0),
        ("Castanha de Caju", "Produtos Regionais", "un/kg", 0.0),
        ("CajuÃ­na", "Produtos Regionais", "garrafa", 0.0),
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
    st.sidebar.title("ðŸŸ Kero Fish")

st.sidebar.title("Kero Fish ERP")
st.sidebar.caption("Sistema Integrado de GestÃ£o Comercial")

menu = st.sidebar.radio(
    "MÃ³dulos do Sistema",
    [
        "ðŸ“Š Dashboard", 
        "ðŸ‘¥ Cadastros", 
        "ðŸ“¦ Controle de Estoque", 
        "ðŸ›’ Vendas & DevoluÃ§Ãµes", 
        "ðŸ’° Financeiro & Despesas",
        "ðŸ›¡ï¸ SeguranÃ§a & Boas PrÃ¡ticas"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Atendimento / Vendas:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("**Instagram:** [@kerofish](https://instagram.com/kerofish)")

# ==========================================
# MÃ“DULO 1: DASHBOARD GERENCIAL
# ==========================================
if menu == "ðŸ“Š Dashboard":
    st.title("ðŸ“Š Painel de Controle Gerencial")
    st.caption("VisÃ£o geral em tempo real da performance do seu negÃ³cio.")
    st.markdown("---")

    conn = get_connection()
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    df_despesas = pd.read_sql_query("SELECT * FROM despesas", conn)
    df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()

    faturamento_bruto = df_vendas[df_vendas['tipo_operacao'] == 'Venda']['valor_total'].sum() if not df_vendas.empty else 0.0
    devolucoes_total = abs(df_vendas[df_vendas['tipo_operacao'] == 'DevoluÃ§Ã£o']['valor_total'].sum()) if not df_vendas.empty else 0.0
    faturamento_liquido = faturamento_bruto - devolucoes_total
    total_despesas = df_despesas['valor'].sum() if not df_despesas.empty else 0.0
    lucro_liquido = faturamento_liquido - total_despesas

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento LÃ­quido", f"R$ {faturamento_liquido:,.2f}")
    col2.metric("Total de Despesas", f"R$ {total_despesas:,.2f}")
    col3.metric("Lucro LÃ­quido Real", f"R$ {lucro_liquido:,.2f}")
    col4.metric("Base de Clientes", len(df_clientes))

    st.markdown("---")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("ðŸ›’ Ãšltimas Vendas Realizadas")
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
            st.info("Nenhuma venda cadastrada atÃ© o momento.")

    with col_g2:
        st.subheader("âš ï¸ Resumo Geral de Vendas por Categoria")
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
            st.info("Aguardando primeiros lanÃ§amentos comerciais.")

# ==========================================
# MÃ“DULO 2: CADASTROS GERAIS
# ==========================================
elif menu == "ðŸ‘¥ Cadastros":
    st.title("ðŸ‘¥ GestÃ£o de Cadastros")
    st.markdown("---")

    tab1, tab2 = st.tabs(["ðŸ‘¤ Cadastrar Cliente", "ðŸ·ï¸ Cadastrar Novo Produto"])

    with tab1:
        st.subheader("Novo Cliente")
        with st.form("form_novo_cliente", clear_on_submit=True):
            col_c1, col_c2, col_c3 = st.columns(3)
            nome_cli = col_c1.text_input("Nome / RazÃ£o Social *")
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
            cat_prod = col_p2.selectbox("Categoria", ["CamarÃ£o", "Peixe", "Produtos Regionais", "Outros"])
            unid_prod = col_p3.selectbox("Unidade de Medida", ["kg", "unidade", "garrafa", "pacote", "caixa"])
            preco_padrao = col_p4.number_input("PreÃ§o Sugerido (R$)", min_value=0.0, step=1.0)
            
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
                    except Exception as e:
                        st.error("Erro: Produto com esse nome jÃ¡ existe.")
                else:
                    st.error("Informe o nome do produto.")

        st.markdown("---")
        st.subheader("Produtos no CatÃ¡logo")
        conn = get_connection()
        df_p = pd.read_sql_query("SELECT id as ID, nome as Produto, categoria as Categoria, unidade as Unidade, preco_padrao as 'PreÃ§o Sugerido (R$)' FROM produtos ORDER BY categoria, nome", conn)
        conn.close()
        st.dataframe(df_p, use_container_width=True)

# ==========================================
# MÃ“DULO 3: CONTROLE DE ESTOQUE
# ==========================================
elif menu == "ðŸ“¦ Controle de Estoque":
    st.title("ðŸ“¦ Controle de Estoque e Almoxarifado")
    st.markdown("---")

    conn = get_connection()
    df_produtos = pd.read_sql_query("SELECT id, nome, unidade FROM produtos ORDER BY nome", conn)
    conn.close()

    dict_produtos = {row['nome']: row['id'] for _, row in df_produtos.iterrows()}

    st.subheader("ðŸ“¥ Entrada / Ajuste Manual de Estoque")
    with st.form("form_estoque", clear_on_submit=True):
        col_e1, col_e2, col_e3, col_e4 = st.columns(4)
        prod_selecionado = col_e1.selectbox("Produto", list(dict_produtos.keys()))
        tipo_mov = col_e2.selectbox("Tipo de MovimentaÃ§Ã£o", ["Entrada (Compra / ProduÃ§Ã£o)", "SaÃ­da (Perda / Avaria / Ajuste)"])
        qtd_mov = col_e3.number_input("Quantidade", min_value=0.1, step=0.5)
        obs_mov = col_e4.text_input("ObservaÃ§Ã£o / Fornecedor")

        btn_est = st.form_submit_button("Registrar MovimentaÃ§Ã£o")
        if btn_est:
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
            st.success(f"MovimentaÃ§Ã£o de {qtd_mov} em '{prod_selecionado}' registrada com sucesso!")

    st.markdown("---")
    st.subheader("ðŸ“Š Saldo Atual e PosiÃ§Ã£o do Estoque Real")

    conn = get_connection()
    query_saldo = """
        SELECT 
            p.nome as Produto,
            p.categoria as Categoria,
            p.unidade as Unidade,
            COALESCE(SUM(e.quantidade), 0) as 'Entradas/Ajustes',
            COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'Venda'), 0) -
            COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'DevoluÃ§Ã£o'), 0) as 'Total Vendido',
            (COALESCE(SUM(e.quantidade), 0) - 
            (COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'Venda'), 0) -
             COALESCE((SELECT SUM(v.quantidade) FROM vendas v WHERE v.produto_id = p.id AND v.tipo_operacao = 'DevoluÃ§Ã£o'), 0))) as 'Saldo Atual'
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
elif menu == "ðŸ›’ Vendas & DevoluÃ§Ãµes":
    st.title("ðŸ›’ Frente de Vendas e DevoluÃ§Ãµes")
    st.markdown("---")

    conn = get_connection()
    df_cli = pd.read_sql_query("SELECT id, nome FROM clientes ORDER BY nome", conn)
    df_prod = pd.read_sql_query("SELECT id, nome, preco_padrao FROM produtos ORDER BY nome", conn)
    conn.close()

    dict_cli = {row['nome']: row['id'] for _, row in df_cli.iterrows()}
    dict_cli["Cliente Avulso / BalcÃ£o"] = None
    dict_prod = {row['nome']: (row['id'], row['preco_padrao']) for _, row in df_prod.iterrows()}

    tab_venda, tab_devolucao = st.tabs(["ðŸ›’ LanÃ§ar Nova Venda", "ðŸ”„ Registrar DevoluÃ§Ã£o / Estorno"])

    with tab_venda:
        with st.form("form_venda", clear_on_submit=True):
            col_v1, col_v2 = st.columns(2)
            cli_sel = col_v1.selectbox("Cliente", list(dict_cli.keys()))
            prod_sel = col_v2.selectbox("Produto Vendido", list(dict_prod.keys()))

            col_v3, col_v4 = st.columns(2)
            qtd_venda = col_v3.number_input("Quantidade Vendida", min_value=0.1, step=0.5)
            preco_sugerido = dict_prod[prod_sel][1] if prod_sel in dict_prod else 0.0
            preco_unit = col_v4.number_input("PreÃ§o UnitÃ¡rio / kg (R$)", min_value=0.0, value=float(preco_sugerido), step=1.0)

            sub_venda = st.form_submit_button("Finalizar e Registrar Venda")
            if sub_venda:
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
        st.info("A devoluÃ§Ã£o abate o valor faturado do sistema e retorna a mercadoria para o saldo de estoque.")
        with st.form("form_dev", clear_on_submit=True):
            col_d1, col_d2 = st.columns(2)
            cli_dev_sel = col_d1.selectbox("Cliente que Devolveu", list(dict_cli.keys()), key="dev_cli")
            prod_dev_sel = col_d2.selectbox("Produto Devolvido", list(dict_prod.keys()), key="dev_prod")

            col_d3, col_d4 = st.columns(2)
            qtd_dev = col_d3.number_input("Quantidade Devolvida", min_value=0.1, step=0.5)
            valor_dev = col_d4.number_input("Valor Total Estornado (R$)", min_value=0.0, step=1.0)

            sub_dev = st.form_submit_button("Confirmar Estorno / DevoluÃ§Ã£o")
            if sub_dev:
                prod_id = dict_prod[prod_dev_sel][0]
                cli_id = dict_cli[cli_dev_sel]
                data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                conn = get_connection()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO vendas (tipo_operacao, cliente_id, produto_id, quantidade, valor_unitario, valor_total, data_venda)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("DevoluÃ§Ã£o", cli_id, prod_id, qtd_dev, 0, -valor_dev, data_hoje))
                conn.commit()
                conn.close()

                st.warning(f"DevoluÃ§Ã£o de R$ {valor_dev:,.2f} em '{prod_dev_sel}' registrada!")

    st.markdown("---")
    st.subheader("ðŸ“‹ HistÃ³rico Comercial Recente")
    conn = get_connection()
    df_hist_vendas = pd.read_sql_query("""
        SELECT 
            v.id as 'ID',
            v.data_venda as 'Data/Hora',
            v.tipo_operacao as 'OperaÃ§Ã£o',
            COALESCE(c.nome, 'Cliente Avulso') as 'Cliente',
            p.nome as 'Produto',
            v.quantidade as 'Qtd',
            v.valor_unitario as 'PreÃ§o Un. (R$)',
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
elif menu == "ðŸ’° Financeiro & Despesas":
    st.title("ðŸ’° GestÃ£o Financeira e Fluxo de Caixa")
    st.markdown("---")

    tab_f1, tab_f2 = st.tabs(["ðŸ’¸ Registrar Despesa / Custo", "ðŸ“Š RelatÃ³rio Financeiro & ExportaÃ§Ã£o"])

    with tab_f1:
        st.subheader("LanÃ§amento de Despesas Operacionais (Embalagem, Frete, Energia, etc.)")
        with st.form("form_despesa", clear_on_submit=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            desc_desp = col_f1.text_input("DescriÃ§Ã£o da Despesa *")
            cat_desp = col_f2.selectbox("Categoria", ["Frete / Transporte", "Embalagem", "Energia / Ãgua", "Insumos", "SalÃ¡rios / Pro-labore", "Outros"])
            valor_desp = col_f3.number_input("Valor da Despesa (R$)", min_value=0.1, step=5.0)

            sub_desp = st.form_submit_button("LanÃ§ar Despesa")
            if sub_desp:
                if desc_desp:
                    data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO despesas (descricao, categoria, valor, data_despesa) VALUES (?, ?, ?, ?)",
                              (desc_desp, cat_desp, valor_desp, data_hoje))
                    conn.commit()
                    conn.close()
                    st.success(f"Despesa '{desc_desp}' de R$ {valor_desp:,.2f} lanÃ§ada!")
                else:
                    st.error("Informe a descriÃ§Ã£o da despesa.")

    with tab_f2:
        st.subheader("RelatÃ³rio de SaÃ­das e Custos")
        conn = get_connection()
        df_despesas_lista = pd.read_sql_query("SELECT id as ID, data_despesa as Data, descricao as DescriÃ§Ã£o, categoria as Categoria, valor as 'Valor (R$)' FROM despesas ORDER BY id DESC", conn)
        conn.close()

        st.dataframe(df_despesas_lista, use_container_width=True)

        if not df_despesas_lista.empty:
            csv = df_despesas_lista.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="ðŸ“¥ Baixar RelatÃ³rio de Despesas (CSV/Excel)",
                data=csv,
                file_name="despesas_kerofish.csv",
                mime="text/csv"
            )

# ==========================================
# MÃ“DULO 6: SEGURANÃ‡A & BOAS PRÃTICAS
# ==========================================
elif menu == "ðŸ›¡ï¸ SeguranÃ§a & Boas PrÃ¡ticas":
    st.title("ðŸ›¡ï¸ SeguranÃ§a, Boas PrÃ¡ticas & Higiene")
    st.caption("OrientaÃ§Ãµes tÃ©cnicas de conservaÃ§Ã£o de pescados e controle diÃ¡rio de rotina.")
    st.markdown("---")

    tab_s1, tab_s2, tab_s3 = st.tabs([
        "â„ï¸ ConservaÃ§Ã£o & Higiene dos Pescados", 
        "ðŸ”’ SeguranÃ§a dos Dados & Backup", 
        "ðŸ“‹ Checklist DiÃ¡rio de Qualidade"
    ])

    with tab_s1:
        st.subheader("ðŸ§Š Boas PrÃ¡ticas de ConservaÃ§Ã£o (CamarÃ£o e Peixes)")
        st.markdown("""
        - **Cadeia do Frio:** O camarÃ£o e peixes frescos devem ser mantidos sempre entre **0Â°C e 4Â°C** ou congelados a **-18Â°C ou mais frio**.
        - **Evitar ContaminaÃ§Ã£o Cruzada:** Nunca armazene produtos brutos/sujos junto com produtos prontos para consumo.
        - **Regra FIFO / PEPS:** *Primeiro que Entra, Primeiro que Sai*. Venda sempre o lote mais antigo primeiro.
        - **Higiene dos UtensÃ­lios:** Lave e sanitize caixas tÃ©rmicas, balanÃ§as e facas a cada troca de lote ou inÃ­cio de expediente.
        """)

    with tab_s2:
        st.subheader("ðŸ” SeguranÃ§a da InformaÃ§Ã£o e Backup")
        st.markdown("""
        - **Backup Semanal:** Como os dados ficam salvos em arquivo interno, exporte o relatÃ³rio da aba **Financeiro** ao menos uma vez por semana.
        - **Privacidade dos Clientes:** Mantenha os dados de telefone e endereÃ§o protegidos para uso exclusivo de vendas da Kero Fish.
        - **Acesso Limitado:** NÃ£o forneÃ§a o link de ediÃ§Ã£o do sistema para terceiros.
        """)

    with tab_s3:
        st.subheader("ðŸ“ Registrar Controle de Qualidade DiÃ¡rio")
        with st.form("form_checklist", clear_on_submit=True):
            col_k1, col_k2, col_k3 = st.columns(3)
            resp = col_k1.text_input("ResponsÃ¡vel pela Checagem")
            temp = col_k2.number_input("Temperatura do Freezer (Â°C)", value=-18.0, step=1.0)
            hig_ok = col_k3.selectbox("Higiene das Caixas/Freezers OK?", ["Sim", "NÃ£o"])

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
                    st.success("Registro de qualidade e seguranÃ§a salvo com sucesso!")
                else:
                    st.error("Informe o nome do responsÃ¡vel.")

        st.markdown("---")
        st.subheader("HistÃ³rico de Registros de Qualidade")
        conn = get_connection()
        df_chk = pd.read_sql_query("SELECT id as ID, data_registro as 'Data/Hora', responsavel as ResponsÃ¡vel, temperatura_freezer as 'Temp (Â°C)', higiene_ok as 'Higiene OK' FROM checklists_seguranca ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(df_chk, use_container_width=True)
    
 
