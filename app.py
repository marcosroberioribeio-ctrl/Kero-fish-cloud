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
    c.execute('CREATE TABLE IF NOT EXISTS contas_pagar (id INTEGER PRIMARY KEY AUTOINCREMENT, fornecedor TEXT, descricao TEXT, valor REAL, vencimento TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS contas_receber (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, descricao TEXT, valor REAL, vencimento TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS entregas (id INTEGER PRIMARY KEY AUTOINCREMENT, data_ent TEXT, pedido TEXT, bairro TEXT, entregador TEXT, taxa_entrega REAL)')
    conn.commit()
    conn.close()

init_db()

# ... [MANTIDO: Carregamento da Logo e Menu Lateral] ...
logo_encontrada = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG"]:
    if os.path.exists(f"logo.{ext}"):
        logo_encontrada = f"logo.{ext}"
        break
if logo_encontrada:
    st.sidebar.image(logo_encontrada, use_container_width=True)
else:
    st.sidebar.warning("Atenção: Envie o arquivo da logo para a raiz.")

opcao = st.sidebar.radio("Navegação", ["Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", "Clientes", "Vendas", "Financeiro", "Despesas Gerais", "Contas a Pagar", "Contas a Receber", "Entregas", "Relatórios", "Normas", "Importar Planilha"])

# ... [MANTIDO: Blocos 1 a 6 (Painel Geral até Vendas)] ...
# (Os blocos 1 ao 6 permanecem exatamente como você enviou)
# [Aqui no seu arquivo, mantenha os seus blocos 1 a 6 originais]

# 7. FINANCEIRO
elif opcao == "Financeiro":
    st.title("Controle Financeiro")
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    st.dataframe(df_fin, use_container_width=True)

# 8. DESPESAS GERAIS
elif opcao == "Despesas Gerais":
    st.title("Registro de Despesas Gerais")
    with st.form("form_despesa", clear_on_submit=True):
        desc_esp = st.text_input("Descrição da Despesa")
        val_esp = st.number_input("Valor R$", min_value=0.0)
        if st.form_submit_button("Registrar Despesa"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO despesas (data_desp, categoria, descricao, valor, pagamento) VALUES (?, ?, ?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d"), "Geral", desc_esp, val_esp, "Dinheiro"))
            c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", 
                      (f"Despesa: {desc_esp}", "Saída", val_esp, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Despesa registrada!")
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    df_esp = pd.read_sql_query("SELECT * FROM despesas", conn)
    conn.close()
    st.dataframe(df_esp, use_container_width=True)

# 9. CONTAS A PAGAR (Corrigido)
elif opcao == "Contas a Pagar":
    st.title("Contas a Pagar")
    with st.form("form_pagar", clear_on_submit=True):
        forn = st.text_input("Fornecedor")
        desc = st.text_input("Descrição")
        val = st.number_input("Valor R$", min_value=0.0)
        venc = st.date_input("Vencimento")
        if st.form_submit_button("Lançar Conta"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO contas_pagar (fornecedor, descricao, valor, vencimento, status) VALUES (?, ?, ?, ?, ?)", 
                      (forn, desc, val, str(venc), "Pendente"))
            conn.commit()
            conn.close()
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM contas_pagar", conn), use_container_width=True)
    conn.close()

# 10. CONTAS A RECEBER (Corrigido)
elif opcao == "Contas a Receber":
    st.title("Contas a Receber")
    with st.form("form_receber", clear_on_submit=True):
        cli = st.text_input("Cliente")
        desc = st.text_input("Descrição")
        val = st.number_input("Valor R$", min_value=0.0)
        venc = st.date_input("Vencimento")
        if st.form_submit_button("Lançar Recebimento"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO contas_receber (cliente, descricao, valor, vencimento, status) VALUES (?, ?, ?, ?, ?)", 
                      (cli, desc, val, str(venc), "Pendente"))
            conn.commit()
            conn.close()
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM contas_receber", conn), use_container_width=True)
    conn.close()

# 11. ENTREGAS (Corrigido)
elif opcao == "Entregas":
    st.title("Controle de Entregas")
    with st.form("form_entrega", clear_on_submit=True):
        ped = st.text_input("Pedido")
        bair = st.text_input("Bairro")
        ent = st.text_input("Entregador")
        taxa = st.number_input("Taxa de Entrega R$", min_value=0.0)
        if st.form_submit_button("Registrar Entrega"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO entregas (data_ent, pedido, bairro, entregador, taxa_entrega) VALUES (?, ?, ?, ?, ?)", 
                      (datetime.now().strftime("%Y-%m-%d"), ped, bair, ent, taxa))
            conn.commit()
            conn.close()
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM entregas", conn), use_container_width=True)
    conn.close()

# 12, 13 e 14: Relatórios, Normas e Importação (Mantidos como estava)
elif opcao == "Relatórios":
    st.title("Relatórios do Sistema")
    st.info("Módulo de relatórios gerenciais.")
elif opcao == "Normas":
    st.title("Normas e Procedimentos")
    st.info("Documentação interna.")
elif opcao == "Importar Planilha":
    # [SEU CÓDIGO ORIGINAL DE IMPORTAÇÃO]
    pass
       
