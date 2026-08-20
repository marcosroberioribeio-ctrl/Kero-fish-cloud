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

# --- Funções de Edição e Exclusão ---

def secao_edicao(tabela, df, colunas_editaveis, coluna_rotulo):
    if df.empty:
        return
    st.markdown("---")
    st.subheader(f"✏️ Editar Registro ({tabela})")
    
    opcoes = {f"ID {row['id']} - {row[coluna_rotulo]}": row['id'] for _, row in df.iterrows()}
    selected_label = st.selectbox(f"Selecione o item para editar:", list(opcoes.keys()), key=f"edit_sel_{tabela}")
    id_selecionado = opcoes[selected_label]
    
    conn = sqlite3.connect(DB_FILE)
    registro = pd.read_sql_query(f"SELECT * FROM {tabela} WHERE id = ?", conn, params=(id_selecionado,))
    conn.close()
    
    if not registro.empty:
        row = registro.iloc[0]
        with st.form(f"form_edit_{tabela}"):
            novos_dados = {}
            for col in colunas_editaveis:
                novos_dados[col] = st.text_input(col, value=str(row[col]))
            
            if st.form_submit_button("Salvar Alterações"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                query = f"UPDATE {tabela} SET {', '.join([f'{col} = ?' for col in colunas_editaveis])} WHERE id = ?"
                params = [novos_dados[col] for col in colunas_editaveis] + [id_selecionado]
                c.execute(query, params)
                conn.commit()
                conn.close()
                st.success("Registro atualizado com sucesso!")
                st.rerun()

def secao_exclusao(tabela, df, coluna_rotulo):
    if df.empty:
        return
    st.markdown("---")
    st.subheader("🗑️ Excluir Registro")
    opcoes_delecao = {f"ID {row['id']} - {row[coluna_rotulo]}": row['id'] for _, row in df.iterrows()}
    selected_label = st.selectbox(f"Selecione o item para excluir ({tabela}):", list(opcoes_delecao.keys()), key=f"del_{tabela}")
    
    if st.button(f"Confirmar Exclusão ({tabela})", key=f"btn_del_{tabela}"):
        id_para_deletar = opcoes_delecao[selected_label]
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(f"DELETE FROM {tabela} WHERE id = ?", (id_para_deletar,))
        conn.commit()
        conn.close()
        st.success(f"Registro ID {id_para_deletar} excluído com sucesso!")
        st.rerun()

# --- UI Sidebar ---
logo_encontrada = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG"]:
    if os.path.exists(f"logo.{ext}"):
        logo_encontrada = f"logo.{ext}"
        break

if logo_encontrada:
    st.sidebar.image(logo_encontrada, use_container_width=True)
else:
    st.sidebar.warning("Atenção: Envie o arquivo da logo.")

opcao = st.sidebar.radio(
    "Navegação", 
    [
        "Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", 
        "Clientes", "Vendas", "Financeiro", "Despesas Gerais", 
        "Contas a Pagar", "Contas a Receber", "Entregas", "Relatórios", "Normas", "Importar Planilha"
    ]
)

# --- Seções ---

if opcao == "Fornecedores":
    st.title("Gestão de Fornecedores")
    conn = sqlite3.connect(DB_FILE)
    df_forn = pd.read_sql_query("SELECT * FROM fornecedores", conn)
    conn.close()
    st.dataframe(df_forn, use_container_width=True)
    secao_edicao("fornecedores", df_forn, ["fornecedor", "contato", "telefone", "endereco", "produto_fornecido", "prazo_pagamento", "observacoes"], "fornecedor")
    secao_exclusao("fornecedores", df_forn, "fornecedor")

elif opcao == "Compras de produtos":
    st.title("Compras de Produtos")
    conn = sqlite3.connect(DB_FILE)
    df_compras_db = pd.read_sql_query("SELECT * FROM compras", conn)
    conn.close()
    st.dataframe(df_compras_db, use_container_width=True)
    secao_edicao("compras", df_compras_db, ["produto", "qtd", "valor_total"], "produto")
    secao_exclusao("compras", df_compras_db, "produto")

elif opcao == "Clientes":
    st.title("Clientes")
    conn = sqlite3.connect(DB_FILE)
    df_cli = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    st.dataframe(df_cli, use_container_width=True)
    secao_edicao("clientes", df_cli, ["nome", "telefone", "cidade"], "nome")
    secao_exclusao("clientes", df_cli, "nome")

elif opcao == "Vendas":
    st.title("Vendas")
    conn = sqlite3.connect(DB_FILE)
    df_vendas_db = pd.read_sql_query("SELECT * FROM vendas", conn)
    conn.close()
    st.dataframe(df_vendas_db, use_container_width=True)
    secao_edicao("vendas", df_vendas_db, ["cliente", "produto", "qtd_kg", "valor_total"], "produto")
    secao_exclusao("vendas", df_vendas_db, "produto")

elif opcao == "Financeiro":
    st.title("Financeiro")
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    st.dataframe(df_fin, use_container_width=True)
    secao_edicao("financeiro", df_fin, ["descricao", "tipo", "valor"], "descricao")
    secao_exclusao("financeiro", df_fin, "descricao")

elif opcao == "Despesas Gerais":
    st.title("Despesas Gerais")
    conn = sqlite3.connect(DB_FILE)
    df_esp = pd.read_sql_query("SELECT * FROM despesas", conn)
    conn.close()
    st.dataframe(df_esp, use_container_width=True)
    secao_edicao("despesas", df_esp, ["categoria", "descricao", "valor", "pagamento"], "descricao")
    secao_exclusao("despesas", df_esp, "descricao")

elif opcao == "Contas a Pagar":
    st.title("Contas a Pagar")
    conn = sqlite3.connect(DB_FILE)
    df_cp = pd.read_sql_query("SELECT * FROM contas_pagar", conn)
    conn.close()
    st.dataframe(df_cp, use_container_width=True)
    secao_edicao("contas_pagar", df_cp, ["fornecedor", "descricao", "valor", "status"], "fornecedor")
    secao_exclusao("contas_pagar", df_cp, "fornecedor")

elif opcao == "Contas a Receber":
    st.title("Contas a Receber")
    conn = sqlite3.connect(DB_FILE)
    df_cr = pd.read_sql_query("SELECT * FROM contas_receber", conn)
    conn.close()
    st.dataframe(df_cr, use_container_width=True)
    secao_edicao("contas_receber", df_cr, ["cliente", "descricao", "valor", "status"], "cliente")
    secao_exclusao("contas_receber", df_cr, "cliente")

elif opcao == "Entregas":
    st.title("Entregas")
    conn = sqlite3.connect(DB_FILE)
    df_ent = pd.read_sql_query("SELECT * FROM entregas", conn)
    conn.close()
    st.dataframe(df_ent, use_container_width=True)
    secao_edicao("entregas", df_ent, ["pedido", "bairro", "entregador", "taxa_entrega"], "pedido")
    secao_exclusao("entregas", df_ent, "pedido")

      
