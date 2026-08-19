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
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "jpg.jpg"]:
    if os.path.exists(f"logo.{ext}"):
        logo_encontrada = f"logo.{ext}"
        break

if logo_encontrada:
    st.sidebar.image(logo_encontrada, use_container_width=True)
else:
    st.sidebar.warning("Atencao: Envie o arquivo da logo para a raiz com o nome 'logo.png'.")

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
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    total_faturado = df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
    total_vendas_qtd = len(df_vendas)
    total_despesas = df_despesas["valor"].sum() if not df_despesas.empty else 0.0
    
    entradas = df_fin[df_fin["tipo"] == "Entrada"]["valor"].sum() if not df_fin.empty else 0.0
    saidas = df_fin[df_fin["tipo"] == "Saída"]["valor"].sum() if not df_fin.empty else 0.0
    saldo_caixa = entradas - saidas
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Faturamento Vendas", f"R$ {total_faturado:,.2f}")
    col2.metric("Total Vendas", f"{total_vendas_qtd}")
    col3.metric("Total de Despesas", f"R$ {total_despesas:,.2f}")
    col4.metric("Saldo Caixa", f"R$ {saldo_caixa:,.2f}")

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
            else:
                st.error("O nome do fornecedor é obrigatório.")

    st.subheader("Lista de Fornecedores")
    conn = sqlite3.connect(DB_FILE)
    df_forn = pd.read_sql_query("SELECT * FROM fornecedores", conn)
    conn.close()
    st.dataframe(df_forn, use_container_width=True)

# 3. COMPRAS DE PRODUTOS
elif opcao == "Compras de produtos":
    st.title("Compras de Produtos e Histórico")
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

    st.subheader("Histórico de Compras")
    conn = sqlite3.connect(DB_FILE)
    df_compras_db = pd.read_sql_query("SELECT * FROM compras", conn)
    conn.close()
    st.dataframe(df_compras_db, use_container_width=True)

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
            
    st.subheader("Produtos em Estoque")
    conn = sqlite3.connect(DB_FILE)
    df_full = pd.read_sql_query("SELECT * FROM produtos", conn)
    conn.close()
    st.dataframe(df_full, use_container_width=True)

# 5. CLIENTES
elif opcao == "Clientes":
    st.title("Cadastro e Gestão de Clientes")
    with st.form("form_cliente", clear_on_submit=True):
        nome_cli = st.text_input("Nome do Cliente")
        tel_cli = st.text_input("Telefone")
        cidade_cli = st.text_input("Cidade")
        if st.form_submit_button("Cadastrar Cliente"):
            if nome_cli:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                hoje = datetime.now().strftime("%Y-%m-%d")
                c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)", (nome_cli, tel_cli, cidade_cli, hoje))
                conn.commit()
                conn.close()
                st.success("Cliente cadastrado com sucesso!")
            else:
                st.error("O nome do cliente é obrigatório.")
    conn = sqlite3.connect(DB_FILE)
    df_cli = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    st.dataframe(df_cli, use_container_width=True)

# 6. VENDAS
elif opcao == "Vendas":
    st.title("Registrar Venda e Histórico")
    conn = sqlite3.connect(DB_FILE)
    df_p = pd.read_sql_query("SELECT id, nome, preco_kg, estoque_kg FROM produtos", conn)
    conn.close()
    lista_produtos = df_p["nome"].tolist() if not df_p.empty else []
    
    with st.form("form_venda", clear_on_submit=True):
        cliente_nome = st.text_input("Nome do Cliente (Opcional)")
        produto_sel = st.selectbox("Produto", lista_produtos if lista_produtos else ["Cadastre produtos no estoque"])
        qtd_kg = st.number_input("Quantidade", min_value=0.1, format="%.2f")
        if st.form_submit_button("Finalizar Venda"):
            if lista_produtos:
                prod_info = df_p[df_p["nome"] == produto_sel].iloc[0]
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
            else:
                st.error("Cadastre produtos no estoque primeiro.")

    st.subheader("Histórico de Vendas")
    conn = sqlite3.connect(DB_FILE)
    df_vendas_db = pd.read_sql_query("SELECT * FROM vendas", conn)
    conn.close()
    st.dataframe(df_vendas_db, use_container_width=True)

# 7. FINANCEIRO
elif opcao == "Financeiro":
    st.title("Controle Financeiro (Entradas e Saídas)")
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
            if desc_esp and val_esp > 0:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                hoje = datetime.now().strftime("%Y-%m-%d")
                c.execute("INSERT INTO despesas (data_desp, categoria, descricao, valor, pagamento) VALUES (?, ?, ?, ?, ?)", (hoje, "Geral", desc_esp, val_esp, "Dinheiro"))
                c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", (f"Despesa: {desc_esp}", "Saída", val_esp, hoje))
                conn.commit()
                conn.close()
                st.success("Despesa registrada com sucesso!")
            else:
                st.error("Preencha a descrição e o valor corretamente.")
    
    st.subheader("Histórico de Despesas")
    conn = sqlite3.connect(DB_FILE)
    df_esp = pd.read_sql_query("SELECT * FROM despesas", conn)
    conn.close()
    st.dataframe(df_esp, use_container_width=True)

