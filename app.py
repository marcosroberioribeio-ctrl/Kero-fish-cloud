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

# MENU LATERAL COM TODOS OS ITENS
opcao = st.sidebar.radio(
    "NavegaÃ§Ã£o", 
    [
        "Painel Geral", 
        "Fornecedores", 
        "Compras de produtos", 
        "Estoque", 
        "Clientes", 
        "Vendas", 
        "Financeiro", 
        "Despesas Gerais", 
        "RelatÃ³rios", 
        "Normas"
    ]
)

# 1. DASHBOARD
if opcao == "Painel Geral":
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

# 2. FORNECEDORES
elif opcao == "Fornecedores":
    st.title("GestÃ£o de Fornecedores")
    st.write("Controle de parceiros e contatos comerciais.")
    
    with st.form("form_fornecedor"):
        nome = st.text_input("Nome do Fornecedor")
        contato = st.text_input("Telefone ou E-mail")
        categoria = st.selectbox("Categoria", ["Embalagens", "Insumos", "Limpeza", "Outros"])
        submit = st.form_submit_button("Cadastrar")
        
        if submit:
            st.success(f"Fornecedor {nome} registrado!")

# 3. COMPRAS DE PRODUTOS
elif opcao == "Compras de produtos":
    st.title("Compras de Produtos")
    st.write("Registre as entradas de mercadorias e repasse automÃ¡tico para o estoque/financeiro.")
    
    conn = sqlite3.connect(DB_FILE)
    df_p = pd.read_sql_query("SELECT id, nome, estoque_kg FROM produtos", conn)
    conn.close()
    
    lista_produtos = df_p["nome"].tolist() if not df_p.empty else []
    
    if not lista_produtos:
        st.warning("Cadastre produtos previamente no menu 'Estoque' para registrar compras.")
    else:
        with st.form("form_compra", clear_on_submit=True):
            prod_sel = st.selectbox("Produto", lista_produtos)
            qtd_compra = st.number_input("Quantidade Comprada (KG/Unid)", min_value=0.1, format="%.2f")
            valor_total_compra = st.number_input("Valor Total da Compra (R$)", min_value=0.01, format="%.2f")
            
            if st.form_submit_button("Registrar Compra"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                c.execute("INSERT INTO compras (produto, qtd, valor_total, data_compra) VALUES (?, ?, ?, ?)",
                          (prod_sel, qtd_compra, valor_total_compra, hoje))
                
                prod_atual = c.execute("SELECT estoque_kg FROM produtos WHERE nome = ?", (prod_sel,)).fetchone()
                if prod_atual:
                    novo_est = prod_atual[0] + qtd_compra
                    c.execute("UPDATE produtos SET estoque_kg = ? WHERE nome = ?", (novo_est, prod_sel))
                
                c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)",
                          (f"Compra: {prod_sel}", "SaÃ­da", valor_total_compra, hoje))
                
                conn.commit()
                conn.close()
                st.success("Compra registrada, estoque atualizado e lanÃ§amento efetuado no caixa!")
                st.rerun()

# 4. ESTOQUE
elif opcao == "Estoque":
    st.title("Controle de Estoque e Mercadorias")
    
    aba1, aba2 = st.tabs(["Cadastrar", "Excluir Produto"])
    
    with aba1:
        with st.form("form_cad", clear_on_submit=True):
            nome_p = st.text_input("Nome da Mercadoria")
            cat_p = st.selectbox("Categoria", ["Peixe Inteiro", "FilÃ©", "Fruto do Mar", "Bebidas", "Outros"])
            preco = st.number_input("PreÃ§o (R$)", min_value=0.0, format="%.2f")
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
                    st.warning("O nome do produto Ã© obrigatÃ³rio.")

    with aba2:
        st.subheader("Excluir Mercadoria")
        conn = sqlite3.connect(DB_FILE)
        df_prod = pd.read_sql_query("SELECT id, nome FROM produtos", conn)
        conn.close()
        
        if not df_prod.empty:
            prod_del = st.selectbox("Selecione o produto para DELETAR", df_prod["nome"].tolist())
            if st.button("Confirmar ExclusÃ£o"):
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

# 5. CLIENTES
elif opcao == "Clientes":
    st.title("GestÃ£o de Clientes")
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome Completo / RazÃ£o Social")
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
                st.warning("O nome Ã© obrigatÃ³rio.")
    
    st.markdown("---")
    conn = sqlite3.connect(DB_FILE)
    df_c = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    st.dataframe(df_c, use_container_width=True)

# 6. VENDAS
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
            
            st.info(f"PreÃ§o UnitÃ¡rio: R$ {preco_unit:.2f} | Total: R$ {valor_calculado:.2f}")
            
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

# 7. FINANCEIRO
elif opcao == "Financeiro":
    st.title("Controle Financeiro / Caixa")
    with st.form("form_fin", clear_on_submit=True):
        desc = st.text_input("DescriÃ§Ã£o")
        tipo = st.selectbox("Tipo", ["Entrada", "SaÃ­da"])
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        if st.form_submit_button("Registrar MovimentaÃ§Ã£o"):
            if desc.strip():
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)",
                          (desc, tipo, valor, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()
                st.success("LanÃ§amento registrado!")
                st.rerun()
            else:
                st.warning("A descriÃ§Ã£o Ã© obrigatÃ³ria.")
                
    st.markdown("---")
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    if not df_fin.empty:
        st.dataframe(df_fin, use_container_width=True)
    else:
        st.info("Nenhum movimento financeiro.")

# 8. DESPESAS GERAIS
elif opcao == "Despesas Gerais":
    st.title("Controle de Despesas Gerais")
    with st.form("form_despesa", clear_on_submit=True):
        desc_esp = st.text_input("DescriÃ§Ã£o da Despesa (ex: Conta de Luz, Aluguel)")
        valor_esp = st.number_input("Valor da Despesa (R$)", min_value=0.01, format="%.2f")
        
        if st.form_submit_button("LanÃ§ar Despesa"):
            if desc_esp.strip():
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                hoje = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # Registra na tabela prÃ³pria de despesas
                c.execute("INSERT INTO despesas (descricao, valor, data_despes
