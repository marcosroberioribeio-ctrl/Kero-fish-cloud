# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(page_title="Kero Fish ERP", layout="wide")

DB_FILE = "kerofish.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produtos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, categoria TEXT, preco_kg REAL, estoque_kg REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- LOGO E SLOGAN ---
try:
    st.sidebar.image("logo.png", use_column_width=True) # Certifique-se que o arquivo 'logo.png' estÃ¡ no GitHub
except:
    st.sidebar.warning("Logo nÃ£o encontrada.")

st.sidebar.markdown("<h3 style='text-align: center;'>Kero Fish ERP</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; font-style: italic;'>O melhor pescado da regiÃ£o!</p>", unsafe_allow_html=True) # SEU SLOGAN AQUI
st.sidebar.markdown("---")

opcao = st.sidebar.radio("NavegaÃ§Ã£o", ["Estoque de Pescados"])

if opcao == "Estoque de Pescados":
    st.title("Controle de Estoque e Mercadorias")
    
    # Aba de Cadastro e ExclusÃ£o
    aba1, aba2 = st.tabs(["Cadastrar", "Excluir Produto"])
    
    with aba1:
        with st.form("form_cad"):
            nome_p = st.text_input("Nome da Mercadoria")
            cat_p = st.selectbox("Categoria", ["Peixe Inteiro", "FilÃ©", "Fruto do Mar", "Bebidas", "Outros"])
            preco = st.number_input("PreÃ§o (R$)", min_value=0.0)
            qtd = st.number_input("Quantidade (KG/Unid)", min_value=0.0)
            if st.form_submit_button("Cadastrar"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)", 
                          (nome_p, cat_p, preco, qtd))
                conn.commit()
                conn.close()
                st.success("Cadastro realizado com sucesso!")
                st.rerun()

    with aba2:
        st.subheader("Excluir Mercadoria")
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT id, nome FROM produtos", conn)
        conn.close()
        
        if not df.empty:
            prod_del = st.selectbox("Selecione o produto para DELETAR", df["nome"].tolist())
            if st.button("Confirmar ExclusÃ£o"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM produtos WHERE nome = ?", (prod_del,))
                conn.commit()
                conn.close()
                st.error(f"Produto '{prod_del}' removido!")
                st.rerun()
        else:
            st.info("Estoque vazio.")

    st.markdown("---")
    conn = sqlite3.connect(DB_FILE)
    df_full = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    st.dataframe(df_full, use_container_width=True)