# 9. CONTAS A PAGAR
elif opcao == "Contas a Pagar":
    st.title("Contas a Pagar")
    conn = sqlite3.connect(DB_FILE)
    df_cp = pd.read_sql_query("SELECT * FROM contas_pagar", conn)
    conn.close()
    st.dataframe(df_cp, use_container_width=True)

# 10. CONTAS A RECEBER
elif opcao == "Contas a Receber":
    st.title("Contas a Receber")
    conn = sqlite3.connect(DB_FILE)
    df_cr = pd.read_sql_query("SELECT * FROM contas_receber", conn)
    conn.close()
    st.dataframe(df_cr, use_container_width=True)

# 11. ENTREGAS
elif opcao == "Entregas":
    st.title("Controle de Entregas")
    conn = sqlite3.connect(DB_FILE)
    df_ent = pd.read_sql_query("SELECT * FROM entregas", conn)
    conn.close()
    st.dataframe(df_ent, use_container_width=True)

# 12. RELATÓRIOS
elif opcao == "Relatórios":
    st.title("Relatórios do Sistema")
    st.info("Módulo de relatórios gerenciais.")

# 13. NORMAS
elif opcao == "Normas":
    st.title("Normas e Procedimentos")
    st.info("Documentação interna e normas operacionais.")

