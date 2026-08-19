# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

st.set_page_config(page_title="Kero Fish ERP", layout="wide")

DB_FILE = "kerofish.db"

# Lista Mestra de Produtos
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
    c.execute('CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, data_despesa TEXT)')
    conn.commit()
    conn.close()

init_db()

# MENU LATERAL
opcao = st.sidebar.radio("Navegação", ["Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", "Clientes", "Vendas", "Financeiro", "Despesas Gerais", "Relatórios", "Normas"])

# 3. COMPRAS DE PRODUTOS
if opcao == "Compras de produtos":
    st.title("Compras de Produtos")
    with st.form("form_compra", clear_on_submit=True):
        prod = st.selectbox("Selecione o Produto", LISTA_PRODUTOS_MESTRA)
        qtd = st.number_input("Quantidade (KG/Unid)", min_value=0.1)
        val = st.number_input("Valor Total R$", min_value=0.0)
        if st.form_submit_button("Registrar Compra"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            hoje = datetime.now().strftime("%Y-%m-%d")
            c.execute("INSERT INTO compras (produto, qtd, valor_total, data_compra) VALUES (?, ?, ?, ?)", (prod, qtd, val, hoje))
            c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", (f"Compra: {prod}", "Saída", val, hoje))
            # Tenta atualizar se existir, senão insere no estoque
            c.execute("UPDATE produtos SET estoque_kg = estoque_kg + ? WHERE nome = ?", (qtd, prod))
            conn.commit()
            conn.close()
            st.success(f"Compra de {prod} registrada!")

# 8. DESPESAS GERAIS
elif opcao == "Despesas Gerais":
    st.title("Controle de Despesas Gerais")
    categorias_despesa = ["Água", "Energia", "Material de Limpeza", "Manutenção", "Embalagens", "Outros"]
    with st.form("form_despesa", clear_on_submit=True):
        cat_sel = st.selectbox("Categoria da Despesa", categorias_despesa)
        val_esp = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        if st.form_submit_button("Lançar Despesa"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO despesas (descricao, valor, data_despesa) VALUES (?, ?, ?)", (cat_sel, val_esp, datetime.now().strftime("%Y-%m-%d")))
            c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", (f"Despesa: {cat_sel}", "Saída", val_esp, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success(f"Despesa de {cat_sel} lançada!")
            st.rerun()

# (Mantenha o restante das outras abas igual ao que você já tinha)
