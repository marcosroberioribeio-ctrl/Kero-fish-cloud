import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Kero Fish ERP", layout="wide")

DB_FILE = "kerofish.db"

# Inicializacao do Banco
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY, nome TEXT, telefone TEXT, cidade TEXT, data_cad TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, categoria TEXT, preco_kg REAL, estoque_kg REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY, cliente TEXT, produto TEXT, qtd_kg REAL, valor_total REAL, data_venda TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY, descricao TEXT, tipo TEXT, valor REAL, data_mov TEXT)')
    conn.commit()
    conn.close()

init_db()

# Logo (Certifique-se que o arquivo logo.png esta no seu repositorio ou use um link http)
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.warning("Logo nao encontrado (coloque 'logo.png' no repositorio)")

st.sidebar.title("Kero Fish ERP")
opcao = st.sidebar.radio("Navegacao", ["Dashboard", "Clientes", "Estoque de Pescados", "Vendas", "Financeiro"])

# Painel de Estoque (Corrigindo a Categoria)
if opcao == "Estoque de Pescados":
    st.title("Controle de Estoque e Mercadorias")
    
    with st.form("form_produto", clear_on_submit=True):
        nome_p = st.text_input("Nome da Mercadoria")
        # Lista flexivel de categorias
        cat_p = st.selectbox("Categoria", ["Peixe Inteiro", "File", "Fruto do Mar", "Bebidas", "Outros"])
        preco_kg = st.number_input("Preco (R$)", min_value=0.0, format="%.2f")
        estoque = st.number_input("Quantidade Inicial", min_value=0.0, format="%.2f")
        salvar = st.form_submit_button("Cadastrar no Estoque")
        
        if salvar:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)", 
                      (nome_p, cat_p, preco_kg, estoque))
            conn.commit()
            conn.close()
            st.success(f"{nome_p} cadastrado na categoria {cat_p} com sucesso!")

    st.subheader("Estoque Atual")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# Painel Vendas (Para evitar erro de leitura)
elif opcao == "Vendas":
    st.title("Registrar Venda")
    conn = sqlite3.connect(DB_FILE)
    df_p = pd.read_sql_query("SELECT id, nome, categoria, preco_kg, estoque_kg FROM produtos", conn)
    conn.close()
    
    if df_p.empty:
        st.warning("Cadastre produtos no menu Estoque primeiro.")
    else:
        produto_sel = st.selectbox("Selecione o produto", df_p["nome"].tolist())
        produto_dados = df_p[df_p["nome"] == produto_sel].iloc[0]
        st.write(f"Categoria: {produto_dados['categoria']} | Disponivel: {produto_dados['estoque_kg']}")
        # ... resto do codigo de venda 
