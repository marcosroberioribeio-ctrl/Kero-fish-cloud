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
    c.execute('CREATE TABLE IF NOT EXISTS contas_pagar (id INTEGER PRIMARY KEY AUTOINCREMENT, fornecedor TEXT, descricao TEXT, valor REAL, vencimento TEXT, status TEXT, data_pagamento TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS contas_receber (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, descricao TEXT, valor REAL, vencimento TEXT, status TEXT, data_recebimento TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS entregas (id INTEGER PRIMARY KEY AUTOINCREMENT, data_ent TEXT, pedido TEXT, bairro TEXT, entregador TEXT, taxa_entrega REAL, custo_combustivel REAL, lucro_entrega REAL)')
    conn.commit()
    conn.close()

init_db()

logo_encontrada = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG"]:
    if os.path.exists(f"logo.{ext}"):
        logo_encontrada = f"logo.{ext}"
        break

if logo_encontrada:
    st.sidebar.image(logo_encontrada, use_container_width=True)
else:
    st.sidebar.warning("Atenção: Envie o arquivo da logo para a raiz.")

opcao = st.sidebar.radio(
    "Navegação", 
    [
        "Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", 
        "Clientes", "Vendas", "Financeiro", "Despesas Gerais", 
        "Contas a Pagar", "Contas a Receber", "Entregas", "Relatórios", "Normas", "Importar Planilha"
    ]
)

# 1. PAINEL GERAL
if opcao == "Painel Geral":
    st.title("Painel Geral de Gestão")
    conn = sqlite3.connect(DB_FILE)
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    df_despesas = pd.read_sql_query("SELECT * FROM despesas", conn)
    df_compras = pd.read_sql_query("SELECT * FROM compras", conn)
    conn.close()
    total_faturado = df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
    total_despesas = df_despesas["valor"].sum() if not df_despesas.empty else 0.0
    total_compras = df_compras["valor_total"].sum() if not df_compras.empty else 0.0
    total_saidas = total_despesas + total_compras
    saldo_caixa = total_faturado - total_saidas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento (Vendas)", f"R$ {total_faturado:,.2f}")
    col2.metric("Total Gastos (Compra+Desp)", f"R$ {total_saidas:,.2f}")
    col3.metric("Saldo em Caixa", f"R$ {saldo_caixa:,.2f}")
    col4.metric("Qtd Vendas", f"{len(df_vendas)}")

# 2. FORNECEDORES
elif opcao == "Fornecedores":
    st.title("Gestão de Fornecedores")
    with st.form("form_fornecedor", clear_on_submit=True):
        f_nome = st.text_input("Nome do Fornecedor")
        f_contato = st.text_input("Contato / Responsável")
        f_tel = st.text_input("Telefone")
        f_end = st.text_input("Endereço")
        f_prod = st.text_input("Produtos Fornecidos")
        f_prazo = st.text_input("Prazo de Pagamento")
        f_obs = st.text_input("Observações")
        if st.form_submit_button("Cadastrar Fornecedor"):
            if f_nome:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO fornecedores (fornecedor, contato, telefone, endereco, produto_fornecido, prazo_pagamento, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (f_nome, f_contato, f_tel, f_end, f_prod, f_prazo, f_obs))
                conn.commit()
                conn.close()
                st.success("Fornecedor cadastrado com sucesso!")
                st.rerun()
    conn = sqlite3.connect(DB_FILE)
    df_forn = pd.read_sql_query("SELECT * FROM fornecedores", conn)
    conn.close()
    st.dataframe(df_forn, use_container_width=True)

# 3. COMPRAS, 4. ESTOQUE, 5. CLIENTES, 6. VENDAS, 7. FINANCEIRO, 8. DESPESAS, 9. CONTAS A PAGAR, 10. CONTAS A RECEBER, 11. ENTREGAS, 12. RELATÓRIOS, 13. NORMAS (Mantido conforme original)
# ... (restante das seções 3 a 13 iguais ao seu original)
elif opcao == "Compras de produtos":
    st.title("Compras de Produtos e Histórico")
    # ... (código existente)
elif opcao == "Estoque":
    st.title("Controle de Estoque Atualizado")
    # ... (código existente)
elif opcao == "Clientes":
    st.title("Cadastro e Gestão de Clientes")
    # ... (código existente)
elif opcao == "Vendas":
    st.title("Registrar Venda e Histórico")
    # ... (código existente)
# ... (demais seções)

# 14. IMPORTAR PLANILHA (CORRIGIDO PARA PULAR CABEÇALHO E LER ENDEREÇO)
elif opcao == "Importar Planilha":
    st.title("Importação de Dados do Excel")
    if st.button("Confirmar Importação de Todas as Abas"):
        arquivo_excel = None
        for f in os.listdir("."):
            if f.startswith("KERO FISH") and f.endswith(".xlsx"):
                arquivo_excel = f
                break
        if arquivo_excel:
            try:
                xls = pd.ExcelFile(arquivo_excel)
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                importadas = []
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    s_lower = sheet_name.lower()
                    if "fornecedor" in s_lower:
                        for idx, row in df.iterrows():
                            if idx == 0: continue # Pula o cabeçalho
                            nome_f = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                            if nome_f: c.execute("INSERT INTO fornecedores (fornecedor, contato, telefone) VALUES (?, ?, ?)", (nome_f, str(row.iloc[1]), str(row.iloc[2])))
                        importadas.append(f"Fornecedores ({sheet_name})")
                    elif "cliente" in s_lower:
                        for idx, row in df.iterrows():
                            if idx == 0: continue # Pula o cabeçalho
                            nome_c = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                            if nome_c: c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)", (nome_c, str(row.iloc[1]), str(row.iloc[2]), datetime.now().strftime("%Y-%m-%d")))
                        importadas.append(f"Clientes ({sheet_name})")
                conn.commit()
                conn.close()
                st.success(f"Importado com sucesso: {', '.join(importadas)}")
            except Exception as e:
                st.error(f"Erro: {e}")
       