# 14. IMPORTAR PLANILHA
elif opcao == "Importar Planilha":
    st.title("Importação Completa de Dados da Planilha Antiga")
    st.write("Certifique-se de que o arquivo `KERO FISH_Financeira_Completa_Preenchida-4.xlsx` está enviado na raiz do projeto no GitHub.")
    
    if st.button("Confirmar Importação de Todas as Abas"):
        try:
            if not os.path.exists("KERO FISH_Financeira_Completa_Preenchida-4.xlsx"):
                st.error("O arquivo Excel 'KERO FISH_Financeira_Completa_Preenchida-4.xlsx' não foi encontrado na raiz do projeto.")
            else:
                xls = pd.ExcelFile("KERO FISH_Financeira_Completa_Preenchida-4.xlsx")
                abas_disponiveis = xls.sheet_names
                
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                
                # 1. Vendas & Extração de Clientes
                if "Vendas" in abas_disponiveis:
                    try:
                        df_v = pd.read_excel(xls, sheet_name="Vendas")
                        for _, r in df_v.iterrows():
                            prod = r.get("Produto")
                            if pd.notna(prod):
                                data_v = str(r.get("Data", ""))[:10]
                                cliente_nome = r.get("Cliente", "Cliente Balcão")
                                if pd.isna(cliente_nome) or str(cliente_nome).strip() == "":
                                    cliente_nome = "Cliente Balcão"
                                    
                                c.execute("INSERT INTO vendas (cliente, produto, qtd_kg, valor_total, data_venda) VALUES (?, ?, ?, ?, ?)",
                                          (str(cliente_nome), str(prod), r.get("Quantidade", 0.0), r.get("Valor Venda", 0.0), data_v))
                                
                                # Cadastrar cliente automaticamente se não existir
                                c.execute("SELECT id FROM clientes WHERE nome = ?", (str(cliente_nome),))
                                if not c.fetchone() and cliente_nome != "Cliente Balcão":
                                    c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)",
                                              (str(cliente_nome), "", "", datetime.now().strftime("%Y-%m-%d")))
                    except Exception as ex: st.warning(f"Vendas: {ex}")

                # 2. Compras
                if "Compras" in abas_disponiveis:
                    try:
                        df_c = pd.read_excel(xls, sheet_name="Compras")
                        for _, r in df_c.iterrows():
                            if pd.notna(r.get("Produto")):
                                data_c = str(r.get("Data", ""))[:10]
                                c.execute("INSERT INTO compras (produto, qtd, valor_total, data_compra) VALUES (?, ?, ?, ?)",
                                          (str(r.get("Produto")), r.get("Quantidade Comprada (KG)", 0.0), r.get("Valor Total", 0.0), data_c))
                    except Exception as ex: st.warning(f"Compras: {ex}")

                # 3. Estoque
                if "Estoque" in abas_disponiveis:
                    try:
                        df_e = pd.read_excel(xls, sheet_name="Estoque")
                        for _, r in df_e.iterrows():
                            p_nome = r.get("Produto")
                            p_qtd = r.get("Estoque Atual", 0.0)
                            if pd.notna(p_nome):
                                c.execute("SELECT id FROM produtos WHERE nome = ?", (str(p_nome),))
                                if c.fetchone():
                                    c.execute("UPDATE produtos SET estoque_kg = ? WHERE nome = ?", (p_qtd, str(p_nome)))
                                else:
                                    c.execute("INSERT INTO produtos (nome, categoria, preco_kg, estoque_kg) VALUES (?, ?, ?, ?)", (str(p_nome), "Geral", 0.0, p_qtd))
                    except Exception as ex: st.warning(f"Estoque: {ex}")

                # 4. Despesas
                if "Despesas" in abas_disponiveis:
                    try:
                        df_d = pd.read_excel(xls, sheet_name="Despesas")
                        for _, r in df_d.iterrows():
                            desc = r.get("Descrição")
                            valor = r.get("Valor")
                            if pd.notna(desc) and pd.notna(valor):
                                data_d = str(r.get("Data", ""))[:10]
                                cat = r.get("Categoria", "Geral")
                                pag = r.get("Forma Pagamento", "Dinheiro")
                                c.execute("INSERT INTO despesas (data_desp, categoria, descricao, valor, pagamento) VALUES (?, ?, ?, ?, ?)", (data_d, str(cat), str(desc), valor, str(pag)))
                                c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", (f"Despesa: {desc}", "Saída", valor, data_d))
                    except Exception as ex: st.warning(f"Despesas: {ex}")

                # 5. Fornecedores
                if "Fornecedores" in abas_disponiveis:
                    try:
                        df_f = pd.read_excel(xls, sheet_name="Fornecedores")
                        for _, r in df_f.iterrows():
                            forn = r.get("Fornecedor")
                            if pd.notna(forn):
                                c.execute("INSERT INTO fornecedores (fornecedor, contato, telefone, endereco, produto_fornecido, prazo_pagamento, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                          (str(forn), str(r.get("Contato", "")), str(r.get("Telefone", "")), str(r.get("ENDEREÇO", "")), str(r.get("Produto Fornecido", "")), str(r.get("Prazo Pagamento", "")), str(r.get("Observações", ""))))
                    except Exception as ex: st.warning(f"Fornecedores: {ex}")

                # 6. Contas_Pagar
                if "Contas_Pagar" in abas_disponiveis:
                    try:
                        df_cp = pd.read_excel(xls, sheet_name="Contas_Pagar")
                        for _, r in df_cp.iterrows():
                            forn_p = r.get("Fornecedor") or r.get("Fornecedores")
                            if pd.notna(forn_p) or pd.notna(r.get("Descrição")):
                                c.execute("INSERT INTO contas_pagar (fornecedor, descricao, valor, vencimento, status, data_pagamento) VALUES (?, ?, ?, ?, ?, ?)",
                                          (str(forn_p), str(r.get("Descrição", "")), r.get("Valor", 0.0), str(r.get("Vencimento", ""))[:10], str(r.get("Status", "")), str(r.get("Data Pagamento", ""))[:10]))
                    except Exception as ex: st.warning(f"Contas_Pagar: {ex}")

                # 7. Contas_Receber
                if "Contas_Receber" in abas_disponiveis:
                    try:
                        df_cr = pd.read_excel(xls, sheet_name="Contas_Receber")
                        for _, r in df_cr.iterrows():
                            cli_r = r.get("Cliente")
                            if pd.notna(cli_r) or pd.notna(r.get("Descrição")):
                                c.execute("INSERT INTO contas_receber (cliente, descricao, valor, vencimento, status, data_recebimento) VALUES (?, ?, ?, ?, ?, ?)",
                                          (str(cli_r), str(r.get("Descrição", "")), r.get("Valor", 0.0), str(r.get("Vencimento", ""))[:10], str(r.get("Status", "")), str(r.get("Data Recebimento", ""))[:10]))
                    except Exception as ex: st.warning(f"Contas_Receber: {ex}")

                # 8. Entregas
                if "Entregas" in abas_disponiveis:
                    try:
                        df_ent = pd.read_excel(xls, sheet_name="Entregas")
                        for _, r in df_ent.iterrows():
                            data_ent = str(r.get("Data", ""))[:10]
                            if pd.notna(r.get("Pedido")) or pd.notna(r.get("Bairro")):
                                c.execute("INSERT INTO entregas (data_ent, pedido, bairro, entregador, taxa_entrega, custo_combustivel, lucro_entrega) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                          (data_ent, str(r.get("Pedido", "")), str(r.get("Bairro", "")), str(r.get("Entregador", "")), r.get("Taxa Entrega", 0.0), r.get("Custo Combustivel", 0.0), r.get("Lucro Entrega", 0.0)))
                    except Exception as ex: st.warning(f"Entregas: {ex}")

                conn.commit()
                conn.close()
                st.success("Importação completa e refinada realizada com sucesso!")
        except Exception as e:
            st.error(f"Erro geral durante a importação: {e}")
