# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3
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
    conn.commit()
    conn.close()

init_db()

# Logo e Slogan
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    pass

st.sidebar.markdown("<h3 style='text-align: center;'>Kero Fish ERP</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-style: italic;'>O melhor pescado da regiao!</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

opcao = st.sidebar.radio("Navegacao", ["Dashboard", "Clientes", "Estoque de Pescados", "Vendas", "Financeiro"])

# 1. DASHBOARD
if opcao == "Dashboard":
    st.title("Painel Geral de Gestao")
    st.markdown("Visualizacao rapida do desempenho do seu negocio.")
    
    conn = sqlite3.connect(DB_FILE)
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    df_clientes = pd.read_sql_query("SELECT * FROM clientes", conn)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    total_faturado = df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
    total_vendas = len(df_vendas)
    total_clientes = len(df_clientes)
    
    entradas = df_fin[df_fin["tipo"] == "Entrada"]["valor"].sum() if not df_fin.empty else 0.0
    saidas = df_fin[df_fin["tipo"] == "Saida"]["valor"].sum() if not df_fin.empty else 0.0
    saldo_caixa = entradas - saidas
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento Vendas", f"R$ {total_faturado:,.2f}")
    col2.metric("Total de Vendas", f"{total_vendas}")
    col3.metric("Clientes Cadastrados", f"{total_clientes}")
    col4.metric("Saldo do Caixa", f"R$ {saldo_caixa:,.2f}")

# 2. CLIENTES
elif opcao == "Clientes":
    st.title("Gestao de Clientes")
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome Completo / Razao Social")
        telefone = st.text_input("Telefone / WhatsApp")
        cidade = st.text_input("Cidade")
        if st.form_submit_button("Cadastrar Cliente"):
            if nome.strip():
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)",
                          (nome, telefone, cidade, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()
                st.success("Cliente cadastrado com sucesso!")
                st.rerun()
            else:
                st.warning("O nome e obrigatorio.")
    
    st.markdown("---")
    conn = sqlite3.connect(DB_FILE)
    df_c = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    st.dataframe(df_c, use_container_width=True)

# 3. ESTOQUE DE PESCADOS
elif opcao == "Estoque de Pescados":
    st.title("Controle de Estoque e Mercadorias")
    
    aba1, aba2 = st.tabs(["Cadastrar", "Excluir Produto"])
    
    with aba1:
        with st.form("form_cad", clear_on_submit=True):
            nome_p = st.text_input("Nome da Mercadoria")
            cat_p = st.selectbox("Categoria", ["Peixe Inteiro", "File", "Fruto do Mar", "Bebidas", "Outros"])
            preco = st.number_input("Preco (R$)", min_value=0.0, format="%.2f")
            qtd = st.number_input("Quantidade (KG/Unid)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Cadastrar no Estoque"):
                if nome_p.strip():
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)", 
                              (nome_p, cat_p, preco, qtd))
                    conn.commit()
                    conn.close()
                    st.success("Produto cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.warning("O nome do produto e obrigatorio.")

    with aba2:
        st.subheader("Excluir Mercadoria")
        conn = sqlite3.connect(DB_FILE)
        df_prod = pd.read_sql_query("SELECT id, nome FROM produtos", conn)
        conn.close()
        
        if not df_prod.empty:
            prod_del = st.selectbox("Selecione o produto para DELETAR", df_prod["nome"].tolist())
            if st.button("Confirmar Exclusao"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM produtos WHERE nome = ?", (prod_del,))
                conn.commit()
                conn.close()
                st.error(f"Produto '{prod_del}' removido do estoque!")
                st.rerun()
        else:
            st.info("Nenhum produto cadastrado.")

    st.markdown("---")
    conn = sqlite3.connect(DB_FILE)
    df_full = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    st.dataframe(df_full, use_container_width=True)

# 4. VENDAS
elif opcao == "Vendas":
    st.title("Registrar Venda")
    conn = sqlite3.connect(DB_FILE)
    df_c = pd.read_sql_query("SELECT nome FROM clientes", conn)
    df_p = pd.read_sql_query("SELECT id, nome, preco_kg, estoque_kg FROM produtos", conn)
    conn.close()
    
    lista_clientes = df_c["nome"].tolist() if not df_c.empty else []
    lista_produtos = df_p["nome"].tolist() if not df_p.empty else []
    
    if not lista_clientes or not lista_produtos:
        st.warning("Cadastre pelo menos 1 Cliente e 1 Produto para registrar vendas.")
    else:
        with st.form("form_venda", clear_on_submit=True):
            cliente_sel = st.selectbox("Cliente", lista_clientes)
            produto_sel = st.selectbox("Produto", lista_produtos)
            qtd_kg = st.number_input("Quantidade (KG/Unid)", min_value=0.1, format="%.2f")
            
            prod_info = df_p[df_p["nome"] == produto_sel].iloc[0]
            preco_unit = prod_info["preco_kg"]
            valor_calculado = qtd_kg * preco_unit
            
            st.info(f"Preco Unitario: R$ {preco_unit:.2f} | Total: R$ {valor_calculado:.2f}")
            
            if st.form_submit_button("Finalizar Venda"):
                if qtd_kg > prod_info["estoque_kg"]:
                    st.error("Estoque insuficiente!")
                else:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO vendas (cliente, produto, qtd_kg, valor_total, data_venda) VALUES (?, ?, ?, ?, ?)",
                              (cliente_sel, produto_sel, qtd_kg, valor_calculado, hoje))
                    novo_estoque = prod_info["estoque_kg"] - qtd_kg
                    c.execute("UPDATE produtos SET estoque_kg = ? WHERE id = ?", (novo_estoque, prod_info["id"]))
                    c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)",
                              (f"Venda: {produto_sel} ({cliente_sel})", "Entrada", valor_calculado, hoje))
                    conn.commit()
                    conn.close()
                    st.success("Venda registrada com sucesso!")
                    st.rerun()

# 5. FINANCEIRO
elif opcao == "Financeiro":
    st.title("Controle Financeiro / Caixa")
    with st.form("form_fin", clear_on_submit=True):
        desc = st.text_input("Descricao")
        tipo = st.selectbox("Tipo", ["Entrada", "Saida"])
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        if st.form_submit_button("Registrar Movimentacao"):
            if desc.strip():
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)",
                          (desc, tipo, valor, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()
                st.success("Lancamento registrado!")
                st.rerun()
            else:
                st.warning("A descricao e obrigatoria.")
                
    st.markdown("---")
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    if not df_fin.empty:
        st.dataframe(df_fin, use_container_width=True)
    else:
        st.info("Nenhum movimento financeiro.")
Yahoo Mail: Pesquise, organize e aumente sua produtividade
