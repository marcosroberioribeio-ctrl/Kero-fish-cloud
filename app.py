# -*- coding: utf-8 -*-
"""
Kero Fish ERP - versão 10.3 - Correção Definitiva de Inserção
"""

import os
import shutil
import sqlite3
from datetime import datetime, date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Kero Fish ERP", layout="wide")

DB_FILE = "kerofish.db"
BACKUP_DIR = "backups"

FORMAS_PAGAMENTO = [
    "Dinheiro",
    "Pix",
    "Cartão de débito",
    "Cartão de crédito",
    "Transferência",
    "A prazo",
]

STATUS_PAGAMENTO = ["Pago", "Pendente", "Parcial"]
STATUS_ENTREGA = ["Aguardando", "Em separação", "Saiu para entrega", "Entregue", "Cancelado"]

CATEGORIAS_PRODUTO = [
    "Peixe",
    "Camarão",
    "Frutos do mar",
    "Castanha",
    "Ovos",
    "Mel",
    "Cajuína",
    "Manteiga da terra",
    "Temperos",
    "Molhos",
    "Outros",
]

PRODUTOS_INICIAIS = [
    ("Tilápia filé", "Peixe"),
    ("Tilápia inteiro", "Peixe"),
    ("Salmão filé", "Peixe"),
    ("Pargo filé", "Peixe"),
    ("Pargo inteiro", "Peixe"),
    ("Atum", "Peixe"),
    ("Sardinha eviscerada", "Peixe"),
    ("Camarão M", "Camarão"),
    ("Camarão G", "Camarão"),
    ("Camarão GG", "Camarão"),
    ("Camarão filé M", "Camarão"),
    ("Camarão filé G", "Camarão"),
    ("Camarão filé GG", "Camarão"),
    ("Castanha de caju assada caseira", "Castanha"),
    ("Castanha caramelizada 100g", "Castanha"),
    ("Castanha caramelizada 200g", "Castanha"),
    ("Castanha assada 100g", "Castanha"),
    ("Castanha assada 200g", "Castanha"),
    ("Ovos caipira", "Ovos"),
    ("Ovos comum", "Ovos"),
    ("Mel", "Mel"),
    ("Cajuína", "Cajuína"),
    ("Manteiga da terra", "Manteiga da terra"),
    ("Temperos", "Temperos"),
    ("Molhos", "Molhos"),
]

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def column_exists(conn, table, column):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)

