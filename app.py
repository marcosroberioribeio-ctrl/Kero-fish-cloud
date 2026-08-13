# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# CONFIGURAÃ‡ÃƒO DA PÃGINA
# ==========================================
st.set_page_config(
    page_title="Kero Fish - ERP de GestÃ£o",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "kerofish.db"

# ==========================================
# BANCO DE DADOS
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Criar tabelas caso nÃ£o existam
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            cidade TEXT,
            data_cad TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            preco_kg REAL,
            estoque_kg REAL
        )
    ''')
    
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

    c.execute('''
        CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            data_mov TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ==========================================
# MENU LATERAL / NAVEGAÃ‡ÃƒO
# ==========================================
st.sidebar.title("Kero Fish ERP")
st.sidebar.markdown("---")

opcao = st.sidebar.radio(
    "NavegaÃ§Ã£o",
    ["Dashboard", "Clientes", "Estoque de Pescados", "Vendas", "Financeiro"]
)

# ==========================================
# PAINEL 1: DASHBOARD
# ==========================================
if opcao == "Dashboard":
    st.title("Painel Geral de GestÃ£o")
    st.markdown("VisualizaÃ§Ã£o rÃ¡pida do desempenho do seu negÃ³cio.")
    
    conn = sqlite3.connect(DB_FILE)
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    total_faturado = df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
    total_vendas = len(df_vendas)
    total_clientes = len(df_clientes)
    
    entradas = df_fin[df_fin["tipo"] == "Entrada"]["valor"].sum() if not df_fin.empty else 0.0
    saidas = df_fin[df_fin["tipo"] == "SaÃ­da"]["valor"].sum() if not df_fin.empty else 0.0
    saldo_caixa = entradas - saidas
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento Vendas", f"R$ {total_faturado:,.2f}")
    col2.metric("Total de Vendas", f"{total_vendas}")
    col3.metric("Clientes Cadastrados", f"{total_clientes}")
    col4.metric("Saldo do Caixa", f"R$ {saldo_caixa:,.2f}")
    
    st.markdown("---")
    if not df_vendas.empty:
        st.subheader("Ãšltimas Vendas Realizadas")
        st.dataframe(df_vendas.tail(10), use_container_width=True)
    else:
        st.info("Nenhuma venda registrada atÃ© o momento.")

# ==========================================
# PAINEL 2: CLIENTES
# ==========================================
elif opcao == "Clientes":
    st.title("GestÃ£o de Clientes")
    
    with st.form("form_cliente", clear_on_submit=True):
        st.subheader("Cadastrar Novo Cliente")
        nome = st.text_input("Nome Completo / RazÃ£o Social")
        telefone = st.text_input("Telefone / WhatsApp")
        cidade = st.text_input("Cidade")
        salvar = st.form_submit_button("Cadastrar Cliente")
        
        if salvar:
            if nome.strip():
                conn = sqlite3.connect(DB_FILE)
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
    conn = sqlite3.connect(DB_FILE)
    df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    st.dataframe(df_clientes, use_container_width=True)

# ==========================================
# PAINEL 3: ESTOQUE DE PESCADOS
# ==========================================
elif opcao == "Estoque de Pescados":
    st.title("Controle de Estoque e Mercadorias")
    
    with st.form("form_produto", clear_on_submit=True):
        st.subheader("Cadastrar Nova Mercadoria / Pescado")
        nome_p = st.text_input("Nome da Mercadoria (ex: TilÃ¡pia, CamarÃ£o, Tambaqui)")
        categoria = st.selectbox("Categoria", ["Peixe Inteiro", "FilÃ©", "Fruto do Mar", "Outros"])
        preco_kg = st.number_input("PreÃ§o por KG (R$)", min_value=0.0, format="%.2f")
        estoque_kg = st.number_input("Quantidade Inicial em Estoque (KG)", min_value=0.0, format="%.2f")
        salvar_p = st.form_submit_button("Cadastrar no Estoque")
        
        if salvar_p:
            if nome_p.strip():
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)",
                          (nome_p, categoria, preco_kg, estoque_kg))
                conn.commit()
                conn.close()
                st.success(f"Mercadoria '{nome_p}' cadastrada com sucesso!")
            else:
                st.warning("O nome da mercadoria Ã© obrigatÃ³rio.")
                
    st.markdown("---")
    st.subheader("Estoque Atual de Mercadorias")
    conn = sqlite3.connect(DB_FILE)
    df_prod = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    st.dataframe(df_prod, use_container_width=True)

