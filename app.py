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
            conn.commit()
            conn.close()
            st.success("Compra registrada com sucesso!")
            st.rerun()

    st.subheader("Histórico de Compras")
    conn = sqlite3.connect(DB_FILE)
    df_compras_db = pd.read_sql_query("SELECT * FROM compras", conn)
    conn.close()
    st.dataframe(df_compras_db, use_container_width=True)

# 4. ESTOQUE
elif opcao == "Estoque":
    st.title("Controle de Estoque Atualizado")
    conn = sqlite3.connect(DB_FILE)
    df_compras = pd.read_sql_query("SELECT produto, SUM(qtd) as total_comprado FROM compras GROUP BY produto", conn)
    df_vendas = pd.read_sql_query("SELECT produto, SUM(qtd_kg) as total_vendido FROM vendas GROUP BY produto", conn)
    conn.close()

    if not df_compras.empty:
        df_estoque = df_compras.merge(df_vendas, on="produto", how="left").fillna(0)
        df_estoque["Estoque Atual"] = df_estoque["total_comprado"] - df_estoque["total_vendido"]
        st.dataframe(df_estoque, use_container_width=True)
    else:
        st.info("Nenhuma compra registrada ainda.")

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
                c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)", (nome_cli, tel_cli, cidade_cli, datetime.now().strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("Cliente cadastrado!")
                st.rerun()
    conn = sqlite3.connect(DB_FILE)
    df_cli = pd.read_sql_query("SELECT * FROM clientes", conn)
    conn.close()
    st.dataframe(df_cli, use_container_width=True)

