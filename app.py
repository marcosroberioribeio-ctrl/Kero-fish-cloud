import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ==========================================
# CONFIGURAÃ‡ÃƒO DA PÃGINA E CONTROLE DE ACESSO
# ==========================================
st.set_page_config(
    page_title="Kero Fish - ERP de GestÃ£o",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir a senha de acesso (pode alterar "1234" para a senha que desejar)
SENHA_CORRETA = "1234"

def checar_senha():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.markdown("<h2 style='text-align: center;'>ðŸ”’ Acesso Restrito - Kero Fish</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            senha_digitada = st.text_input("Digite a senha de acesso:", type="password")
            if st.button("Entrar", use_container_width=True):
                if senha_digitada == SENHA_CORRETA:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        return False
    return True

if checar_senha():
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
        
        # Tabela de Produtos / Pescados
        c.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT,
                preco_kg REAL,
                estoque_kg REAL
            )
        ''')
        
        # Tabela de Vendas
        c.execute('''
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT,
                produto TEXT,
                qtd_kg REAL,
                valor_total REAL,
                data_venda TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    init_db()

    # ==========================================
    # MENU LATERAL / NAVEGAÃ‡ÃƒO
    # ==========================================
    st.sidebar.title("ðŸŸ Kero Fish ERP")
    st.sidebar.markdown("---")
    
    opcao = st.sidebar.radio(
        "NavegaÃ§Ã£o",
        ["ðŸ“Š Dashboard", "ðŸ‘¥ Clientes", "ðŸ“¦ Estoque de Pescados", "ðŸ’° Vendas", "ðŸšª Sair"]
    )

    if opcao == "ðŸšª Sair":
        st.session_state.autenticado = False
        st.rerun()

    # ==========================================
    # PAINEL 1: DASHBOARD
    # ==========================================
    if opcao == "ðŸ“Š Dashboard":
        st.title("ðŸ“Š Painel Geral de GestÃ£o")
        st.markdown("VisualizaÃ§Ã£o rÃ¡pida do desempenho do seu negÃ³cio.")
        
        conn = sqlite3.connect("kerofish.db")
        df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
        df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
        df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
        conn.close()
        
        total_faturado = df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
        total_vendas = len(df_vendas)
        total_clientes = len(df_clientes)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {total_faturado:,.2f}")
        col2.metric("Total de Vendas", f"{total_vendas}")
        col3.metric("Clientes Cadastrados", f"{total_clientes}")
        
        st.markdown("---")
        if not df_vendas.empty:
            st.subheader("Ãšltimas Vendas Realizadas")
            st.dataframe(df_vendas.tail(10), use_container_width=True)
        else:
            st.info("Nenhuma venda registrada atÃ© o momento.")

    # ==========================================
    # PAINEL 2: CLIENTES
    # ==========================================
    elif opcao == "ðŸ‘¥ Clientes":
        st.title("ðŸ‘¥ GestÃ£o de Clientes")
        
        with st.form("form_cliente", clear_on_submit=True):
            st.subheader("Cadastrar Novo Cliente")
            nome = st.text_input("Nome Completo / RazÃ£o Social")
            telefone = st.text_input("Telefone / WhatsApp")
            cidade = st.text_input("Cidade")
            salvar = st.form_submit_button("Cadastrar Cliente")
            
            if salvar:
                if nome.strip():
                    conn = sqlite3.connect("kerofish.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)",
                              (nome, telefone, cidade, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                else:
                    st.warning("O nome do cliente Ã© obrigatÃ³rio.")
                    
        st.markdown("---")
        st.subheader("Lista de Clientes Cadastrados")
        conn = sqlite3.connect("kerofish.db")
        df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
        conn.close()
        st.dataframe(df_clientes, use_container_width=True)

    # ==========================================
    # PAINEL 3: ESTOQUE DE PESCADOS
    # ==========================================
    elif opcao == "ðŸ“¦ Estoque de Pescados":
        st.title("ðŸ“¦ Controle de Estoque")
        
        with st.form("form_produto", clear_on_submit=True):
            st.subheader("Cadastrar Novo Pescado/Produto")
            nome_p = st.text_input("Nome do Pescado (ex: TilÃ¡pia, CamarÃ£o, Tambaqui)")
            categoria = st.selectbox("Categoria", ["Peixe Inteiro", "FilÃ©", "Fruto do Mar", "Outros"])
            preco_kg = st.number_input("PreÃ§o por KG (R$)", min_value=0.0, format="%.2f")
            estoque_kg = st.number_input("Quantidade Inicial em Estoque (KG)", min_value=0.0, format="%.2f")
            salvar_p = st.form_submit_button("Cadastrar no Estoque")
            
            if salvar_p:
                if nome_p.strip():
                    conn = sqlite3.connect("kerofish.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)",
                              (nome_p, categoria, preco_kg, estoque_kg))
                    conn.commit()
                    conn.close()
                    st.success(f"Produto '{nome_p}' cadastrado no estoque!")
                else:
                    st.warning("O nome do produto Ã© obrigatÃ³rio.")
                    
        st.markdown("---")
        st.subheader("Estoque Atual")
        conn = sqlite3.connect("kerofish.db")
        df_prod = pd.read_sql_query("SELECT * FROM produtos", conn)
        conn.close()
        st.dataframe(df_prod, use_container_width=True)

    # ==========================================
    # PAINEL 4: VENDAS
    # ==========================================
    elif opcao == "ðŸ’° Vendas":
        st.title("ðŸ’° Registrar Venda")
        
        conn = sqlite3.connect("kerofish.db")
        df_c = pd.read_sql_query("SELECT nome FROM clientes", conn)
        df_p = pd.read_sql_query("SELECT id, nome, preco_kg, estoque_kg FROM produtos", conn)
        conn.close()
        
        lista_clientes = df_c["nome"].tolist() if not df_c.empty else []
        lista_produtos = df_p["nome"].tolist() if not df_p.empty else []
        
        if not lista_clientes or not lista_produtos:
            st.warning("Para registrar uma venda, vocÃª precisa ter pelo menos 1 cliente e 1 produto cadastrados.")
        else:
            with st.form("form_venda", clear_on_submit=True):
                cliente_sel = st.selectbox("Selecione o Cliente", lista_clientes)
                produto_sel = st.selectbox("Selecione o Pescado", lista_produtos)
                qtd_kg = st.number_input("Quantidade Vendida (KG)", min_value=0.1, format="%.2f")
                
                prod_info = df_p[df_p["nome"] == produto_sel].iloc[0]
                preco_unit = prod_info["preco_kg"]
                valor_calculado = qtd_kg * preco_unit
                
                st.info(f"PreÃ§o UnitÃ¡rio: R$ {preco_unit:.2f}/KG | **Valor Total Estimado: R$ {valor_calculado:.2f}**")
                
                finalizar = st.form_submit_button("Confirmar e Registrar Venda")
                
                if finalizar:
                    if qtd_kg > prod_info["estoque_kg"]:
                        st.error(f"Estoque insuficiente! Estoque disponÃ­vel: {prod_info['estoque_kg']} KG.")
                    else:
                        conn = sqlite3.connect("kerofish.db")
                        c = conn.cursor()
                        # Registrar venda
                        c.execute("INSERT INTO vendas (cliente, produto, qtd_kg, valor_total, data_venda) VALUES (?, ?, ?, ?, ?)",
                                  (cliente_sel, produto_sel, qtd_kg, valor_calculado, datetime.now().strftime("%Y-%m-%d %H:%M")))
                        # Baixar estoque
                        novo_estoque = prod_info["estoque_kg"] - qtd_kg
                        c.execute("UPDATE produtos SET estoque_kg = ? WHERE id = ?", (novo_estoque, prod_info["id"]))
                        conn.commit()
                        conn.close()
                        st.success(f"Venda registrada para {cliente_sel}! Valor: R$ {valor_calculado:.2f}")
