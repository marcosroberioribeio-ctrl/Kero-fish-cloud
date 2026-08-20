# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

st.set_page_config(page_title="Kero Fish ERP", layout="wide")
DB_FILE = "kerofish.db"

LISTA_PRODUTOS_MESTRA = [
    "Peixe: Tilapia filé", "Peixe: Tilapia inteiro", "Peixe: Salmão filé", 
    "Peixe: Pargo filé", "Peixe: Pargo inteiro", "Peixe: Atum", "Sardinha eviscerada",
    "Camarão: M", "Camarão: G", "Camarão: GG", 
    "Camarão filé: M", "Camarão filé: G", "Camarão filé: GG",
    "Castanha: Caju assada caseira", "Castanha: Caramelizada (100g)", "Castanha: Caramelizada (200g)",
    "Castanha: Assada (100g)", "Castanha: Assada (200g)",
    "Ovos: Caipira (10/13/20/30 un)", "Ovos: Comum",
    "Mel", "Cajuína", "Manteiga da terra", "Temperos", "Molhos"
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, telefone TEXT, cidade TEXT, data_cad TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria TEXT, preco_kg REAL, estoque_kg REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, produto TEXT, qtd_kg REAL, valor_total REAL, data_venda TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, tipo TEXT, valor REAL, data_mov TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, produto TEXT, qtd REAL, valor_total REAL, data_compra TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, data_desp TEXT, categoria TEXT, descricao TEXT, valor REAL, pagamento TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS fornecedores (id INTEGER PRIMARY KEY AUTOINCREMENT, fornecedor TEXT, contato TEXT, telefone TEXT, endereco TEXT, produto_fornecido TEXT, prazo_pagamento TEXT, observacoes TEXT)')
    conn.commit()
    conn.close()

init_db()

opcao = st.sidebar.radio("Navegação", ["Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", "Clientes", "Vendas", "Financeiro", "Despesas Gerais", "Importar Planilha"])

if opcao == "Painel Geral":
    st.title("Painel Geral")
    conn = sqlite3.connect(DB_FILE)
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    st.metric("Total de Vendas", f"{len(df_vendas)}")
    conn.close()

elif opcao == "Fornecedores":
    st.title("Gestão de Fornecedores")
    conn = sqlite3.connect(DB_FILE)
    df_forn = pd.read_sql_query("SELECT * FROM fornecedores", conn)
    st.dataframe(df_forn, use_container_width=True)
    conn.close()

elif opcao == "Compras de produtos":
    st.title("Compras de Produtos")
    with st.form("compra", clear_on_submit=True):
        prod = st.selectbox("Produto", LISTA_PRODUTOS_MESTRA)
        qtd = st.number_input("Quantidade (KG)", min_value=0.1)
        val = st.number_input("Valor R$", min_value=0.0)
        if st.form_submit_button("Registrar"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO compras (produto, qtd, valor_total, data_compra) VALUES (?, ?, ?, ?)", (prod, qtd, val, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM compras", conn), use_container_width=True)
    conn.close()

elif opcao == "Estoque":
    st.title("Controle de Estoque")
    conn = sqlite3.connect(DB_FILE)
    df_c = pd.read_sql_query("SELECT produto, SUM(qtd) as total_comp FROM compras GROUP BY produto", conn)
    df_v = pd.read_sql_query("SELECT produto, SUM(qtd_kg) as total_vend FROM vendas GROUP BY produto", conn)
    conn.close()
    if not df_c.empty:
        df_e = df_c.merge(df_v, on="produto", how="left").fillna(0)
        df_e["Saldo"] = df_e["total_comp"] - df_e["total_vend"]
        st.dataframe(df_e, use_container_width=True)

elif opcao == "Clientes":
    st.title("Clientes")
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM clientes", conn), use_container_width=True)
    conn.close()

elif opcao == "Vendas":
    st.title("Vendas")
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM vendas", conn), use_container_width=True)
    conn.close()

elif opcao == "Importar Planilha":
    st.title("Importação de Planilha")
    if st.button("Executar Importação"):
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for f in os.listdir("."):
                if f.startswith("KERO FISH") and f.endswith(".xlsx"):
                    xls = pd.ExcelFile(f)
                    for sheet in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet)
                        if "cliente" in sheet.lower():
                            for idx, row in df.iterrows():
                                if idx == 0: continue # Pula o cabeçalho
                                c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)", 
                                          (str(row[0]), str(row[1]), str(row[2]), datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Importação concluída com sucesso!")
        except Exception as e:
            st.error(f"Erro ao importar: {e}")
        
