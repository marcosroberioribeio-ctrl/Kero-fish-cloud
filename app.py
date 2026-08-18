# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

st.set_page_config(page_title="Kero Fish ERP", layout="wide")

DB_FILE = "kerofish.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, cidade TEXT, data_cad TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria TEXT, preco_kg REAL, estoque_kg REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, produto TEXT, qtd_kg REAL, valor_total REAL, data_venda TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, tipo TEXT, valor REAL, data_mov TEXT)')
    # Tabelas novas para os novos mÃ³dulos
    c.execute('CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, produto TEXT, qtd REAL, valor_total REAL, data_compra TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, data_despesa TEXT)')
    conn.commit()
    conn.close()

init_db()

# Logo Automatica
logo_encontrada = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "jpg.jpg"]:
    if os.path.exists(f"logo.{ext}"):
        logo_encontrada = f"logo.{ext}"
        break

if logo_encontrada:
    st.sidebar.image(logo_encontrada, use_container_width=True)
else:
    st.sidebar.warning("Atencao: Envie o arquivo da logo para a raiz do GitHub com o nome 'logo.png' ou 'logo.jpg'.")

# Menu atualizado com os novos itens na ordem solicitada
opcao = st.sidebar.radio("NavegaÃ§Ã£o", ["Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", "Clientes", "Vendas", "Financeiro", "Despesas Gerais", "RelatÃ³rios", "Normas"])

# 1. DASHBOARD
if opcao == "Painel Geral":
    st.title("Painel Geral de GestÃ£o")
    conn = sqlite3.connect(DB_FILE)
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    total_faturado = df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
    entradas = df_fin[df_fin["tipo"] == "Entrada"]["valor"].sum() if not df_fin.empty else 0.0
    saidas = df_fin[df_fin["tipo"] == "SaÃ­da"]["valor"].sum() if not df_fin.empty else 0.0
    st.metric("Saldo do Caixa", f"R$ {entradas - saidas:,.2f}")

# 2. FORNECEDORES
elif opcao == "Fornecedores":
    st.title("GestÃ£o de Fornecedores")
    # ... (seu cÃ³digo de fornecedores original)

# 3. COMPRAS DE PRODUTOS (NOVO)
elif opcao == "Compras de produtos":
    st.title("Compras de Produtos")
    with st.form("form_compra"):
        prod = st.text_input("Produto comprado")
        qtd = st.number_input("Quantidade", min_value=0.1)
        val = st.number_input("Valor Total R$", min_value=0.0)
        if st.form_submit_button("Registrar Compra"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO compras (produto, qtd, valor_total, data_compra) VALUES (?, ?, ?, ?)", 
                      (prod, qtd, val, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Compra registrada!")

# 4. ESTOQUE
elif opcao == "Estoque":
    st.title("Controle de Estoque")
    # ... (seu cÃ³digo de estoque original)

# 5. CLIENTES
elif opcao == "Clientes":
    st.title("GestÃ£o de Clientes")
    # ... (seu cÃ³digo de clientes original)

# 6. VENDAS
elif opcao == "Vendas":
    st.title("Registrar Venda")
    # ... (seu cÃ³digo de vendas original)

# 7. FINANCEIRO
elif opcao == "Financeiro":
    st.title("Controle Financeiro")
    # ... (seu cÃ³digo de financeiro original)

# 8. DESPESAS GERAIS (NOVO)
elif opcao == "Despesas Gerais":
    st.title("Despesas Gerais")
    with st.form("form_desp"):
        desc = st.text_input("DescriÃ§Ã£o da despesa")
        val = st.number_input("Valor R$", min_value=0.01)
        if st.form_submit_button("LanÃ§ar Despesa"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO despesas (descricao, valor, data_despesa) VALUES (?, ?, ?)", 
                      (desc, val, datetime.now().strftime("%Y-%m-%d")))
            c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", 
                      (f"Despesa: {desc}", "SaÃ­da", val, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Despesa lanÃ§ada no caixa!")

# 9. RELATÃ“RIOS (NOVO)
elif opcao == "RelatÃ³rios":
    st.title("RelatÃ³rios do Sistema")
    conn = sqlite3.connect(DB_FILE)
    df_compras = pd.read_sql_query("SELECT * FROM compras", conn)
    df_despesas = pd.read_sql_query("SELECT * FROM despesas", conn)
    conn.close()
    st.subheader("HistÃ³rico de Compras")
    st.dataframe(df_compras)
    st.subheader("HistÃ³rico de Despesas")
    st.dataframe(df_despesas)

elif opcao == "Normas":
    st.title("Normas e Boas PrÃ¡ticas")
    # ... (seu cÃ³digo de normas original)
    