def add_column_if_missing(conn, table, column, definition):
    if not column_exists(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT DEFAULT '',
            cidade TEXT DEFAULT '',
            endereco TEXT DEFAULT '',
            data_cad TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            contato TEXT DEFAULT '',
            telefone TEXT DEFAULT '',
            endereco TEXT DEFAULT '',
            produto_fornecido TEXT DEFAULT '',
            prazo_pagamento TEXT DEFAULT '',
            observacoes TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT DEFAULT 'Outros',
            unidade TEXT DEFAULT 'kg',
            preco_venda REAL DEFAULT 0,
            custo_medio REAL DEFAULT 0,
            estoque_minimo REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT DEFAULT '',
            produto TEXT NOT NULL,
            qtd REAL DEFAULT 0,
            preco_kg REAL DEFAULT 0,
            valor_total REAL DEFAULT 0,
            data_compra TEXT DEFAULT '',
            lote TEXT DEFAULT '',
            validade TEXT DEFAULT '',
            forma_pagamento TEXT DEFAULT 'A prazo',
            status_pagamento TEXT DEFAULT 'Pendente',
            vencimento TEXT DEFAULT '',
            observacoes TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido TEXT,
            cliente TEXT DEFAULT '',
            produto TEXT NOT NULL,
            qtd_kg REAL DEFAULT 0,
            preco_kg REAL DEFAULT 0,
            desconto REAL DEFAULT 0,
            valor_total REAL DEFAULT 0,
            data_venda TEXT DEFAULT '',
            forma_pagamento TEXT DEFAULT 'Pix',
            status_pagamento TEXT DEFAULT 'Pago',
            valor_recebido REAL DEFAULT 0,
            vencimento TEXT DEFAULT '',
            observacoes TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_desp TEXT DEFAULT '',
            categoria TEXT DEFAULT '',
            descricao TEXT DEFAULT '',
            valor REAL DEFAULT 0,
            pagamento TEXT DEFAULT 'Pix',
            status TEXT DEFAULT 'Pago',
            vencimento TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT DEFAULT '',
            descricao TEXT DEFAULT '',
            valor REAL DEFAULT 0,
            valor_pago REAL DEFAULT 0,
            vencimento TEXT DEFAULT '',
            status TEXT DEFAULT 'Pendente',
            origem_tipo TEXT DEFAULT '',
            origem_id INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT DEFAULT '',
            descricao TEXT DEFAULT '',
            valor REAL DEFAULT 0,
            valor_recebido REAL DEFAULT 0,
            vencimento TEXT DEFAULT '',
            status TEXT DEFAULT 'Pendente',
            origem_tipo TEXT DEFAULT '',
            origem_id INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS entregas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido TEXT DEFAULT '',
            cliente TEXT DEFAULT '',
            data_ent TEXT DEFAULT '',
            endereco TEXT DEFAULT '',
            bairro TEXT DEFAULT '',
            cidade TEXT DEFAULT '',
            entregador TEXT DEFAULT '',
            taxa_entrega REAL DEFAULT 0,
            status TEXT DEFAULT 'Aguardando',
            observacoes TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_mov TEXT DEFAULT '',
            descricao TEXT DEFAULT '',
            tipo TEXT DEFAULT 'Entrada',
            valor REAL DEFAULT 0,
            forma_pagamento TEXT DEFAULT '',
            origem_tipo TEXT DEFAULT '',
            origem_id INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS movimentos_estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_mov TEXT DEFAULT '',
            produto TEXT NOT NULL,
            tipo TEXT NOT NULL,
            quantidade REAL DEFAULT 0,
            custo_unitario REAL DEFAULT 0,
            origem_tipo TEXT DEFAULT '',
            origem_id INTEGER,
            observacoes TEXT DEFAULT ''
        )
    """)

    # Migrações seguras
    add_column_if_missing(conn, "clientes", "endereco", "TEXT DEFAULT ''")
    add_column_if_missing(conn, "produtos", "unidade", "TEXT DEFAULT 'kg'")
    add_column_if_missing(conn, "produtos", "preco_venda", "REAL DEFAULT 0")
    add_column_if_missing(conn, "produtos", "custo_medio", "REAL DEFAULT 0")
    add_column_if_missing(conn, "produtos", "estoque_minimo", "REAL DEFAULT 0")
    add_column_if_missing(conn, "produtos", "ativo", "INTEGER DEFAULT 1")
    add_column_if_missing(conn, "contas_pagar", "valor_pago", "REAL DEFAULT 0")
    add_column_if_missing(conn, "contas_receber", "valor_recebido", "REAL DEFAULT 0")

    for nome, categoria in PRODUTOS_INICIAIS:
        existe = conn.execute("SELECT id FROM produtos WHERE nome = ?", (nome,)).fetchone()
        if not existe:
            conn.execute(
                "INSERT INTO produtos (nome, categoria, unidade) VALUES (?, ?, 'kg')",
                (nome, categoria),
            )

    conn.commit()
    conn.close()

def backup_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(BACKUP_DIR, f"kerofish_backup_{stamp}.db")
    if os.path.exists(DB_FILE):
        shutil.copy2(DB_FILE, destino)
        return destino
    return None

def df_query(sql, params=()):
    conn = get_conn()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()

def scalar(sql, params=()):
    conn = get_conn()
    try:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else 0
    finally:
        conn.close()

def moeda(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def hoje():
    return date.today().strftime("%Y-%m-%d")

def proximo_pedido():
    ultimo = scalar("SELECT MAX(id) FROM vendas") or 0
    return f"KF-{datetime.now().year}-{int(ultimo)+1:06d}"

def get_produtos():
    return df_query("SELECT * FROM produtos WHERE ativo=1 ORDER BY nome")

def resumo_estoque():
    produtos = get_produtos()
    registros = []
    for _, r in produtos.iterrows():
        produto = r["nome"]
        compras = float(scalar("SELECT COALESCE(SUM(qtd),0) FROM compras WHERE produto=?", (produto,)) or 0)
        vendas = float(scalar("SELECT COALESCE(SUM(qtd_kg),0) FROM vendas WHERE produto=?", (produto,)) or 0)
        ajuste_ent = float(scalar("SELECT COALESCE(SUM(quantidade),0) FROM movimentos_estoque WHERE produto=? AND origem_tipo='manual' AND tipo='Ajuste Entrada'", (produto,)) or 0)
        ajuste_saida = float(scalar("SELECT COALESCE(SUM(quantidade),0) FROM movimentos_estoque WHERE produto=? AND origem_tipo='manual' AND tipo IN ('Ajuste Saída','Perda')", (produto,)) or 0)
        estoque = compras - vendas + ajuste_ent - ajuste_saida
        minimo = float(r["estoque_minimo"] or 0)
        registros.append({
            "Produto": produto,
            "Categoria": r["categoria"],
            "Compras": compras,
            "Vendas": vendas,
            "Estoque atual": estoque,
            "Mínimo": minimo,
            "Situação": "⚠️ BAIXO" if estoque <= minimo else "OK",
        })
    return pd.DataFrame(registros)

def registrar_movimento(produto, tipo, quantidade, custo=0, origem_tipo="", origem_id=None, observacoes=""):
    if quantidade <= 0:
        return
    conn = get_conn()
    conn.execute("""
        INSERT INTO movimentos_estoque
        (data_mov, produto, tipo, quantidade, custo_unitario, origem_tipo, origem_id, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (hoje(), produto, tipo, quantidade, custo, origem_tipo, origem_id, observacoes))
    conn.commit()
    conn.close()