# 6. VENDAS
elif opcao == "Vendas":
    st.title("Registrar Venda e Histórico")
    with st.form("form_venda", clear_on_submit=True):
        cliente_nome = st.text_input("Nome do Cliente")
        produto_sel = st.selectbox("Produto", LISTA_PRODUTOS_MESTRA)
        qtd_kg = st.number_input("Quantidade", min_value=0.1, format="%.2f")
        preco_unit = st.number_input("Preço Unitário / KG (R$)", min_value=0.0, format="%.2f")
        
        if st.form_submit_button("Finalizar Venda"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            val_tot = qtd_kg * preco_unit
            c.execute("INSERT INTO vendas (cliente, produto, qtd_kg, valor_total, data_venda) VALUES (?, ?, ?, ?, ?)",
                      (cliente_nome if cliente_nome else "Balcão", produto_sel, qtd_kg, val_tot, datetime.now().strftime("%Y-%m-%d %H:%M")))
            c.execute("INSERT INTO financeiro (descricao, tipo, valor, data_mov) VALUES (?, ?, ?, ?)", (f"Venda: {produto_sel}", "Entrada", val_tot, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
            conn.close()
            st.success("Venda realizada!")
            st.rerun()

    conn = sqlite3.connect(DB_FILE)
    df_vendas_db = pd.read_sql_query("SELECT * FROM vendas", conn)
    conn.close()
    st.dataframe(df_vendas_db, use_container_width=True)

# 7. FINANCEIRO
elif opcao == "Financeiro":
    st.title("Controle Financeiro (Extrato de Caixa)")
    
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    if not df_fin.empty:
        # Filtros de Tipo de Movimentação
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Entrada", "Saída"])
        df_filtrado = df_fin if filtro_tipo == "Todos" else df_fin[df_fin["tipo"] == filtro_tipo]
        
        # Métricas de Resumo
        total_entradas = df_fin[df_fin["tipo"] == "Entrada"]["valor"].sum()
        total_saidas = df_fin[df_fin["tipo"] == "Saída"]["valor"].sum()
        saldo_geral = total_entradas - total_saidas
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Entradas", f"R$ {total_entradas:,.2f}")
        col2.metric("Total Saídas", f"R$ {total_saidas:,.2f}")
        col3.metric("Saldo em Caixa", f"R$ {saldo_geral:,.2f}")
        
        st.markdown("---")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.info("Nenhuma movimentação financeira registrada até o momento.")

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
                st.success("Despesa registrada!")
                st.rerun()
    conn = sqlite3.connect(DB_FILE)
    df_esp = pd.read_sql_query("SELECT * FROM despesas", conn)
    conn.close()
    st.dataframe(df_esp, use_container_width=True)

# 9. CONTAS A PAGAR
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
            st.success("Conta a pagar lançada com sucesso!")
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM contas_pagar", conn), use_container_width=True)
    conn.close()

# 10. CONTAS A RECEBER
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
            st.success("Conta a receber lançada com sucesso!")
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM contas_receber", conn), use_container_width=True)
    conn.close()

# 11. ENTREGAS
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
            st.success("Entrega registrada com sucesso!")
            st.rerun()
    conn = sqlite3.connect(DB_FILE)
    st.dataframe(pd.read_sql_query("SELECT * FROM entregas", conn), use_container_width=True)
    conn.close()

# 12. RELATÓRIOS
elif opcao == "Relatórios":
    st.title("Relatórios e Indicadores Gerenciais")
    
    conn = sqlite3.connect(DB_FILE)
    df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)
    df_despesas = pd.read_sql_query("SELECT * FROM despesas", conn)
    df_compras = pd.read_sql_query("SELECT * FROM compras", conn)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    st.subheader("📊 Resumo Consolidado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Vendas Registradas", len(df_vendas))
    c2.metric("Total de Despesas", f"R$ {df_despesas['valor'].sum() if not df_despesas.empty else 0.0:,.2f}")
    c3.metric("Total em Compras", f"R$ {df_compras['valor_total'].sum() if not df_compras.empty else 0.0:,.2f}")
    
    st.markdown("---")
    st.subheader("📋 Extrato Financeiro Completo (Entradas e Saídas)")
    if not df_fin.empty:
        st.dataframe(df_fin, use_container_width=True)
    else:
        st.info("Nenhuma movimentação financeira registrada.")
        
    st.markdown("---")
    st.subheader("📦 Vendas por Produto")
    if not df_vendas.empty:
        df_vendas_resumo = df_vendas.groupby("produto")[["qtd_kg", "valor_total"]].sum().reset_index()
        st.dataframe(df_vendas_resumo, use_container_width=True)
    else:
        st.info("Nenhuma venda realizada para gerar o relatório de produtos.")

# 13. NORMAS
elif opcao == "Normas":
    st.title("Normas e Procedimentos Operacionais - Kero Fish")
    
    st.markdown("""
    ### 1. Higiene e Manipulação de Pescados
    * **Uso de EPIs:** É obrigatório o uso de toucas, aventais impermeáveis, luvas adequadas e botas de borracha limpas durante o manuseio de peixes e frutos do mar.
    * **Cadeia de Frio:** O pescado fresco deve permanecer sob refrigeração adequada ou em contato direto com gelo limpo em escamas. O tempo de exposição em temperatura ambiente deve ser o menor possível.
    * **Limpeza e Sanitização:** As bancadas, facas, tábuas de corte e caixas térmicas devem ser rigorosamente higienizadas e sanitizadas antes e após o expediente ou na troca de turnos.

    ### 2. Controle de Estoque e Validade
    * **Método PEPS:** Utilize sempre o princípio **Primeiro a Entrar, Primeiro a Sair (PEPS)** para evitar perdas e garantir a rotação correta dos produtos armazenados.
    * **Conferência de Carga:** Toda mercadoria recebida de fornecedores deve passar por dupla conferência de peso, temperatura e integridade visual antes de dar entrada no sistema.

    ### 3. Atendimento ao Cliente e Vendas
    * **Cordialidade:** O atendimento deve ser ágil, prestativo e focado na excelência, tirando dúvidas sobre cortes, conservação e peso.
    * **Registro Rigoroso:** Nenhuma saída de mercadoria (venda, cortesia ou consumo interno) pode ser feita sem o devido lançamento imediato no sistema ERP para manter o estoque e o financeiro sincronizados.

    ### 4. Segurança Financeira e Caixa
    * **Fechamento Diário:** O caixa físico deve ser conferido diariamente e batido com os registros de entradas do sistema.
    * **Comprovantes:** Despesas pagas ou contas liquidadas exigem sempre o registro fotográfico ou o armazenamento do comprovante físico para fins de auditoria interna.
    """)

# 14. IMPORTAR PLANILHA
elif opcao == "Importar Planilha":
    st.title("Importação de Dados do Excel")
    st.write("Clique no botão abaixo para ler o arquivo do Excel que está na raiz e importar Fornecedores e Clientes para o banco de dados.")
    
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
                        for _, row in df.iterrows():
                            vals = [str(val) for val in row.values if pd.notna(val)]
                            if vals:
                                nome_f = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else "Desconhecido"
                                contato_f = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                                tel_f = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                                c.execute("INSERT INTO fornecedores (fornecedor, contato, telefone) VALUES (?, ?, ?)", (nome_f, contato_f, tel_f))
                        importadas.append(f"Fornecedores ({sheet_name})")

                    elif "cliente" in s_lower:
                        for _, row in df.iterrows():
                            vals = [str(val) for val in row.values if pd.notna(val)]
                            if vals:
                                nome_c = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else "Desconhecido"
                                tel_c = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                                cidade_c = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                                c.execute("INSERT INTO clientes (nome, telefone, cidade, data_cad) VALUES (?, ?, ?, ?)", 
                                          (nome_c, tel_c, cidade_c, datetime.now().strftime("%Y-%m-%d")))
                        importadas.append(f"Clientes ({sheet_name})")
                        
                conn.commit()
                conn.close()
                st.success(f"Planilha processada com sucesso! Abas importadas: {', '.join(importadas)}")
            except Exception as e:
                st.error(f"Erro ao ler a planilha: {e}")
        else:
            st.error("Arquivo do Excel não foi encontrado na raiz do projeto.")
       
