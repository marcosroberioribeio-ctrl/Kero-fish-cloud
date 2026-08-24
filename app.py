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
    st.sidebar.warning("Atenção: Envie o arquivo da logo para a raiz ou carregue abaixo.")
    uploaded_logo = st.sidebar.file_uploader("Enviar arquivo da logo", type=["png", "jpg", "jpeg"])
    if uploaded_logo is not None:
        with open("logo.png", "wb") as f:
            f.write(uploaded_logo.getbuffer())
        st.success("Logo salva com sucesso! Atualizando...")
        st.rerun()

opcao = st.sidebar.radio(
    "Navegação", 
    [
        "Painel Geral", "Fornecedores", "Compras de produtos", "Estoque", 
        "Clientes", "Vendas", "Financeiro", "Despesas Gerais", 
        "Contas a Pagar", "Contas a Receber", "Entregas", "Relatórios", "Normas", "Importar Planilha"
    ]
)

# --- Função genérica para Grid Editável (Salvar alterações na tabela) ---
def renderizar_tabela_editavel(tabela, nome_exibicao):
    st.subheader(f"Gerenciamento de {nome_exibicao}")
    st.info("💡 Você pode editar os dados diretamente na tabela abaixo ou excluir linhas selecionando-as. Clique em 'Salvar Alterações' para gravar no banco.")
    
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
    conn.close()
    
    # st.data_editor permite edição direta, adição e exclusão de linhas
    df_editado = st.data_editor(df, num_rows="dynamic", key=f"editor_{tabela}", use_container_width=True)
    
    if st.button(f"💾 Salvar Alterações em {nome_exibicao}", key=f"btn_save_{tabela}"):
        conn = sqlite3.connect(DB_FILE)
        try:
            # Substitui os dados da tabela com base no DataFrame editado na tela
            df_editado.to_sql(tabela, conn, if_exists="replace", index=False)
            st.success(f"Alterações em {nome_exibicao} salvas com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar os dados: {e}")
        finally:
            conn.close()

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
    renderizar_tabela_editavel("fornecedores", "Fornecedores")

# 3. COMPRAS DE PRODUTOS
elif opcao == "Compras de produtos":
    st.title("Compras de Produtos e Histórico")
    renderizar_tabela_editavel("compras", "Compras")

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
    renderizar_tabela_editavel("clientes", "Clientes")

# 6. VENDAS
elif opcao == "Vendas":
    st.title("Registro de Vendas e Histórico")
    renderizar_tabela_editavel("vendas", "Vendas")

# 7. FINANCEIRO
elif opcao == "Financeiro":
    st.title("Controle Financeiro")
    
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    if not df_fin.empty:
        total_entradas = df_fin[df_fin["tipo"] == "Entrada"]["valor"].sum()
        total_saidas = df_fin[df_fin["tipo"] == "Saída"]["valor"].sum()
        saldo_caixa = total_entradas - total_saidas
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Entradas", f"R$ {total_entradas:,.2f}")
        col2.metric("Saídas", f"R$ {total_saidas:,.2f}")
        col3.metric("Saldo Líquido", f"R$ {saldo_caixa:,.2f}")
        
        st.markdown("---")
    
    renderizar_tabela_editavel("financeiro", "Movimentações Financeiras")

# 8. DESPESAS GERAIS
elif opcao == "Despesas Gerais":
    st.title("Registro de Despesas Gerais")
    renderizar_tabela_editavel("despesas", "Despesas")

# 9. CONTAS A PAGAR
elif opcao == "Contas a Pagar":
    st.title("Contas a Pagar")
    renderizar_tabela_editavel("contas_pagar", "Contas a Pagar")

# 10. CONTAS A RECEBER
elif opcao == "Contas a Receber":
    st.title("Contas a Receber")
    renderizar_tabela_editavel("contas_receber", "Contas a Receber")

# 11. ENTREGAS
elif opcao == "Entregas":
    st.title("Controle de Entregas")
    renderizar_tabela_editavel("entregas", "Entregas")

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
    * **Uso de EPIs:** Obrigatório o uso de toucas, aventais impermeáveis, luvas adequadas e botas de borracha limpas durante o manuseio de peixes e frutos do mar.
    * **Cadeia de Frio:** O pescado fresco deve permanecer sob refrigeração adequada ou em contato direto com gelo limpo em escamas.
    * **Limpeza:** Bancadas, facas, tábuas de corte e caixas térmicas devem ser rigorosamente higienizadas antes e após o expediente.

    ### 2. Controle de Estoque e Validade
    * **Método PEPS:** Utilize sempre o princípio **Primeiro a Entrar, Primeiro a Sair (PEPS)** para correta rotação dos produtos.
    * **Conferência:** Toda mercadoria recebida deve passar por dupla conferência de peso, temperatura e integridade antes do aceite.

    ### 3. Atendimento e Vendas
    * **Cordialidade:** Atendimento ágil e prestativo, auxiliando o cliente com informações sobre cortes e conservação.
    * **Registro Rigoroso:** Nenhuma saída de mercadoria pode ser feita sem o devido lançamento imediato no ERP.
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