def registrar_financeiro(data_mov, descricao, tipo, valor, forma_pagamento="", origem_tipo="", origem_id=None):
    if valor <= 0:
        return
    conn = get_conn()
    conn.execute("""
        INSERT INTO financeiro
        (data_mov, descricao, tipo, valor, forma_pagamento, origem_tipo, origem_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data_mov, descricao, tipo, valor, forma_pagamento, origem_tipo, origem_id))
    conn.commit()
    conn.close()

def garantir_conta_pagar(fornecedor, descricao, valor, vencimento, origem_tipo="", origem_id=None, valor_pago=0):
    valor = float(valor or 0)
    valor_pago = min(max(float(valor_pago or 0), 0), valor)
    if valor <= 0:
        return None
    status = "Pago" if valor_pago >= valor else ("Parcial" if valor_pago > 0 else "Pendente")
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO contas_pagar
        (fornecedor, descricao, valor, valor_pago, vencimento, status, origem_tipo, origem_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fornecedor, descricao, valor, valor_pago, vencimento, status, origem_tipo, origem_id))
    conta_id = cur.lastrowid
    conn.commit()
    conn.close()
    return conta_id

def garantir_conta_receber(cliente, descricao, valor, vencimento, origem_tipo="", origem_id=None, valor_recebido=0):
    valor = float(valor or 0)
    valor_recebido = min(max(float(valor_recebido or 0), 0), valor)
    if valor <= 0:
        return None
    status = "Pago" if valor_recebido >= valor else ("Parcial" if valor_recebido > 0 else "Pendente")
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO contas_receber
        (cliente, descricao, valor, valor_recebido, vencimento, status, origem_tipo, origem_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (cliente, descricao, valor, valor_recebido, vencimento, status, origem_tipo, origem_id))
    conta_id = cur.lastrowid
    conn.commit()
    conn.close()
    return conta_id

def renderizar_tabela_simples(tabela, titulo, colunas_ocultar=None):
    st.subheader(titulo)
    df = df_query(f"SELECT * FROM {tabela} ORDER BY id DESC")
    if colunas_ocultar:
        df = df.drop(columns=[c for c in colunas_ocultar if c in df.columns])
    if df.empty:
        st.info("Nenhum registro encontrado.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

def main():
    init_db()

    st.sidebar.title("🐟 Kero Fish ERP")
    st.sidebar.caption("Versão 10.3 — Estável")

    menu = st.sidebar.selectbox(
        "Navegação",
        [
            "Painel Gerencial",
            "Produtos",
            "Clientes",
            "Fornecedores",
            "Compras",
            "Vendas",
            "Despesas",
            "Estoque",
            "Financeiro & Caixa",
            "Contas a Pagar/Receber",
            "Entregas",
            "Importar/Exportar",
            "Backup & Restaurar",
        ],
    )

    if menu == "Painel Gerencial":
        st.title("📊 Painel Gerencial")
        
        vendas_tot = scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Entrada'")
        compras_tot = scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Saída'")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas Totais (Caixa)", moeda(vendas_tot))
        c2.metric("Saídas Totais (Caixa)", moeda(compras_tot))
        c3.metric("Saldo Atual em Caixa", moeda(vendas_tot - compras_tot))

        st.markdown("---")
        st.subheader("⚠️ Alertas de Estoque Mínimo")
        df_est = resumo_estoque()
        baixos = df_est[df_est["Situação"].str.contains("BAIXO")]
        if baixos.empty:
            st.success("Nenhum produto abaixo do estoque mínimo.")
        else:
            st.dataframe(baixos, use_container_width=True, hide_index=True)

    elif menu == "Produtos":
        st.title("📦 Cadastro de Produtos")
        with st.form("form_produto"):
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Nome do Produto")
            categoria = c2.selectbox("Categoria", CATEGORIAS_PRODUTO)
            unidade = c3.selectbox("Unidade", ["kg", "un", "pct", "L", "frasco"])
            c4, c5, c6 = st.columns(3)
            preco = c4.number_input("Preço de Venda (R$)", min_value=0.0, format="%.2f")
            custo = c5.number_input("Custo Médio (R$)", min_value=0.0, format="%.2f")
            minimo = c6.number_input("Estoque Mínimo", min_value=0.0, format="%.2f")
            if st.form_submit_button("Cadastrar Produto"):
                if nome.strip():
                    try:
                        conn = get_conn()
                        conn.execute(
                            "INSERT INTO produtos (nome, categoria, unidade, preco_venda, custo_medio, estoque_minimo) VALUES (?,?,?,?,?,?)",
                            (nome.strip(), categoria, unidade, preco, custo, minimo)
                        )
                        conn.commit()
                        conn.close()
                        st.success("Produto cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar produto: {e}")
                else:
                    st.warning("Informe o nome do produto.")

        renderizar_tabela_simples("produtos", "Lista de Produtos Ativos")

    elif menu == "Clientes":
        st.title("👥 Cadastro de Clientes")
        with st.form("form_cliente"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome do Cliente")
            telefone = c2.text_input("Telefone")
            c3, c4 = st.columns(2)
            cidade = c3.text_input("Cidade")
            endereco = c4.text_input("Endereço completo")
            if st.form_submit_button("Salvar Cliente"):
                if nome.strip():
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO clientes (nome, telefone, cidade, endereco, data_cad) VALUES (?,?,?,?,?)",
                        (nome.strip(), telefone, cidade, endereco, hoje())
                    )
                    conn.commit()
                    conn.close()
                    st.success("Cliente cadastrado!")
                    st.rerun()
                else:
                    st.warning("O nome do cliente é obrigatório.")

        renderizar_tabela_simples("clientes", "Clientes Cadastrados")

    elif menu == "Fornecedores":
        st.title("🏭 Cadastro de Fornecedores")
        with st.form("form_forn"):
            c1, c2 = st.columns(2)
            fornecedor = c1.text_input("Nome do Fornecedor")
            contato = c2.text_input("Contato responsável")
            c3, c4 = st.columns(2)
            telefone = c3.text_input("Telefone")
            produto_fornecido = c4.text_input("Produto fornecido principal")
            observacoes = st.text_area("Observações")
            if st.form_submit_button("Salvar Fornecedor"):
                if fornecedor.strip():
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO fornecedores (fornecedor, contato, telefone, produto_fornecido, observacoes) VALUES (?,?,?,?,?)",
                        (fornecedor.strip(), contato, telefone, produto_fornecido, observacoes)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Fornecedor cadastrado!")
                    st.rerun()
                else:
                    st.warning("Informe o nome do fornecedor.")

        renderizar_tabela_simples("fornecedores", "Fornecedores Cadastrados")

    elif menu == "Compras":
        st.title("🛒 Registro de Compras & Entradas")
        df_p = get_produtos()
        lista_prod = df_p["nome"].tolist() if not df_p.empty else []
        df_f = df_query("SELECT fornecedor FROM fornecedores ORDER BY fornecedor")
        lista_forn = df_f["fornecedor"].tolist() if not df_f.empty else ["Geral"]

        with st.form("form_compra"):
            c1, c2 = st.columns(2)
            fornecedor = c1.selectbox("Fornecedor", lista_forn)
            produto = c2.selectbox("Produto", lista_prod)
            c3, c4, c5 = st.columns(3)
            qtd = c3.number_input("Quantidade (kg/un)", min_value=0.01, format="%.2f")
            preco_kg = c4.number_input("Custo Unitário / Preço kg (R$)", min_value=0.0, format="%.2f")
            data_compra = c5.date_input("Data da Compra", value=date.today())

            c6, c7, c8 = st.columns(3)
            lote = c6.text_input("Lote")
            validade = c7.date_input("Validade", value=date.today())
            forma = c8.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO)

            c9, c10 = st.columns(2)
            status_pag = c9.selectbox("Status Pagamento", STATUS_PAGAMENTO)
            vencimento = c10.date_input("Vencimento", value=date.today())
            obs = st.text_area("Observações da Compra")

            if st.form_submit_button("Registrar Compra"):
                if produto:
                    total = qtd * preco_kg
                    conn = get_conn()
                    cur = conn.execute("""
                        INSERT INTO compras (fornecedor, produto, qtd, preco_kg, valor_total, data_compra, lote, validade, forma_pagamento, status_pagamento, vencimento, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (fornecedor, produto, qtd, preco_kg, total, str(data_compra), lote, str(validade), forma, status_pag, str(vencimento), obs))
                    cid = cur.lastrowid
                    conn.commit()
                    conn.close()

                    registrar_movimento(produto, "Entrada", qtd, preco_kg, "compra", cid, f"Lote: {lote}")
                    if status_pag == "Pago":
                        registrar_financeiro(str(data_compra), f"Compra #{cid}: {produto}", "Saída", total, forma, "compra", cid)
                    else:
                        garantir_conta_pagar(fornecedor, f"Compra #{cid}: {produto}", total, str(vencimento), "compra", cid)

                    st.success("Compra registrada com sucesso!")
                    st.rerun()

        renderizar_tabela_simples("compras", "Histórico de Compras")

    elif menu == "Vendas":
        st.title("💰 Registro de Vendas & Pedidos")
        df_p = get_produtos()
        lista_prod = df_p["nome"].tolist() if not df_p.empty else []
        df_c = df_query("SELECT nome FROM clientes ORDER BY nome")
        lista_cli = df_c["nome"].tolist() if not df_c.empty else ["Balcão"]

        novo_ped = proximo_pedido()
        st.info(f"Número do próximo pedido sugerido: **{novo_ped}**")

        with st.form("form_venda"):
            c1, c2, c3 = st.columns(3)
            pedido = c1.text_input("Código do Pedido", value=novo_ped)
            cliente = c2.selectbox("Cliente", lista_cli)
            produto = c3.selectbox("Produto", lista_prod)

            c4, c5, c6 = st.columns(3)
            qtd_kg = c4.number_input("Quantidade (kg/un)", min_value=0.01, format="%.2f")
            preco_kg = c5.number_input("Preço de Venda / kg (R$)", min_value=0.0, format="%.2f")
            desconto = c6.number_input("Desconto (R$)", min_value=0.0, format="%.2f")

            c7, c8, c9 = st.columns(3)
            data_venda = c7.date_input("Data da Venda", value=date.today())
            forma = c8.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO)
            recebido = c9.number_input("Valor já recebido (R$)", min_value=0.0, format="%.2f")

            c10, c11 = st.columns(2)
            vencimento = c10.date_input("Vencimento do saldo", value=date.today())
            obs = c11.text_input("Observações / Endereço de entrega")

            if st.form_submit_button("Finalizar Venda"):
                if produto:
                    bruto = qtd_kg * preco_kg
                    total = max(0.0, bruto - desconto)
                    status_pag = "Pago" if recebido >= total else ("Parcial" if recebido > 0 else "Pendente")

                    conn = get_conn()
                    cur = conn.execute("""
                        INSERT INTO vendas (pedido, cliente, produto, qtd_kg, preco_kg, desconto, valor_total, data_venda, forma_pagamento, status_pagamento, valor_recebido, vencimento, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (pedido, cliente, produto, qtd_kg, preco_kg, desconto, total, str(data_venda), forma, status_pag, recebido, str(vencimento), obs))
                    vid = cur.lastrowid
                    conn.commit()
                    conn.close()

                    registrar_movimento(produto, "Saída", qtd_kg, preco_kg, "venda", vid, pedido)
                    if recebido > 0:
                        registrar_financeiro(str(data_venda), f"Venda {pedido} - recebimento", "Entrada", recebido, forma, "venda", vid)
                    if total - recebido > 0:
                        garantir_conta_receber(cliente, f"Venda {pedido}", total - recebido, str(vencimento), "venda", vid, valor_recebido=0)

                    st.success(f"Venda {pedido} registrada com sucesso!")
                    st.rerun()

        renderizar_tabela_simples("vendas", "Histórico de Vendas")

    elif menu == "Despesas":
        st.title("💸 Controle de Despesas")
        with st.form("form_despesa"):
            c1, c2, c3 = st.columns(3)
            data_desp = c1.date_input("Data", value=date.today())
            categoria = c2.selectbox("Categoria", ["Gelo", "Embalagem", "Frete", "Água/Luz", "Aluguel", "Salários", "Manutenção", "Outros"])
            descricao = c3.text_input("Descrição")

            c4, c5, c6 = st.columns(3)
            valor = c4.number_input("Valor (R$)", min_value=0.01, format="%.2f")
            pagamento = c5.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO)
            status = c6.selectbox("Status", STATUS_PAGAMENTO)
            vencimento = st.date_input("Vencimento (se a prazo)", value=date.today())

            if st.form_submit_button("Lançar Despesa"):
                conn = get_conn()
                cur = conn.execute(
                    "INSERT INTO despesas (data_desp, categoria, descricao, valor, pagamento, status, vencimento) VALUES (?,?,?,?,?,?,?)",
                    (str(data_desp), categoria, descricao, valor, pagamento, status, str(vencimento))
                )
                did = cur.lastrowid
                conn.commit()
                conn.close()

                if status == "Pago":
                    registrar_financeiro(str(data_desp), f"Despesa #{did}: {categoria}", "Saída", valor, pagamento, "despesa", did)
                    garantir_conta_pagar("", f"Despesa #{did}: {categoria}", valor, str(vencimento), "despesa", did, valor_pago=valor)
                else:
                    garantir_conta_pagar("", f"Despesa #{did}: {categoria}", valor, str(vencimento), "despesa", did, valor_pago=0)

                st.success("Despesa registrada com sucesso!")
                st.rerun()

        renderizar_tabela_simples("despesas", "Histórico de Despesas")

    elif menu == "Estoque":
        st.title("📋 Posição Atual de Estoque")
        df_est = resumo_estoque()
        st.dataframe(df_est, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("⚙️ Ajuste Manual / Perda de Estoque")
        df_p = get_produtos()
        lista_prod = df_p["nome"].tolist() if not df_p.empty else []
        with st.form("form_ajuste"):
            c1, c2, c3 = st.columns(3)
            prod_aju = c1.selectbox("Produto para ajuste", lista_prod)
            tipo_aju = c2.selectbox("Tipo de Movimento", ["Ajuste Entrada", "Ajuste Saída", "Perda"])
            qtd_aju = c3.number_input("Quantidade", min_value=0.01, format="%.2f")
            obs_aju = st.text_input("Motivo / Observação")
            if st.form_submit_button("Confirmar Ajuste"):
                registrar_movimento(prod_aju, tipo_aju, qtd_aju, 0, "manual", None, obs_aju)
                st.success("Estoque ajustado com sucesso!")
                st.rerun()

    elif menu == "Financeiro & Caixa":
        st.title("💵 Fluxo de Caixa Realizado")
        extrato = df_query("SELECT data_mov AS data, descricao, tipo, valor, forma_pagamento FROM financeiro ORDER BY date(data_mov) DESC, id DESC")
        if extrato.empty:
            st.info("Nenhuma movimentação financeira registrada.")
        else:
            st.dataframe(extrato, use_container_width=True, hide_index=True)

    elif menu == "Contas a Pagar/Receber":
        st.title("📑 Gestão de Contas a Pagar e Receber")
        t1, t2 = st.tabs(["Contas a Pagar", "Contas a Receber"])

        with t1:
            st.subheader("Contas a Pagar Pendentes / Parciais")
            df_pagar = df_query("SELECT * FROM contas_pagar WHERE status IN ('Pendente','Parcial') ORDER BY date(vencimento)")
            st.dataframe(df_pagar, use_container_width=True, hide_index=True)

        with t2:
            st.subheader("Contas a Receber Pendentes / Parciais")
            df_receber = df_query("SELECT * FROM contas_receber WHERE status IN ('Pendente','Parcial') ORDER BY date(vencimento)")
            st.dataframe(df_receber, use_container_width=True, hide_index=True)

    elif menu == "Entregas":
        st.title("🚚 Gestão de Entregas")
        with st.form("form_entrega"):
            c1, c2, c3 = st.columns(3)
            pedido_ent = c1.text_input("Pedido relacionado")
            cliente_ent = c2.text_input("Nome do Cliente")
            data_ent = c3.date_input("Data da Entrega", value=date.today())
            c4, c5, c6 = st.columns(3)
            endereco_ent = c4.text_input("Endereço")
            bairro_ent = c5.text_input("Bairro")
            cidade_ent = c6.text_input("Cidade")
            c7, c8 = st.columns(2)
            entregador = c7.text_input("Entregador responsável")
            status_ent = c8.selectbox("Status da Entrega", STATUS_ENTREGA)
            if st.form_submit_button("Cadastrar Entrega"):
                conn = get_conn()
                conn.execute(
                    "INSERT INTO entregas (pedido, cliente, data_ent, endereco, bairro, cidade, entregador, status) VALUES (?,?,?,?,?,?,?,?)",
                    (pedido_ent, cliente_ent, str(data_ent), endereco_ent, bairro_ent, cidade_ent, entregador, status_ent)
                )
                conn.commit()
                conn.close()
                st.success("Entrega cadastrada!")
                st.rerun()

        renderizar_tabela_simples("entregas", "Painel de Entregas")

    elif menu == "Importar/Exportar":
        st.title("📥📤 Importação e Exportação de Dados")
        tabela_exp = st.selectbox("Selecione a tabela para exportar", ["produtos", "clientes", "fornecedores", "vendas", "compras"])
        df_export = df_query(f"SELECT * FROM {tabela_exp}")
        st.dataframe(df_export, use_container_width=True)
        if not df_export.empty:
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button("Baixar CSV da tabela", csv_data, f"{tabela_exp}.csv", "text/csv")

    elif menu == "Backup & Restaurar":
        st.title("💾 Backup e Restauração do Banco de Dados")
        if st.button("Fazer Backup Agora"):
            destino = backup_db()
            if destino:
                st.success(f"Backup gerado com sucesso em: **{destino}**")
            else:
                st.error("Erro ao gerar backup.")

if __name__ == "__main__":
    main()

