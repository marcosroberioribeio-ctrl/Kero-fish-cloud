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

# Logo Automatica
logo_encontrada = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "jpg.jpg"]:
    if os.path.exists(f"logo.{ext}"):
        logo_encontrada = f"logo.{ext}"
        break

if logo_encontrada:
    st.sidebar.image(logo_encontrada, use_container_width=True)
else:
    st.sidebar.warning("Atencao: Envie o arquivo da logo para a raiz do projeto com o nome 'logo.png' ou 'logo.jpg'.")

# MENU LATERAL
opcao = st.sidebar.radio(
    "Navegação", 
    [
        "Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", 
        "Clientes", "Vendas", "Financeiro", "Despesas Gerais", "Relatórios", "Normas","Importar Planilha"
    ]
)

# 1. DASHBOARD
if opcao == "Painel Geral":
       st.title("Painel Geral de Gestão")
    
        
conn = sqlite3.connect(DB_FILE)
        df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
        df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
        df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
        conn.close()
    
    total_faturado = df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
    entradas = df_fin[df_fin["tipo"] == "Entrada"]["valor"].sum() if not df_fin.empty else 0.0
    saidas = df_fin[df_fin["tipo"] == "Saída"]["valor"].sum() if not df_fin.empty else 0.0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento Vendas", f"R$ {total_faturado:,.2f}")
    col2.metric("Total Vendas", f"{len(df_vendas)}")
    col3.metric("Clientes", f"{len(df_clientes)}")
    col4.metric("Saldo Caixa", f"R$ {entradas - saidas:,.2f}")

# 3. COMPRAS DE PRODUTOS
elif opcao == "Compras de produtos":
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
            c.execute("SELECT id FROM produtos WHERE nome = ?", (prod,))
            if c.fetchone():
                c.execute("UPDATE produtos SET estoque_kg = estoque_kg + ? WHERE nome = ?", (qtd, prod))
            else:
                c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)", (prod, "Geral", 0.0, qtd))
            conn.commit()
            conn.close()
            st.success("Compra registrada e estoque atualizado!")
            st.rerun()

# 4. ESTOQUE
elif opcao == "Estoque":
    st.title("Controle de Estoque")
    with st.form("form_cad", clear_on_submit=True):
        nome_p = st.selectbox("Selecionar Produto da Lista", LISTA_PRODUTOS_MESTRA)
        cat_p = st.selectbox("Categoria", ["Peixe Inteiro", "Filé", "Crustáceos", "Castanhas e Secos", "Ovos e Laticínios", "Outros"])
        preco = st.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
        qtd = st.number_input("Ajustar Quantidade (KG/Unid)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Salvar no Estoque"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id FROM produtos WHERE nome = ?", (nome_p,))
            if c.fetchone():
                c.execute("UPDATE produtos SET categoria = ?, preco_kg = ?, estoque_kg = estoque_kg + ? WHERE nome = ?", (cat_p, preco, qtd, nome_p))
            else:
                c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)", (nome_p, cat_p, preco, qtd))
            conn.commit()
            conn.close()
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    df_full = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    st.dataframe(df_full, use_container_width=True)

# 6. VENDAS
elif opcao == "Vendas":
    st.title("Registrar Venda")
    conn = sqlite3.connect(DB_FILE)
    df_p = pd.read_sql_query("SELECT id, nome, preco_kg, estoque_kg FROM produtos", conn)
    conn.close()
    lista_produtos = df_p["nome"].tolist() if not df_p.empty else []
    if not lista_produtos:
        st.warning("Cadastre produtos no Estoque primeiro.")
    else:
        with st.form("form_venda", clear_on_submit=True):
            cliente_nome = st.text_input("Nome do Cliente (Opcional)")
            produto_sel = st.selectbox("Produto", lista_produtos)
            qtd_kg = st.number_input("Quantidade", min_value=0.1, format="%.2f")
            prod_info = df_p[df_p["nome"] == produto_sel].iloc[0]
            if st.form_submit_button("Finalizar Venda"):
                if qtd_kg > prod_info["estoque_kg"]:
                    st.error(f"Estoque insuficiente! Disponível: {prod_info['estoque_kg']}")
                else:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    val_tot = qtd_kg * prod_info["preco_kg"]
                    c.execute("INSERT INTO vendas (cliente, produto, qtd_kg, valor_total, data_venda) VALUES (?, ?, ?, ?, ?)",
                              (cliente_nome if cliente_nome else "Cliente Balcão", produto_sel, qtd_kg, val_tot, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    c.execute("UPDATE produtos SET estoque_kg = estoque_kg - ? WHERE id = ?", (qtd_kg, prod_info["id"]))
                    c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", (f"Venda: {produto_sel}", "Entrada", val_tot, datetime.now().strftime("%Y-%m-%d %H:%M")))
                    conn.commit()
                    conn.close()
                    st.success("Venda realizada com sucesso!")
                    st.rerun()

# [O restante do seu código (Clientes, Financeiro, Despesas, Relatórios, Normas) permanece igual]
# ... (mantenha os outros blocos elif da mesma forma que estavam no seu arquivo original)
if opçao == "Importar Planilha":
    st.title("Importação de Dados")
    if st.button("Confirmar Importação"):
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            
            # Importar Vendas
            df_v = pd.read_excel("KERO FISH_Financeira_Completa_Preenchida-4.xlsx", sheet_name="Vendas")
            for _, r in df_v.iterrows():
                if pd.notna(r.get("Produto")):
                    data_v = str(r.get("Data", ""))[:10]
                    c.execute("INSERT INTO vendas (cliente, produto, qtd_kg, valor_total, data_venda) VALUES (?, ?, ?, ?, ?)",
                              (r.get("Cliente", "Cliente Balcão"), r.get("Produto"), r.get("Quantidade"), r.get("Valor Venda"), data_v))
            
            # Importar Compras
            df_c = pd.read_excel("KERO FISH_Financeira_Completa_Preenchida-4.xlsx", sheet_name="Compras")
            for _, r in df_c.iterrows():
                if pd.notna(r.get("Produto")):
                    data_c = str(r.get("Data", ""))[:10]
                    c.execute("INSERT INTO compras (produto, qtd, valor_total, data_compra) VALUES (?, ?, ?, ?)",
                              (r.get("Produto"), r.get("Quantidade Comprada (KG)"), r.get("Valor Total"), data_c))

            conn.commit()
            conn.close()
            st.success("Importação concluída com sucesso!")
        except Exception as e:
            st.error(f"Erro: {e}")