# ==========================================
# PAINEL 4: VENDAS
# ==========================================
elif opcao == "Vendas":
    st.title("Registrar Venda")
    
    conn = sqlite3.connect(DB_FILE)
    df_c = pd.read_sql_query("SELECT nome FROM clientes", conn)
    df_p = pd.read_sql_query("SELECT id, nome, preco_kg, estoque_kg FROM produtos", conn)
    conn.close()
    
    lista_clientes = df_c["nome"].tolist() if not df_c.empty else []
    lista_produtos = df_p["nome"].tolist() if not df_p.empty else []
    
    if not lista_clientes or not lista_produtos:
        st.warning("AtenÃ§Ã£o: Para registrar uma venda, vocÃª precisa primeiro cadastrar pelo menos 1 Cliente e 1 Mercadoria no menu ao lado!")
    else:
        with st.form("form_venda", clear_on_submit=True):
            cliente_sel = st.selectbox("Selecione o Cliente", lista_clientes)
            produto_sel = st.selectbox("Selecione a Mercadoria", lista_produtos)
            qtd_kg = st.number_input("Quantidade Vendida (KG)", min_value=0.1, format="%.2f")
            
            prod_info = df_p[df_p["nome"] == produto_sel].iloc[0]
            preco_unit = prod_info["preco_kg"]
            valor_calculado = qtd_kg * preco_unit
            
            st.info(f"PreÃ§o UnitÃ¡rio: R$ {preco_unit:.2f}/KG | Valor Total Estimado: R$ {valor_calculado:.2f}")
            
            finalizar = st.form_submit_button("Confirmar e Registrar Venda")
            
            if finalizar:
                if qtd_kg > prod_info["estoque_kg"]:
                    st.error(f"Estoque insuficiente! DisponÃ­vel: {prod_info['estoque_kg']} KG.")
                else:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    # 1. Registrar Venda
                    c.execute("INSERT INTO vendas (cliente, produto, qtd_kg, valor_total, data_venda) VALUES (?, ?, ?, ?, ?)",
                              (cliente_sel, produto_sel, qtd_kg, valor_calculado, hoje))
                    
                    # 2. Baixar Estoque
                    novo_estoque = prod_info["estoque_kg"] - qtd_kg
                    c.execute("UPDATE produtos SET estoque_kg = ? WHERE id = ?", (novo_estoque, prod_info["id"]))
                    
                    # 3. LanÃ§ar no Financeiro
                    c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)",
                              (f"Venda: {produto_sel} ({cliente_sel})", "Entrada", valor_calculado, hoje))
                    
                    conn.commit()
                    conn.close()
                    st.success("Venda registrada com sucesso!")

# ==========================================
# PAINEL 5: FINANCEIRO
# ==========================================
elif opcao == "Financeiro":
    st.title("Controle Financeiro / Fluxo de Caixa")
    
    with st.form("form_financeiro", clear_on_submit=True):
        st.subheader("LanÃ§amento Manual (Despesas / Entradas)")
        descricao = st.text_input("DescriÃ§Ã£o (ex: Energia, Frete, Fornecedor)")
        tipo = st.selectbox("Tipo de MovimentaÃ§Ã£o", ["SaÃ­da (Despesa)", "Entrada (Receita)"])
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        salvar_fin = st.form_submit_button("Registrar LanÃ§amento")
        
        if salvar_fin:
            if descricao.strip():
                tipo_limpo = "SaÃ­da" if "SaÃ­da" in tipo else "Entrada"
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)",
                          (descricao, tipo_limpo, valor, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()
                st.success("LanÃ§amento financeiro registrado com sucesso!")
            else:
                st.warning("A descriÃ§Ã£o Ã© obrigatÃ³ria.")
                
    st.markdown("---")
    st.subheader("HistÃ³rico de MovimentaÃ§Ãµes Financeiras")
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    if not df_fin.empty:
        st.dataframe(df_fin, use_container_width=True)
    else:
        st.info("Nenhum lanÃ§amento financeiro registrado ainda.")
