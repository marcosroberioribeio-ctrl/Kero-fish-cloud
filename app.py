# -*- coding: utf-8 -*-
"""
Kero Fish ERP - versão 10 - edição direta no grid
Base independente para análise/uso do arquivo enviado pelo usuário.

Principais melhorias:
- Banco SQLite preservado, sem to_sql(..., if_exists="replace")
- Migração automática de colunas da versão anterior
- Cadastro mestre de produtos
- Compras com fornecedor, custo/kg, pagamento e validade
- Vendas com pedido, preço/kg, desconto e pagamento
- Pagamentos: Pago / Pendente / Parcial
- Financeiro integrado a compras, vendas, despesas, contas a pagar e contas a receber
- Estoque por entradas, vendas, perdas e ajustes
- Estoque mínimo e alertas
- Fluxo de caixa realizado x previsto, com saldo de contas parciais
- Lucro bruto e líquido
- Entregas integradas ao pedido
- Backup e restauração do banco
- Importação de Excel com proteção contra duplicidade
- Painel gerencial
"""

import os
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, date

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Kero Fish ERP", layout="wide")

# O banco fica sempre junto do aplicativo, e não no diretório de execução.
# Isso evita que o Streamlit crie outro kerofish.db quando o diretório de
# execução mudar entre uma versão e outra. A variável de ambiente abaixo
# permite apontar explicitamente para um banco persistente, se desejado.
APP_DIR = Path(__file__).resolve().parent
DB_FILE = os.environ.get("KEROFISH_DB_PATH", str(APP_DIR / "kerofish.db"))
BACKUP_DIR = os.environ.get("KEROFISH_BACKUP_DIR", str(APP_DIR / "backups"))

FORMAS_PAGAMENTO = [
    "Dinheiro",
    "Pix",
    "Cartão de débito",
    "Cartão de crédito",
    "Transferência",
    "A prazo",
]

STATUS_PAGAMENTO = ["Pago", "Pendente", "Parcial"]
STATUS_CONTA = ["Pendente", "Pago", "Parcial", "Cancelado"]
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
    Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _db_record_count(path):
    """Pontua um banco existente para escolher o banco antigo correto."""
    try:
        con = sqlite3.connect(path)
        total = 0
        for tabela in ("clientes", "fornecedores", "produtos", "compras", "vendas", "despesas", "contas_pagar", "contas_receber", "financeiro"):
            try:
                total += int(con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0])
            except Exception:
                pass
        con.close()
        return total
    except Exception:
        return -1


def _localizar_banco_antigo():
    """Procura um kerofish.db antigo antes de criar um banco vazio."""
    alvo = Path(DB_FILE).resolve()
    candidatos = []
    locais = [
        alvo.parent,
        Path.cwd(),
        APP_DIR,
        APP_DIR.parent,
        Path("/mount/src"),
        Path("/app"),
    ]
    vistos=set()
    for base in locais:
        try:
            base=base.resolve()
        except Exception:
            continue
        if not base.exists() or str(base) in vistos:
            continue
        vistos.add(str(base))
        try:
            for f in base.rglob("kerofish.db"):
                f=f.resolve()
                if f == alvo or not f.is_file():
                    continue
                score=_db_record_count(f)
                if score > 0:
                    candidatos.append((score, f))
        except Exception:
            continue
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: x[0], reverse=True)
    return candidatos[0][1]


def garantir_banco_correto():
    """Evita que uma atualização silenciosamente crie um banco vazio."""
    alvo=Path(DB_FILE)
    alvo.parent.mkdir(parents=True, exist_ok=True)
    if alvo.exists():
        return
    antigo=_localizar_banco_antigo()
    if antigo:
        shutil.copy2(antigo, alvo)


def backup_db(label="manual"):
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    if not os.path.exists(DB_FILE):
        return None
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    destino=os.path.join(BACKUP_DIR, f"kerofish_{label}_{stamp}.db")
    shutil.copy2(DB_FILE, destino)
    return destino


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
            nome TEXT NOT NULL UNIQUE,
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
            pedido TEXT UNIQUE,
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

    # Migração das estruturas antigas.
    add_column_if_missing(conn, "clientes", "endereco", "TEXT DEFAULT ''")
    add_column_if_missing(conn, "produtos", "unidade", "TEXT DEFAULT 'kg'")
    add_column_if_missing(conn, "produtos", "preco_venda", "REAL DEFAULT 0")
    add_column_if_missing(conn, "produtos", "custo_medio", "REAL DEFAULT 0")
    add_column_if_missing(conn, "produtos", "estoque_minimo", "REAL DEFAULT 0")
    add_column_if_missing(conn, "produtos", "ativo", "INTEGER DEFAULT 1")

    for col, definition in [
        ("fornecedor", "TEXT DEFAULT ''"),
        ("preco_kg", "REAL DEFAULT 0"),
        ("lote", "TEXT DEFAULT ''"),
        ("validade", "TEXT DEFAULT ''"),
        ("forma_pagamento", "TEXT DEFAULT 'A prazo'"),
        ("status_pagamento", "TEXT DEFAULT 'Pendente'"),
        ("vencimento", "TEXT DEFAULT ''"),
        ("observacoes", "TEXT DEFAULT ''"),
    ]:
        add_column_if_missing(conn, "compras", col, definition)

    for col, definition in [
        ("pedido", "TEXT"),
        ("preco_kg", "REAL DEFAULT 0"),
        ("desconto", "REAL DEFAULT 0"),
        ("forma_pagamento", "TEXT DEFAULT 'Pix'"),
        ("status_pagamento", "TEXT DEFAULT 'Pago'"),
        ("valor_recebido", "REAL DEFAULT 0"),
        ("vencimento", "TEXT DEFAULT ''"),
        ("observacoes", "TEXT DEFAULT ''"),
    ]:
        add_column_if_missing(conn, "vendas", col, definition)

    for col, definition in [
        ("status", "TEXT DEFAULT 'Pago'"),
        ("vencimento", "TEXT DEFAULT ''"),
    ]:
        add_column_if_missing(conn, "despesas", col, definition)

    add_column_if_missing(conn, "financeiro", "forma_pagamento", "TEXT DEFAULT ''")
    add_column_if_missing(conn, "financeiro", "origem_tipo", "TEXT DEFAULT ''")
    add_column_if_missing(conn, "financeiro", "origem_id", "INTEGER")

    # Controle do que já foi pago/recebido em contas parciais.
    add_column_if_missing(conn, "contas_pagar", "valor_pago", "REAL DEFAULT 0")
    add_column_if_missing(conn, "contas_receber", "valor_recebido", "REAL DEFAULT 0")

    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome)")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_vendas_pedido ON vendas(pedido) WHERE pedido IS NOT NULL")

    # Produtos iniciais sem duplicar.
    for nome, categoria in PRODUTOS_INICIAIS:
        conn.execute(
            "INSERT OR IGNORE INTO produtos (nome, categoria, unidade) VALUES (?, ?, 'kg')",
            (nome, categoria),
        )

    # Converte compras antigas: se preco_kg estiver vazio, calcula pelo total/qtd.
    conn.execute("""
        UPDATE compras
        SET preco_kg = CASE
            WHEN COALESCE(qtd,0) > 0 THEN COALESCE(valor_total,0) / qtd
            ELSE 0
        END
        WHERE COALESCE(preco_kg,0) = 0
    """)

    conn.execute("""
        UPDATE vendas
        SET preco_kg = CASE
            WHEN COALESCE(qtd_kg,0) > 0 THEN
                (COALESCE(valor_total,0) + COALESCE(desconto,0)) / qtd_kg
            ELSE 0
        END
        WHERE COALESCE(preco_kg,0) = 0
    """)

    # Gera pedidos para vendas antigas que não tinham número.
    antigas = conn.execute("SELECT id FROM vendas WHERE pedido IS NULL OR pedido=''").fetchall()
    for row in antigas:
        pedido = f"KF-{datetime.now().year}-{row['id']:06d}"
        conn.execute("UPDATE vendas SET pedido=? WHERE id=?", (pedido, row["id"]))

    conn.commit()
    conn.close()


# backup_db definido no início do arquivo para garantir o banco correto.




# -----------------------------------------------------------------------------
# IMPORTAÇÃO DA PLANILHA BASE DO KERO FISH
# -----------------------------------------------------------------------------
# A planilha da Versão 9 é a fonte dos dados operacionais que devem aparecer
# nos respectivos módulos do ERP. A importação é idempotente: pode ser feita
# mais de uma vez sem duplicar produtos, clientes, compras ou vendas.
PLANILHA_BASE = APP_DIR / "Kero_Fish_Versao_9_Nosso_Projeto.xlsx"


def _texto(v, padrao=""):
    if pd.isna(v):
        return padrao
    return str(v).strip()


def _numero(v, padrao=0.0):
    if pd.isna(v):
        return float(padrao)
    try:
        return float(str(v).replace("R$", "").replace(".", "").replace(",", ".").strip())
    except Exception:
        try:
            return float(v)
        except Exception:
            return float(padrao)


def _data_iso(v, padrao=None):
    if pd.isna(v) or _texto(v) == "":
        return padrao or hoje()
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    try:
        return pd.to_datetime(v, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return padrao or hoje()


def importar_planilha_base(caminho=None):
    """Importa os dados da planilha Versão 9 para as tabelas do ERP.

    Fonte: Produtos, Clientes, Compras, Vendas e Financeiro.
    Campos sem equivalente no ERP ficam em observações; nada é apagado.
    """
    caminho = Path(caminho or PLANILHA_BASE)
    if not caminho.exists():
        return {"erro": f"Planilha não encontrada: {caminho}", "importados": {}}

    xls = pd.ExcelFile(caminho)
    conn = get_conn()
    cont = {"produtos": 0, "clientes": 0, "fornecedores": 0, "compras": 0, "vendas": 0, "financeiro": 0}
    try:
        # 1) PRODUTOS ---------------------------------------------------------
        if "Produtos" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="Produtos")
            for _, r in df.dropna(how="all").iterrows():
                nome = _texto(r.get("Produto"))
                if not nome or nome.lower() == "produto":
                    continue
                categoria = _texto(r.get("Categoria"), "Outros")
                unidade = _texto(r.get("Unidade"), "kg")
                minimo = _numero(r.get("Estoque Mínimo"))
                custo = _numero(r.get("Custo Atual"))
                preco = _numero(r.get("Preço Venda"))
                existe = conn.execute("SELECT id FROM produtos WHERE lower(nome)=lower(?)", (nome,)).fetchone()
                if existe:
                    conn.execute("""UPDATE produtos SET categoria=?,unidade=?,custo_medio=?,preco_venda=?,estoque_minimo=? WHERE id=?""",
                                 (categoria, unidade, custo, preco, minimo, existe[0]))
                else:
                    conn.execute("""INSERT INTO produtos(nome,categoria,unidade,custo_medio,preco_venda,estoque_minimo,ativo)
                                    VALUES(?,?,?,?,?,?,1)""", (nome,categoria,unidade,custo,preco,minimo))
                cont["produtos"] += 1

        # 2) CLIENTES ---------------------------------------------------------
        if "Clientes" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="Clientes")
            for _, r in df.dropna(how="all").iterrows():
                nome = _texto(r.get("Nome"))
                if not nome or nome.lower() == "nome":
                    continue
                tel = _texto(r.get("Telefone"))
                endereco = _texto(r.get("Endereço"))
                cidade = _texto(r.get("Cidade"))
                obs = _texto(r.get("Observações"))
                existe = conn.execute("SELECT id FROM clientes WHERE lower(nome)=lower(?)", (nome,)).fetchone()
                if existe:
                    conn.execute("UPDATE clientes SET telefone=?,endereco=?,cidade=? WHERE id=?", (tel,endereco,cidade,existe[0]))
                else:
                    conn.execute("INSERT INTO clientes(nome,telefone,endereco,cidade,data_cad) VALUES(?,?,?,?,?)",
                                 (nome,tel,endereco,cidade,hoje()))
                cont["clientes"] += 1

        # 3) FORNECEDORES -----------------------------------------------------
        fornecedores_encontrados = set()
        if "Fornecedores" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="Fornecedores", header=2)
            for _, r in df.dropna(how="all").iterrows():
                nome = _texto(r.get("Fornecedor"))
                if not nome or nome.lower() == "fornecedor":
                    continue
                fornecedores_encontrados.add(nome)
                tel = _texto(r.get("Telefone")); cidade = _texto(r.get("Cidade"))
                produto_f = _texto(r.get("Produto principal")); obs = _texto(r.get("Observação"))
                existe = conn.execute("SELECT id FROM fornecedores WHERE lower(fornecedor)=lower(?)", (nome,)).fetchone()
                if existe:
                    conn.execute("UPDATE fornecedores SET telefone=?,produto_fornecido=?,observacoes=? WHERE id=?",
                                 (tel,produto_f,obs,existe[0]))
                else:
                    conn.execute("""INSERT INTO fornecedores(fornecedor,telefone,endereco,produto_fornecido,observacoes)
                                    VALUES(?,?,?,?,?)""", (nome,tel,cidade,produto_f,obs))
                cont["fornecedores"] += 1

        # A planilha de fornecedores da Versão 9 está sem linhas preenchidas,
        # mas compras/produtos identificam Fornecedor 1 e Fornecedor 2.
        # Criamos somente esses nomes que já constam nos próprios dados.
        for origem_sheet, col in (("Compras", "Fornecedor"), ("Produtos", "Fornecedor")):
            if origem_sheet not in xls.sheet_names:
                continue
            df = pd.read_excel(xls, sheet_name=origem_sheet)
            for v in df[col].dropna().tolist() if col in df.columns else []:
                nome = _texto(v)
                if nome and nome.lower() not in ("fornecedor", "nan"):
                    fornecedores_encontrados.add(nome)
        for nome in sorted(fornecedores_encontrados):
            existe = conn.execute("SELECT id FROM fornecedores WHERE lower(fornecedor)=lower(?)", (nome,)).fetchone()
            if not existe:
                conn.execute("INSERT INTO fornecedores(fornecedor,observacoes) VALUES(?,?)",
                             (nome, "Importado da planilha base; cadastro complementar pode ser preenchido."))
                cont["fornecedores"] += 1

        # 4) COMPRAS ----------------------------------------------------------
        if "Compras" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="Compras")
            for _, r in df.dropna(how="all").iterrows():
                produto = _texto(r.get("Produto")); fornecedor = _texto(r.get("Fornecedor"))
                qtd = _numero(r.get("Quantidade")); preco = _numero(r.get("Custo Unitário"))
                if not produto or qtd <= 0:
                    continue
                data_compra = _data_iso(r.get("Data")); lote = _texto(r.get("Lote")); validade = _data_iso(r.get("Validade"), "")
                freezer = _texto(r.get("Freezer"))
                total = _numero(r.get("Total")) or qtd * preco
                existe = conn.execute("""SELECT id FROM compras WHERE data_compra=? AND fornecedor=? AND produto=? AND qtd=? AND abs(preco_kg-?)<0.00001""",
                                     (data_compra,fornecedor,produto,qtd,preco)).fetchone()
                if existe:
                    continue
                cur = conn.execute("""INSERT INTO compras(fornecedor,produto,qtd,preco_kg,valor_total,data_compra,lote,validade,
                                      forma_pagamento,status_pagamento,vencimento,observacoes)
                                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                                   (fornecedor,produto,qtd,preco,total,data_compra,lote,validade,"A prazo","Pendente",data_compra,
                                    f"Freezer: {freezer}" if freezer else ""))
                compra_id = cur.lastrowid
                conn.execute("""INSERT INTO movimentos_estoque(data_mov,produto,tipo,quantidade,custo_unitario,origem_tipo,origem_id,observacoes)
                                VALUES(?,?,?,?,?,?,?,?)""",
                             (data_compra,produto,"Entrada",qtd,preco,"compra",compra_id,f"Importado da planilha; lote {lote}"))
                cont["compras"] += 1

        # 5) VENDAS -----------------------------------------------------------
        vendas_importadas = []
        if "Vendas" in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name="Vendas")
            for _, r in df.dropna(how="all").iterrows():
                source_id = int(_numero(r.get("ID"))) if _numero(r.get("ID")) else None
                cliente = _texto(r.get("Cliente")); produto = _texto(r.get("Produto"))
                qtd = _numero(r.get("Quantidade")); preco = _numero(r.get("Preço Unitário")); desconto = 0.0
                if not produto or qtd <= 0:
                    continue
                data_venda = _data_iso(r.get("Data")); bruto=qtd*preco; total=_numero(r.get("Total")) or bruto
                pagamento = _texto(r.get("Pagamento"), "Não informado")
                status_pedido = _texto(r.get("Status"), "")
                entrega = _texto(r.get("Entrega"), "")
                pedido = f"KF-IMPORT-{source_id:06d}" if source_id else proximo_pedido()
                # A planilha Financeiro registra essas duas vendas como entradas PIX;
                # portanto o recebimento é tratado como realizado.
                recebido = total if pagamento.upper() in ("PIX","DINHEIRO","CARTÃO","CARTAO","TRANSFERÊNCIA","TRANSFERENCIA") else 0.0
                status_pag = "Pago" if recebido >= total and total > 0 else ("Parcial" if recebido > 0 else "Pendente")
                obs = f"Status do pedido: {status_pedido}; Entrega: {entrega}".strip("; ")
                existe = conn.execute("SELECT id FROM vendas WHERE pedido=?", (pedido,)).fetchone()
                if existe:
                    venda_id=existe[0]
                    conn.execute("""UPDATE vendas SET cliente=?,produto=?,qtd_kg=?,preco_kg=?,valor_total=?,data_venda=?,forma_pagamento=?,
                                      status_pagamento=?,valor_recebido=?,vencimento=?,observacoes=? WHERE id=?""",
                                 (cliente,produto,qtd,preco,total,data_venda,pagamento,status_pag,recebido,data_venda,obs,venda_id))
                else:
                    cur=conn.execute("""INSERT INTO vendas(pedido,cliente,produto,qtd_kg,preco_kg,desconto,valor_total,data_venda,
                                      forma_pagamento,status_pagamento,valor_recebido,vencimento,observacoes)
                                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                     (pedido,cliente,produto,qtd,preco,desconto,total,data_venda,pagamento,status_pag,recebido,data_venda,obs))
                    venda_id=cur.lastrowid
                    conn.execute("""INSERT INTO movimentos_estoque(data_mov,produto,tipo,quantidade,custo_unitario,origem_tipo,origem_id,observacoes)
                                    VALUES(?,?,?,?,?,?,?,?)""",
                                 (data_venda,produto,"Saída",qtd,0,"venda",venda_id,"Importado da planilha"))
                vendas_importadas.append((venda_id,total,recebido,data_venda,pagamento,pedido))
                cont["vendas"] += 1

        # 6) FINANCEIRO -------------------------------------------------------
        # Não copiamos linhas vazias da coluna Valor. Para as vendas, usamos o
        # valor calculado a partir da própria venda e mantemos o vínculo com ela.
        for venda_id,total,recebido,data_venda,pagamento,pedido in vendas_importadas:
            if recebido <= 0:
                continue
            existe = conn.execute("SELECT id FROM financeiro WHERE origem_tipo='venda' AND origem_id=?", (venda_id,)).fetchone()
            if existe:
                conn.execute("UPDATE financeiro SET data_mov=?,descricao=?,tipo=?,valor=?,forma_pagamento=? WHERE id=?",
                             (data_venda,f"Venda {pedido} - recebimento","Entrada",recebido,pagamento,existe[0]))
            else:
                conn.execute("""INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id)
                                VALUES(?,?,?,?,?,?,?)""",
                             (data_venda,f"Venda {pedido} - recebimento","Entrada",recebido,pagamento,"venda",venda_id))
                cont["financeiro"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {"erro": None, "importados": cont}

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
    df = df_query("SELECT * FROM produtos WHERE ativo=1 ORDER BY nome")
    return df


def estoque_produto(produto):
    """Calcula o estoque real diretamente a partir das compras e vendas.

    Compras = entradas; vendas = saídas. Ajustes/perdas manuais continuam
    vindo da tabela de movimentos_estoque. Isso também corrige estoques
    históricos quando compras/vendas antigas não possuem movimento gravado.
    """
    compras = scalar(
        "SELECT COALESCE(SUM(qtd),0) FROM compras WHERE produto=?",
        (produto,),
    )
    vendas = scalar(
        "SELECT COALESCE(SUM(qtd_kg),0) FROM vendas WHERE produto=?",
        (produto,),
    )
    ajustes_entrada = scalar(
        "SELECT COALESCE(SUM(quantidade),0) FROM movimentos_estoque "
        "WHERE produto=? AND origem_tipo='manual' AND tipo='Ajuste Entrada'",
        (produto,),
    )
    ajustes_saida = scalar(
        "SELECT COALESCE(SUM(quantidade),0) FROM movimentos_estoque "
        "WHERE produto=? AND origem_tipo='manual' AND tipo IN ('Ajuste Saída','Perda')",
        (produto,),
    )
    return float(compras or 0) - float(vendas or 0) + float(ajustes_entrada or 0) - float(ajustes_saida or 0)


def resumo_estoque():
    """Retorna o estoque por produto, sempre baseado em compras - vendas + ajustes."""
    produtos = get_produtos()
    registros = []
    for _, r in produtos.iterrows():
        produto = r["nome"]
        compras = float(scalar("SELECT COALESCE(SUM(qtd),0) FROM compras WHERE produto=?", (produto,)) or 0)
        vendas = float(scalar("SELECT COALESCE(SUM(qtd_kg),0) FROM vendas WHERE produto=?", (produto,)) or 0)
        ajuste_ent = float(scalar(
            "SELECT COALESCE(SUM(quantidade),0) FROM movimentos_estoque WHERE produto=? AND origem_tipo='manual' AND tipo='Ajuste Entrada'",
            (produto,)
        ) or 0)
        ajuste_saida = float(scalar(
            "SELECT COALESCE(SUM(quantidade),0) FROM movimentos_estoque WHERE produto=? AND origem_tipo='manual' AND tipo IN ('Ajuste Saída','Perda')",
            (produto,)
        ) or 0)
        estoque = compras - vendas + ajuste_ent - ajuste_saida
        minimo = float(r["estoque_minimo"] or 0)
        registros.append({
            "Produto": produto,
            "Categoria": r["categoria"],
            "Compras": compras,
            "Vendas": vendas,
            "Ajustes +": ajuste_ent,
            "Ajustes -": ajuste_saida,
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



def registrar_compra(fornecedor, produto, qtd, preco_kg, data_compra, lote, validade,
                     forma, status, vencimento, observacoes):
    total = float(qtd) * float(preco_kg)
    status = status if status in STATUS_PAGAMENTO else "Pendente"

    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO compras
        (fornecedor, produto, qtd, preco_kg, valor_total, data_compra, lote, validade,
         forma_pagamento, status_pagamento, vencimento, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fornecedor, produto, qtd, preco_kg, total, data_compra, lote, validade,
          forma, status, vencimento, observacoes))
    compra_id = cur.lastrowid
    conn.commit()
    conn.close()

    registrar_movimento(produto, "Entrada", qtd, preco_kg, "compra", compra_id, f"Lote: {lote}")

    # COMPRA -> FINANCEIRO ou CONTAS A PAGAR
    if status == "Pago":
        registrar_financeiro(
            data_compra, f"Compra #{compra_id}: {produto}", "Saída",
            total, forma, "compra", compra_id
        )
    else:
        garantir_conta_pagar(
            fornecedor, f"Compra #{compra_id}: {produto}", total,
            vencimento or data_compra, "compra", compra_id
        )



def registrar_venda(pedido, cliente, produto, qtd, preco_kg, desconto, data_venda,
                    forma, status, recebido, vencimento, observacoes):
    bruto = float(qtd) * float(preco_kg)
    total = max(0.0, bruto - float(desconto or 0))
    recebido = min(max(float(recebido or 0), 0.0), total)
    pendente = max(0.0, total - recebido)

    if recebido >= total and total > 0:
        status = "Pago"
    elif recebido > 0:
        status = "Parcial"
    else:
        status = "Pendente"

    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO vendas
        (pedido, cliente, produto, qtd_kg, preco_kg, desconto, valor_total, data_venda,
         forma_pagamento, status_pagamento, valor_recebido, vencimento, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pedido, cliente, produto, qtd, preco_kg, desconto, total, data_venda,
          forma, status, recebido, vencimento, observacoes))
    venda_id = cur.lastrowid
    conn.commit()
    conn.close()

    registrar_movimento(produto, "Saída", qtd, preco_kg, "venda", venda_id, pedido)

    # VENDA -> CAIXA pelo valor efetivamente recebido.
    if recebido > 0:
        registrar_financeiro(
            data_venda, f"Venda {pedido} - recebimento", "Entrada",
            recebido, forma, "venda", venda_id
        )

    # VENDA -> CONTAS A RECEBER somente pelo saldo pendente.
    if pendente > 0:
        garantir_conta_receber(
            cliente, f"Venda {pedido}", pendente,
            vencimento or data_venda, "venda", venda_id
        )



def obter_extrato_realizado():
    return df_query("""
        SELECT data_mov AS data, descricao, tipo, valor, forma_pagamento,
               origem_tipo, origem_id
        FROM financeiro
        ORDER BY date(data_mov) DESC, id DESC
    """)



def obter_previsto():
    entradas = df_query("""
        SELECT vencimento AS data,
               'A receber: ' || COALESCE(cliente,'') || ' - ' || descricao AS descricao,
               'Entrada prevista' AS tipo,
               CASE WHEN valor - COALESCE(valor_recebido,0) > 0 THEN valor - COALESCE(valor_recebido,0) ELSE 0 END AS valor,
               '' AS forma_pagamento,
               'conta_receber' AS origem
        FROM contas_receber
        WHERE status IN ('Pendente','Parcial')
          AND (valor - COALESCE(valor_recebido,0)) > 0
    """)
    saidas = df_query("""
        SELECT vencimento AS data,
               'A pagar: ' || COALESCE(fornecedor,'') || ' - ' || descricao AS descricao,
               'Saída prevista' AS tipo,
               CASE WHEN valor - COALESCE(valor_pago,0) > 0 THEN valor - COALESCE(valor_pago,0) ELSE 0 END AS valor,
               '' AS forma_pagamento,
               'conta_pagar' AS origem
        FROM contas_pagar
        WHERE status IN ('Pendente','Parcial')
          AND (valor - COALESCE(valor_pago,0)) > 0
    """)
    return pd.concat([entradas, saidas], ignore_index=True)


def resumo_financeiro_por_origem():
    compras = scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE origem_tipo='compra' AND tipo='Saída'")
    vendas = scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE origem_tipo='venda' AND tipo='Entrada'")
    despesas = scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE origem_tipo='despesa' AND tipo='Saída'")
    pagar = scalar("""
        SELECT COALESCE(SUM(CASE WHEN valor - COALESCE(valor_pago,0) > 0 THEN valor - COALESCE(valor_pago,0) ELSE 0 END),0)
        FROM contas_pagar WHERE status IN ('Pendente','Parcial')
    """)
    receber = scalar("""
        SELECT COALESCE(SUM(CASE WHEN valor - COALESCE(valor_recebido,0) > 0 THEN valor - COALESCE(valor_recebido,0) ELSE 0 END),0)
        FROM contas_receber WHERE status IN ('Pendente','Parcial')
    """)
    return {
        "Compras pagas": float(compras or 0),
        "Vendas recebidas": float(vendas or 0),
        "Despesas pagas": float(despesas or 0),
        "Contas a pagar": float(pagar or 0),
        "Contas a receber": float(receber or 0),
    }



def renderizar_tabela_simples(tabela, titulo, colunas_ocultar=None):
    st.subheader(titulo)
    df = df_query(f"SELECT * FROM {tabela} ORDER BY id DESC")
    if colunas_ocultar:
        df = df.drop(columns=[c for c in colunas_ocultar if c in df.columns])
    if df.empty:
        st.info("Nenhum registro encontrado.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)



def _parse_date_text(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return date.today()


def _status_por_saldo(total, pago):
    total = float(total or 0)
    pago = min(max(float(pago or 0), 0), total)
    return "Pago" if total > 0 and pago >= total else ("Parcial" if pago > 0 else "Pendente")


def sincronizar_origem_financeira(origem_tipo, origem_id):
    """Recalcula caixa/contas vinculadas depois de editar uma compra, venda ou despesa."""
    conn = get_conn()
    conn.execute("DELETE FROM financeiro WHERE origem_tipo=? AND origem_id=?", (origem_tipo, origem_id))

    if origem_tipo == "compra":
        row = conn.execute("SELECT * FROM compras WHERE id=?", (origem_id,)).fetchone()
        if row:
            total = float(row["valor_total"] or 0)
            conta = conn.execute("SELECT id, valor_pago FROM contas_pagar WHERE origem_tipo='compra' AND origem_id=? ORDER BY id DESC LIMIT 1", (origem_id,)).fetchone()
            pago = float(conta["valor_pago"] or 0) if conta else 0.0
            if row["status_pagamento"] == "Pago":
                pago = total
            pago = min(max(pago, 0), total)
            if pago > 0:
                conn.execute("""INSERT INTO financeiro
                    (data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id)
                    VALUES (?,?,?,?,?,?,?)""",
                    (row["data_compra"], f"Compra #{origem_id}: {row['produto']}", "Saída", pago,
                     row["forma_pagamento"], "compra", origem_id))
            saldo = total - pago
            if saldo > 0:
                if conta:
                    conn.execute("""UPDATE contas_pagar SET fornecedor=?, descricao=?, valor=?, vencimento=?,
                        valor_pago=?, status=?, origem_tipo='compra', origem_id=? WHERE id=?""",
                        (row["fornecedor"], f"Compra #{origem_id}: {row['produto']}", total,
                         row["vencimento"] or row["data_compra"], pago, _status_por_saldo(total,pago), origem_id, conta["id"]))
                else:
                    conn.execute("""INSERT INTO contas_pagar
                        (fornecedor,descricao,valor,valor_pago,vencimento,status,origem_tipo,origem_id)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (row["fornecedor"], f"Compra #{origem_id}: {row['produto']}", total, pago,
                         row["vencimento"] or row["data_compra"], _status_por_saldo(total,pago), "compra", origem_id))
            elif conta:
                conn.execute("UPDATE contas_pagar SET fornecedor=?, descricao=?, valor=?, vencimento=?, valor_pago=?, status=? WHERE id=?",
                             (row["fornecedor"], f"Compra #{origem_id}: {row['produto']}", total,
                              row["vencimento"] or row["data_compra"], pago, "Pago", conta["id"]))

    elif origem_tipo == "venda":
        row = conn.execute("SELECT * FROM vendas WHERE id=?", (origem_id,)).fetchone()
        if row:
            total = float(row["valor_total"] or 0)
            recebido = min(max(float(row["valor_recebido"] or 0),0), total)
            if recebido > 0:
                conn.execute("""INSERT INTO financeiro
                    (data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id)
                    VALUES (?,?,?,?,?,?,?)""",
                    (row["data_venda"], f"Venda {row['pedido']} - recebimento", "Entrada", recebido,
                     row["forma_pagamento"], "venda", origem_id))
            conta = conn.execute("SELECT id, valor_recebido FROM contas_receber WHERE origem_tipo='venda' AND origem_id=? ORDER BY id DESC LIMIT 1", (origem_id,)).fetchone()
            recebido_conta = max(recebido, float(conta["valor_recebido"] or 0) if conta else 0.0)
            recebido_conta = min(recebido_conta, total)
            saldo = total - recebido_conta
            if saldo > 0:
                if conta:
                    conn.execute("""UPDATE contas_receber SET cliente=?, descricao=?, valor=?, vencimento=?,
                        valor_recebido=?, status=? WHERE id=?""",
                        (row["cliente"], f"Venda {row['pedido']}", total, row["vencimento"] or row["data_venda"],
                         recebido_conta, _status_por_saldo(total,recebido_conta), conta["id"]))
                else:
                    conn.execute("""INSERT INTO contas_receber
                        (cliente,descricao,valor,valor_recebido,vencimento,status,origem_tipo,origem_id)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (row["cliente"], f"Venda {row['pedido']}", total, recebido_conta,
                         row["vencimento"] or row["data_venda"], _status_por_saldo(total,recebido_conta), "venda", origem_id))
            elif conta:
                conn.execute("UPDATE contas_receber SET cliente=?, descricao=?, valor=?, vencimento=?, valor_recebido=?, status='Pago' WHERE id=?",
                             (row["cliente"], f"Venda {row['pedido']}", total, row["vencimento"] or row["data_venda"], recebido_conta, conta["id"]))

    elif origem_tipo == "despesa":
        row = conn.execute("SELECT * FROM despesas WHERE id=?", (origem_id,)).fetchone()
        if row:
            total = float(row["valor"] or 0)
            conta = conn.execute("SELECT id, valor_pago FROM contas_pagar WHERE origem_tipo='despesa' AND origem_id=? ORDER BY id DESC LIMIT 1", (origem_id,)).fetchone()
            pago = float(conta["valor_pago"] or 0) if conta else (total if row["status"] == "Pago" else 0)
            pago = min(max(pago,0),total)
            if pago > 0:
                conn.execute("""INSERT INTO financeiro
                    (data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id)
                    VALUES (?,?,?,?,?,?,?)""",
                    (row["data_desp"], f"Despesa #{origem_id}: {row['categoria']} - {row['descricao']}", "Saída", pago,
                     row["pagamento"], "despesa", origem_id))
            saldo = total-pago
            if saldo > 0:
                if conta:
                    conn.execute("""UPDATE contas_pagar SET fornecedor='', descricao=?, valor=?, vencimento=?, valor_pago=?, status=? WHERE id=?""",
                                 (f"Despesa #{origem_id}: {row['categoria']} - {row['descricao']}", total,
                                  row["vencimento"] or row["data_desp"], pago, _status_por_saldo(total,pago), conta["id"]))
                else:
                    conn.execute("""INSERT INTO contas_pagar
                        (fornecedor,descricao,valor,valor_pago,vencimento,status,origem_tipo,origem_id)
                        VALUES ('',?,?,?,?,?,?,?)""",
                        (f"Despesa #{origem_id}: {row['categoria']} - {row['descricao']}", total, pago,
                         row["vencimento"] or row["data_desp"], _status_por_saldo(total,pago), "despesa", origem_id))
            elif conta:
                conn.execute("UPDATE contas_pagar SET descricao=?, valor=?, vencimento=?, valor_pago=?, status='Pago' WHERE id=?",
                             (f"Despesa #{origem_id}: {row['categoria']} - {row['descricao']}", total,
                              row["vencimento"] or row["data_desp"], pago, conta["id"]))
    conn.commit()
    conn.close()


def excluir_origem_integrada(origem_tipo, origem_id, tabela):
    conn = get_conn()
    conn.execute("DELETE FROM financeiro WHERE origem_tipo=? AND origem_id=?", (origem_tipo, origem_id))
    conn.execute("DELETE FROM contas_pagar WHERE origem_tipo=? AND origem_id=?", (origem_tipo, origem_id))
    conn.execute("DELETE FROM contas_receber WHERE origem_tipo=? AND origem_id=?", (origem_tipo, origem_id))
    conn.execute("DELETE FROM movimentos_estoque WHERE origem_tipo=? AND origem_id=?", (origem_tipo, origem_id))
    conn.execute(f"DELETE FROM {tabela} WHERE id=?", (origem_id,))
    conn.commit()
    conn.close()


def editar_registro_simples(tabela, titulo, label_id, campos, order_by="id DESC"):
    df = df_query(f"SELECT * FROM {tabela} ORDER BY {order_by}")
    if df.empty:
        return
    st.markdown("---")
    st.subheader(f"✏️ Editar ou excluir — {titulo}")
    opcoes = {f"#{int(r['id'])} - {r.get(label_id, '')}": int(r["id"]) for _, r in df.iterrows()}
    escolha = st.selectbox("Selecione o registro", list(opcoes), key=f"edit_sel_{tabela}")
    rid = opcoes[escolha]
    row = df[df["id"] == rid].iloc[0]
    valores = {}
    with st.form(f"edit_form_{tabela}"):
        cols = st.columns(2)
        for i, (col, rotulo, tipo, opcoes_campo) in enumerate(campos):
            atual = row[col]
            box = cols[i % 2]
            if tipo == "float":
                valores[col] = box.number_input(rotulo, min_value=0.0, value=float(atual or 0), step=0.01)
            elif tipo == "date":
                valores[col] = box.date_input(rotulo, value=_parse_date_text(atual))
            elif tipo == "select":
                lista = opcoes_campo or []
                atual_s = str(atual or "")
                idx = lista.index(atual_s) if atual_s in lista else 0
                valores[col] = box.selectbox(rotulo, lista, index=idx)
            else:
                valores[col] = box.text_input(rotulo, value="" if pd.isna(atual) else str(atual))
        c1, c2 = st.columns(2)
        salvar = c1.form_submit_button("💾 Salvar alteração")
        excluir = c2.form_submit_button("🗑️ Excluir registro")
    if salvar:
        sets=[]; params=[]
        for col, _, tipo, _ in campos:
            v=valores[col]
            if tipo == "date": v=v.strftime("%Y-%m-%d")
            sets.append(f"{col}=?"); params.append(v)
        params.append(rid)
        conn=get_conn(); conn.execute(f"UPDATE {tabela} SET {', '.join(sets)} WHERE id=?", params); conn.commit(); conn.close()
        st.success("Alteração salva com sucesso.")
        st.rerun()
    if excluir:
        conn=get_conn(); conn.execute(f"DELETE FROM {tabela} WHERE id=?", (rid,)); conn.commit(); conn.close()
        st.success("Registro excluído.")
        st.rerun()



def _salvar_grid_dataframe(tabela, original, editado, campos, titulo):
    """Salva alterações feitas diretamente no grid (st.data_editor)."""
    if editado is None or editado.empty:
        return 0
    orig = original.set_index("id", drop=False)
    alterados = 0
    conn = get_conn()
    try:
        for _, row in editado.iterrows():
            rid = int(row["id"])
            if rid not in orig.index:
                continue
            antigo = orig.loc[rid]
            mudou = any(str(row.get(c, "")) != str(antigo.get(c, "")) for c in campos)
            if not mudou:
                continue
            sets=[]; params=[]
            for c in campos:
                v=row.get(c)
                if pd.isna(v):
                    v=""
                if c in ("valor","valor_pago","valor_recebido","qtd","qtd_kg","preco_kg","desconto","taxa_entrega","estoque_minimo","preco_venda"):
                    v=float(v or 0)
                sets.append(f"{c}=?")
                params.append(v)
            params.append(rid)
            conn.execute(f"UPDATE {tabela} SET {', '.join(sets)} WHERE id=?", params)
            alterados += 1
        conn.commit()
    finally:
        conn.close()
    return alterados


def _grid_simples(tabela, titulo, colunas_editaveis, colunas_disabled=None, altura=420):
    """Tabela editável e formulário de segurança para correção de registros."""
    df=df_query(f"SELECT * FROM {tabela} ORDER BY id DESC")
    if df.empty:
        st.info(f"Nenhum registro em {titulo.lower()}."); return
    colunas_editaveis=[c for c in colunas_editaveis if c in df.columns]
    colunas_disabled=[c for c in (colunas_disabled or []) if c in df.columns]
    st.markdown(f"### ✏️ {titulo} — PLANILHA EDITÁVEL")
    st.info("Clique na célula, apague o valor antigo, digite o novo valor e clique em **💾 SALVAR ALTERAÇÕES**.")
    editado=st.data_editor(df,key=f"editor_{tabela}",use_container_width=True,hide_index=True,num_rows="fixed",disabled=colunas_disabled,height=altura)
    if st.button("💾 SALVAR ALTERAÇÕES",key=f"save_editor_{tabela}",type="primary"):
        n=_salvar_grid_dataframe(tabela,df,editado,colunas_editaveis,titulo)
        if n:
            st.success(f"{n} registro(s) alterado(s) com sucesso."); st.rerun()
        else: st.warning("Nenhuma alteração foi detectada no grid.")
    st.markdown("#### 🛠️ Correção individual")
    opcoes={f"#{int(r['id'])} — {str(r.get(colunas_editaveis[0],''))}":int(r['id']) for _,r in df.iterrows()}
    escolha=st.selectbox("Registro para corrigir",list(opcoes),key=f"fallback_sel_{tabela}")
    rid=opcoes[escolha]; atual=df[df.id==rid].iloc[0]
    valores={}
    with st.form(f"fallback_form_{tabela}"):
        cols=st.columns(2)
        for i,campo in enumerate(colunas_editaveis):
            v=atual[campo]; label=campo.replace('_',' ').title(); box=cols[i%2]
            if campo in ("qtd","qtd_kg","preco_kg","preco_venda","estoque_minimo","valor","desconto","taxa_entrega"):
                valores[campo]=box.number_input(label,value=float(v or 0),step=0.01)
            else:
                valores[campo]=box.text_input(label,value="" if pd.isna(v) else str(v))
        salvar=st.form_submit_button("💾 Salvar correção")
    if salvar:
        sets=[]; params=[]
        for campo in colunas_editaveis:
            v=valores[campo]
            if campo in ("qtd","qtd_kg","preco_kg","preco_venda","estoque_minimo","valor","desconto","taxa_entrega"): v=float(v or 0)
            sets.append(f"{campo}=?"); params.append(v)
        params.append(rid); conn=get_conn()
        try: conn.execute(f"UPDATE {tabela} SET {', '.join(sets)} WHERE id=?",params); conn.commit()
        finally: conn.close()
        st.success("Correção salva."); st.rerun()

def _grid_contas(tabela, titulo, pessoa_col, valor_pago_col):
    df=df_query(f"""SELECT id,{pessoa_col},descricao,valor,COALESCE({valor_pago_col},0) AS {valor_pago_col},MAX(valor-COALESCE({valor_pago_col},0),0) AS saldo,vencimento,status,origem_tipo,origem_id FROM {tabela} ORDER BY date(vencimento),id DESC""")
    if df.empty: st.info(f"Nenhuma {titulo.lower()} cadastrada."); return
    editaveis=[pessoa_col,"descricao","valor","vencimento"]
    st.markdown(f"### ✏️ {titulo} — PLANILHA EDITÁVEL")
    st.info("Esta é a planilha de edição. Clique na célula, apague o valor antigo, digite o novo e clique em **💾 SALVAR ALTERAÇÕES**.")
    editado=st.data_editor(df,key=f"editor_{tabela}_contas",use_container_width=True,hide_index=True,num_rows="fixed",disabled=["id",valor_pago_col,"saldo","status","origem_tipo","origem_id"],height=430)
    if st.button("💾 SALVAR ALTERAÇÕES",key=f"save_editor_{tabela}_contas",type="primary"):
        orig=df.set_index('id',drop=False); alterados=0; erro=None; conn=get_conn()
        try:
            for _,row in editado.iterrows():
                rid=int(row.id); old=orig.loc[rid]
                if not any(str(row.get(c,''))!=str(old.get(c,'')) for c in editaveis): continue
                pessoa='' if pd.isna(row[pessoa_col]) else str(row[pessoa_col]); desc='' if pd.isna(row.descricao) else str(row.descricao); valor=float(row.valor or 0); venc='' if pd.isna(row.vencimento) else str(row.vencimento)
                if valor<=0: erro=f"Conta #{rid}: o valor precisa ser maior que zero."; break
                if tabela=='contas_pagar': conn.execute("UPDATE contas_pagar SET fornecedor=?,descricao=?,valor=?,vencimento=? WHERE id=?",(pessoa,desc,valor,venc,rid))
                else: conn.execute("UPDATE contas_receber SET cliente=?,descricao=?,valor=?,vencimento=? WHERE id=?",(pessoa,desc,valor,venc,rid))
                alterados+=1
            if erro: conn.rollback()
            else: conn.commit()
        except Exception as exc: conn.rollback(); erro=str(exc)
        finally: conn.close()
        if erro: st.error(f"Não foi possível salvar: {erro}")
        elif alterados:
            for _,row in editado.iterrows():
                rid=int(row.id); old=orig.loc[rid]
                if any(str(row.get(c,''))!=str(old.get(c,'')) for c in editaveis):
                    origem=str(old.origem_tipo or ''); oid=old.origem_id
                    if origem in ('compra','venda','despesa') and pd.notna(oid) and oid: sincronizar_origem_financeira(origem,int(oid))
            st.success(f"{alterados} conta(s) alterada(s) com sucesso."); st.rerun()
        else: st.warning("Nenhuma alteração foi detectada.")
    st.markdown("#### 🛠️ Correção individual")
    op={f"#{int(r.id)} — {str(r[pessoa_col])} — {str(r.descricao)}":int(r.id) for _,r in df.iterrows()}; escolha=st.selectbox("Selecione a conta",list(op),key=f"fallback_conta_{tabela}"); rid=op[escolha]; row=df[df.id==rid].iloc[0]
    with st.form(f"fallback_form_conta_{tabela}"):
        pessoa=st.text_input("Pessoa/Empresa",value='' if pd.isna(row[pessoa_col]) else str(row[pessoa_col])); descricao=st.text_input("Descrição",value='' if pd.isna(row.descricao) else str(row.descricao)); valor=st.number_input("Valor",min_value=0.0,value=float(row.valor or 0),step=0.01); vencimento=st.text_input("Vencimento (AAAA-MM-DD)",value='' if pd.isna(row.vencimento) else str(row.vencimento)); salvar=st.form_submit_button("💾 Salvar correção da conta")
    if salvar:
        conn=get_conn()
        try:
            if tabela=='contas_pagar': conn.execute("UPDATE contas_pagar SET fornecedor=?,descricao=?,valor=?,vencimento=? WHERE id=?",(pessoa,descricao,valor,vencimento,rid))
            else: conn.execute("UPDATE contas_receber SET cliente=?,descricao=?,valor=?,vencimento=? WHERE id=?",(pessoa,descricao,valor,vencimento,rid))
            conn.commit()
        finally: conn.close()
        origem=str(row.origem_tipo or '')
        oid=row.origem_id
        if origem in ('compra','venda','despesa') and oid:
            oid=int(oid); conn=get_conn()
            try:
                if origem=='compra':
                    comp=conn.execute("SELECT qtd FROM compras WHERE id=?",(oid,)).fetchone()
                    if comp:
                        q=float(comp['qtd'] or 0); preco_origem=valor/q if q>0 else 0
                        conn.execute("UPDATE compras SET fornecedor=?,valor_total=?,preco_kg=?,vencimento=? WHERE id=?",(pessoa,valor,preco_origem,vencimento,oid))
                elif origem=='despesa':
                    conn.execute("UPDATE despesas SET valor=?,vencimento=?,descricao=? WHERE id=?",(valor,vencimento,descricao,oid))
                elif origem=='venda':
                    venda=conn.execute("SELECT qtd_kg,preco_kg FROM vendas WHERE id=?",(oid,)).fetchone()
                    if venda:
                        bruto=float(venda['qtd_kg'] or 0)*float(venda['preco_kg'] or 0); desconto=max(0.0,bruto-valor)
                        conn.execute("UPDATE vendas SET cliente=?,valor_total=?,desconto=?,vencimento=? WHERE id=?",(pessoa,valor,desconto,vencimento,oid))
                conn.commit()
            finally: conn.close()
            sincronizar_origem_financeira(origem,oid)
        st.success('Correção salva com sucesso.'); st.rerun()

def _grid_vendas():
    df=df_query("SELECT id,pedido,cliente,produto,qtd_kg,preco_kg,desconto,valor_total,data_venda,forma_pagamento,status_pagamento,valor_recebido,vencimento,observacoes FROM vendas ORDER BY id DESC")
    if df.empty:
        return
    st.markdown("### ✏️ Vendas — edição direta no grid")
    st.caption("Edite a célula diretamente. Ao salvar, o valor da venda, estoque, contas a receber e caixa são recalculados.")
    editado=st.data_editor(df,key="grid_vendas",use_container_width=True,hide_index=True,num_rows="fixed",disabled=["id","valor_total","status_pagamento"],height=500)
    if st.button("💾 Salvar alterações das vendas",key="save_grid_vendas"):
        orig=df.set_index("id",drop=False); alterados=0; erro=None
        for _,row in editado.iterrows():
            rid=int(row["id"]); old=orig.loc[rid]
            campos=["pedido","cliente","produto","qtd_kg","preco_kg","desconto","data_venda","forma_pagamento","valor_recebido","vencimento","observacoes"]
            if not any(str(row[c])!=str(old[c]) for c in campos): continue
            qtd=float(row["qtd_kg"] or 0); preco=float(row["preco_kg"] or 0); desconto=float(row["desconto"] or 0)
            if qtd<=0 or preco<0:
                erro=f"Venda #{rid}: quantidade/preço inválidos."; break
            produto=str(row["produto"] or "")
            disponivel=estoque_produto(produto)
            old_prod=str(old["produto"] or ""); old_q=float(old["qtd_kg"] or 0)
            if produto==old_prod: disponivel += old_q
            if disponivel < qtd:
                erro=f"Venda #{rid}: estoque insuficiente para {produto}. Disponível para essa alteração: {disponivel:.2f}."; break
            total=max(0.0,qtd*preco-desconto); recebido=min(max(float(row["valor_recebido"] or 0),0),total); status=_status_por_saldo(total,recebido)
            conn=get_conn()
            try:
                conn.execute("UPDATE vendas SET pedido=?,cliente=?,produto=?,qtd_kg=?,preco_kg=?,desconto=?,valor_total=?,data_venda=?,forma_pagamento=?,status_pagamento=?,valor_recebido=?,vencimento=?,observacoes=? WHERE id=?",
                    (str(row["pedido"] or ""),str(row["cliente"] or ""),produto,qtd,preco,desconto,total,str(row["data_venda"] or ""),str(row["forma_pagamento"] or ""),status,recebido,str(row["vencimento"] or ""),str(row["observacoes"] or ""),rid))
                conn.commit()
            finally: conn.close()
            sincronizar_origem_financeira("venda",rid); alterados+=1
        if erro:
            st.error(erro)
        elif alterados:
            st.success(f"{alterados} venda(s) alterada(s) com estoque e financeiro recalculados."); st.rerun()
        else: st.info("Nenhuma alteração foi detectada.")
    _fallback_venda(df)


def _fallback_venda(df):
    st.markdown("#### 🛠️ Correção individual da venda")
    op={f"#{int(r.id)} — {str(r.pedido)} — {str(r.produto)}":int(r.id) for _,r in df.iterrows()}
    escolha=st.selectbox("Selecione a venda",list(op),key="fallback_venda_sel")
    rid=op[escolha]; row=df[df.id==rid].iloc[0]
    with st.form("fallback_venda_form"):
        c1,c2=st.columns(2)
        pedido=c1.text_input("Pedido",value="" if pd.isna(row.pedido) else str(row.pedido))
        cliente=c2.text_input("Cliente",value="" if pd.isna(row.cliente) else str(row.cliente))
        produto=st.text_input("Produto",value="" if pd.isna(row.produto) else str(row.produto))
        c3,c4,c5=st.columns(3)
        qtd=c3.number_input("Quantidade",min_value=0.0,value=float(row.qtd_kg or 0),step=0.01)
        preco=c4.number_input("Preço",min_value=0.0,value=float(row.preco_kg or 0),step=0.01)
        desconto=c5.number_input("Desconto",min_value=0.0,value=float(row.desconto or 0),step=0.01)
        data_venda=st.text_input("Data da venda (AAAA-MM-DD)",value="" if pd.isna(row.data_venda) else str(row.data_venda))
        forma=st.text_input("Forma de pagamento",value="" if pd.isna(row.forma_pagamento) else str(row.forma_pagamento))
        recebido=st.number_input("Valor recebido",min_value=0.0,value=float(row.valor_recebido or 0),step=0.01)
        venc=st.text_input("Vencimento (AAAA-MM-DD)",value="" if pd.isna(row.vencimento) else str(row.vencimento))
        obs=st.text_area("Observações",value="" if pd.isna(row.observacoes) else str(row.observacoes))
        salvar=st.form_submit_button("💾 Salvar correção da venda")
    if salvar:
        total=max(0.0,qtd*preco-desconto); recebido=min(max(recebido,0),total); status=_status_por_saldo(total,recebido)
        old_prod=str(row.produto or ""); disponivel=estoque_produto(produto)+(float(row.qtd_kg or 0) if produto==old_prod else 0)
        if qtd<=0 or preco<0: st.error("Quantidade/preço inválidos."); return
        if disponivel<qtd: st.error(f"Estoque insuficiente. Disponível para esta alteração: {disponivel:.2f}."); return
        conn=get_conn()
        try:
            conn.execute("UPDATE vendas SET pedido=?,cliente=?,produto=?,qtd_kg=?,preco_kg=?,desconto=?,valor_total=?,data_venda=?,forma_pagamento=?,status_pagamento=?,valor_recebido=?,vencimento=?,observacoes=? WHERE id=?",(pedido,cliente,produto,qtd,preco,desconto,total,data_venda,forma,status,recebido,venc,obs,rid)); conn.commit()
        finally: conn.close()
        sincronizar_origem_financeira('venda',rid); st.success('Venda corrigida e vínculos recalculados.'); st.rerun()


def _fallback_compra(df):
    st.markdown("#### 🛠️ Correção individual da compra")
    op={f"#{int(r.id)} — {str(r.fornecedor)} — {str(r.produto)}":int(r.id) for _,r in df.iterrows()}
    escolha=st.selectbox("Selecione a compra",list(op),key="fallback_compra_sel")
    rid=op[escolha]; row=df[df.id==rid].iloc[0]
    with st.form("fallback_compra_form"):
        fornecedor=st.text_input("Fornecedor",value="" if pd.isna(row.fornecedor) else str(row.fornecedor))
        produto=st.text_input("Produto",value="" if pd.isna(row.produto) else str(row.produto))
        c1,c2=st.columns(2)
        qtd=c1.number_input("Quantidade",min_value=0.0,value=float(row.qtd or 0),step=0.01)
        preco=c2.number_input("Preço",min_value=0.0,value=float(row.preco_kg or 0),step=0.01)
        data_compra=st.text_input("Data da compra (AAAA-MM-DD)",value="" if pd.isna(row.data_compra) else str(row.data_compra))
        lote=st.text_input("Lote",value="" if pd.isna(row.lote) else str(row.lote)); validade=st.text_input("Validade (AAAA-MM-DD)",value="" if pd.isna(row.validade) else str(row.validade))
        forma=st.text_input("Forma de pagamento",value="" if pd.isna(row.forma_pagamento) else str(row.forma_pagamento)); venc=st.text_input("Vencimento (AAAA-MM-DD)",value="" if pd.isna(row.vencimento) else str(row.vencimento)); obs=st.text_area("Observações",value="" if pd.isna(row.observacoes) else str(row.observacoes))
        salvar=st.form_submit_button("💾 Salvar correção da compra")
    if salvar:
        if qtd<=0 or preco<0: st.error('Quantidade/preço inválidos.'); return
        total=qtd*preco; conn=get_conn()
        try:
            conn.execute("UPDATE compras SET fornecedor=?,produto=?,qtd=?,preco_kg=?,valor_total=?,data_compra=?,lote=?,validade=?,forma_pagamento=?,vencimento=?,observacoes=? WHERE id=?",(fornecedor,produto,qtd,preco,total,data_compra,lote,validade,forma,venc,obs,rid)); conn.commit()
        finally: conn.close()
        sincronizar_origem_financeira('compra',rid); st.success('Compra corrigida e vínculos recalculados.'); st.rerun()

def _grid_compras():
    df=df_query("SELECT id,fornecedor,produto,qtd,preco_kg,valor_total,data_compra,lote,validade,forma_pagamento,status_pagamento,vencimento,observacoes FROM compras ORDER BY id DESC")
    if df.empty: return
    st.markdown("### ✏️ Compras — edição direta no grid")
    st.caption("Edite a célula diretamente. Ao salvar, estoque, contas a pagar e caixa são recalculados.")
    editado=st.data_editor(df,key="grid_compras",use_container_width=True,hide_index=True,num_rows="fixed",disabled=["id","valor_total","status_pagamento"],height=500)
    if st.button("💾 Salvar alterações das compras",key="save_grid_compras"):
        orig=df.set_index("id",drop=False); alterados=0
        for _,row in editado.iterrows():
            rid=int(row["id"]); old=orig.loc[rid]
            campos=["fornecedor","produto","qtd","preco_kg","data_compra","lote","validade","forma_pagamento","vencimento","observacoes"]
            if not any(str(row[c])!=str(old[c]) for c in campos): continue
            qtd=float(row["qtd"] or 0); preco=float(row["preco_kg"] or 0)
            if qtd<=0 or preco<0:
                st.error(f"Compra #{rid}: quantidade/preço inválidos."); continue
            total=qtd*preco
            conn=get_conn()
            try:
                conn.execute("UPDATE compras SET fornecedor=?,produto=?,qtd=?,preco_kg=?,valor_total=?,data_compra=?,lote=?,validade=?,forma_pagamento=?,vencimento=?,observacoes=? WHERE id=?",
                    (str(row["fornecedor"] or ""),str(row["produto"] or ""),qtd,preco,total,str(row["data_compra"] or ""),str(row["lote"] or ""),str(row["validade"] or ""),str(row["forma_pagamento"] or ""),str(row["vencimento"] or ""),str(row["observacoes"] or ""),rid)); conn.commit()
            finally: conn.close()
            sincronizar_origem_financeira("compra",rid); alterados+=1
        if alterados: st.success(f"{alterados} compra(s) alterada(s) com estoque e financeiro recalculados."); st.rerun()
        else: st.info("Nenhuma alteração foi detectada.")
    _fallback_compra(df)


def pagina_clientes():
    st.title("👥 Clientes")
    with st.form("novo_cliente"):
        c1,c2,c3=st.columns(3)
        nome=c1.text_input("Nome *"); telefone=c2.text_input("Telefone"); cidade=c3.text_input("Cidade")
        endereco=st.text_input("Endereço")
        salvar=st.form_submit_button("Cadastrar cliente")
        if salvar:
            if not nome.strip(): st.error("Informe o nome.")
            else:
                conn=get_conn()
                try:
                    existe=conn.execute("SELECT id FROM clientes WHERE lower(nome)=lower(?)",(nome.strip(),)).fetchone()
                    if existe: st.warning("Esse cliente já está cadastrado.")
                    else:
                        conn.execute("INSERT INTO clientes (nome,telefone,cidade,endereco,data_cad) VALUES (?,?,?,?,?)",(nome.strip(),telefone,cidade,endereco,hoje())); conn.commit(); st.success("Cliente cadastrado."); st.rerun()
                finally: conn.close()
    _grid_simples("clientes","Clientes",["nome","telefone","cidade","endereco"],["id","data_cad"])

def pagina_fornecedores():
    st.title("🚚 Fornecedores")
    with st.form("novo_fornecedor"):
        c1,c2,c3=st.columns(3)
        nome=c1.text_input("Fornecedor *"); contato=c2.text_input("Contato"); telefone=c3.text_input("Telefone")
        endereco=st.text_input("Endereço"); produto_fornecido=st.text_input("Produtos fornecidos"); prazo=st.text_input("Prazo de pagamento"); obs=st.text_area("Observações")
        salvar=st.form_submit_button("Cadastrar fornecedor")
        if salvar:
            if not nome.strip(): st.error("Informe o fornecedor.")
            else:
                conn=get_conn(); conn.execute("INSERT INTO fornecedores (fornecedor,contato,telefone,endereco,produto_fornecido,prazo_pagamento,observacoes) VALUES (?,?,?,?,?,?,?)",(nome,contato,telefone,endereco,produto_fornecido,prazo,obs)); conn.commit(); conn.close(); st.success("Fornecedor cadastrado."); st.rerun()
    _grid_simples("fornecedores","Fornecedores",["fornecedor","contato","telefone","endereco","produto_fornecido","prazo_pagamento","observacoes"],["id"])

def pagina_produtos():
    st.title("🐟 Cadastro Mestre de Produtos")
    with st.form("novo_produto"):
        c1,c2,c3,c4=st.columns(4)
        nome=c1.text_input("Produto *"); categoria=c2.selectbox("Categoria",CATEGORIAS_PRODUTO); unidade=c3.selectbox("Unidade",["kg","un","g","pacote","caixa"]); estoque_min=c4.number_input("Estoque mínimo",min_value=0.0,step=0.1)
        preco=st.number_input("Preço de venda padrão",min_value=0.0,step=0.01); salvar=st.form_submit_button("Cadastrar produto")
        if salvar:
            if not nome.strip(): st.error("Informe o produto.")
            else:
                conn=get_conn()
                try:
                    conn.execute("INSERT INTO produtos (nome,categoria,unidade,preco_venda,estoque_minimo) VALUES (?,?,?,?,?)",(nome.strip(),categoria,unidade,preco,estoque_min)); conn.commit(); st.success("Produto cadastrado."); st.rerun()
                except sqlite3.IntegrityError: st.error("Esse produto já existe.")
                finally: conn.close()
    _grid_simples("produtos","Produtos",["nome","categoria","unidade","preco_venda","estoque_minimo"],["id","custo_medio","ativo"])

def pagina_compras():
    st.title("📥 Compras")
    produtos=get_produtos(); fornecedores=df_query("SELECT fornecedor FROM fornecedores ORDER BY fornecedor"); lp=produtos["nome"].tolist() if not produtos.empty else []; lf=fornecedores["fornecedor"].tolist() if not fornecedores.empty else []
    with st.form("nova_compra"):
        c1,c2,c3=st.columns(3); fornecedor=c1.selectbox("Fornecedor",[""]+lf); produto=c2.selectbox("Produto *",lp if lp else ["Cadastre produtos primeiro"]); qtd=c3.number_input("Quantidade",min_value=0.0,step=0.1); preco=st.number_input("Preço por kg/unidade",min_value=0.0,step=0.01)
        st.info(f"Valor total: {moeda(qtd*preco)}")
        c4,c5,c6=st.columns(3); dc=c4.date_input("Data",value=date.today()); lote=c5.text_input("Lote"); validade=c6.date_input("Validade",value=date.today())
        c7,c8,c9=st.columns(3); forma=c7.selectbox("Forma de pagamento",FORMAS_PAGAMENTO,index=5); status=c8.selectbox("Status",STATUS_PAGAMENTO,index=0 if forma!="A prazo" else 1); venc=c9.date_input("Vencimento",value=date.today()); obs=st.text_area("Observações")
        salvar=st.form_submit_button("Registrar compra")
        if salvar:
            if not lp: st.error("Cadastre produtos antes de registrar compras.")
            elif qtd<=0 or preco<=0: st.error("Informe quantidade e preço maiores que zero.")
            else: registrar_compra(fornecedor,produto,qtd,preco,dc.strftime("%Y-%m-%d"),lote,validade.strftime("%Y-%m-%d"),forma,status,venc.strftime("%Y-%m-%d"),obs); st.success("Compra registrada e estoque atualizado."); st.rerun()
    _grid_compras()

def pagina_vendas():
    st.title("🧾 Vendas e Pagamentos")
    produtos=get_produtos(); clientes=df_query("SELECT nome FROM clientes ORDER BY nome"); lp=produtos["nome"].tolist() if not produtos.empty else []; lc=clientes["nome"].tolist() if not clientes.empty else []
    with st.form("nova_venda"):
        pedido=st.text_input("Número do pedido",value=proximo_pedido()); c1,c2,c3=st.columns(3); cliente=c1.selectbox("Cliente",[""]+lc); produto=c2.selectbox("Produto *",lp if lp else ["Cadastre produtos primeiro"]); qtd=c3.number_input("Quantidade (kg/un)",min_value=0.0,step=0.1)
        preco_padrao=float(produtos[produtos["nome"]==produto].iloc[0]["preco_venda"] or 0) if produto in lp else 0.0
        c4,c5,c6=st.columns(3); preco=c4.number_input("Preço por kg/unidade",min_value=0.0,value=preco_padrao,step=0.01); desconto=c5.number_input("Desconto",min_value=0.0,step=0.01); dv=c6.date_input("Data",value=date.today()); total=max(0.0,qtd*preco-desconto); st.metric("Total da venda",moeda(total))
        c7,c8,c9=st.columns(3); forma=c7.selectbox("Forma de pagamento",FORMAS_PAGAMENTO); status=c8.selectbox("Status",STATUS_PAGAMENTO); recebido=c9.number_input("Valor recebido",min_value=0.0,max_value=max(total,0.0),step=0.01); venc=st.date_input("Vencimento",value=date.today()); obs=st.text_area("Observações"); salvar=st.form_submit_button("Registrar venda")
        if salvar:
            if not lp: st.error("Cadastre produtos antes de vender.")
            elif qtd<=0 or preco<=0: st.error("Informe quantidade e preço maiores que zero.")
            elif estoque_produto(produto)<qtd: st.error(f"Estoque insuficiente. Estoque atual de {produto}: {estoque_produto(produto):.2f}")
            else: registrar_venda(pedido,cliente,produto,qtd,preco,desconto,dv.strftime("%Y-%m-%d"),forma,status,recebido,venc.strftime("%Y-%m-%d"),obs); st.success(f"Venda {pedido} registrada."); st.rerun()
    _grid_vendas()

def pagina_estoque():
    st.title("📦 Estoque")
    produtos = get_produtos()

    if produtos.empty:
        st.info("Cadastre produtos primeiro.")
        return

    st.subheader("🔗 Estoque integrado: Compras − Vendas + Ajustes")
    df = resumo_estoque()
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption("O estoque atual é calculado diretamente pelas compras registradas menos as vendas registradas, considerando também perdas e ajustes manuais.")

    st.markdown("---")
    st.subheader("Registrar perda ou ajuste")
    with st.form("ajuste_estoque"):
        produto = st.selectbox("Produto", produtos["nome"].tolist())
        tipo = st.selectbox("Tipo", ["Perda", "Ajuste Entrada", "Ajuste Saída"])
        qtd = st.number_input("Quantidade", min_value=0.0, step=0.1)
        obs = st.text_input("Motivo/observação")
        salvar = st.form_submit_button("Registrar movimentação")
        if salvar:
            if qtd <= 0:
                st.error("Informe uma quantidade.")
            else:
                registrar_movimento(produto, tipo, qtd, 0, "manual", None, obs)
                st.success("Movimentação registrada e estoque atualizado.")
                st.rerun()

    st.subheader("Histórico de movimentações")
    renderizar_tabela_simples("movimentos_estoque", "Movimentações")

def pagina_financeiro():
    st.title("💰 Financeiro Integrado")

    realizado = obter_extrato_realizado()
    previsto = obter_previsto()

    entradas = float(realizado.loc[realizado["tipo"] == "Entrada", "valor"].sum()) if not realizado.empty else 0
    saidas = float(realizado.loc[realizado["tipo"] == "Saída", "valor"].sum()) if not realizado.empty else 0
    saldo = entradas - saidas

    receber = float(scalar("""
        SELECT COALESCE(SUM(CASE WHEN valor - COALESCE(valor_recebido,0) > 0 THEN valor - COALESCE(valor_recebido,0) ELSE 0 END),0)
        FROM contas_receber WHERE status IN ('Pendente','Parcial')
    """) or 0)
    pagar = float(scalar("""
        SELECT COALESCE(SUM(CASE WHEN valor - COALESCE(valor_pago,0) > 0 THEN valor - COALESCE(valor_pago,0) ELSE 0 END),0)
        FROM contas_pagar WHERE status IN ('Pendente','Parcial')
    """) or 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entradas realizadas", moeda(entradas))
    c2.metric("Saídas realizadas", moeda(saidas))
    c3.metric("Caixa realizado", moeda(saldo))
    c4.metric("Saldo futuro líquido", moeda(receber - pagar))

    st.markdown("### 🔗 Integração automática")
    resumo = resumo_financeiro_por_origem()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🛒 Compras pagas", moeda(resumo["Compras pagas"]))
    c2.metric("🧾 Vendas recebidas", moeda(resumo["Vendas recebidas"]))
    c3.metric("💳 Despesas pagas", moeda(resumo["Despesas pagas"]))
    c4.metric("💸 A pagar", moeda(resumo["Contas a pagar"]))
    c5.metric("💵 A receber", moeda(resumo["Contas a receber"]))

    st.caption(
        "Compras, vendas e despesas entram automaticamente no caixa quando efetivamente pagas/recebidas. "
        "O que ficar pendente ou parcial aparece em Contas a Pagar/Receber."
    )

    tab1, tab2, tab3 = st.tabs(["Caixa realizado", "Compromissos futuros", "Origem das movimentações"])

    with tab1:
        if realizado.empty:
            st.info("Nenhuma movimentação realizada.")
        else:
            exib = realizado.copy()
            exib["origem"] = exib.get("origem_tipo", "")
            st.dataframe(exib, use_container_width=True, hide_index=True)

    with tab2:
        if previsto.empty:
            st.info("Nenhum compromisso pendente.")
        else:
            st.dataframe(previsto.sort_values("data"), use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Compras")
        compras = df_query("""
            SELECT id, data_compra AS data, fornecedor, produto, valor_total,
                   forma_pagamento, status_pagamento, vencimento
            FROM compras ORDER BY id DESC
        """)
        st.dataframe(compras, use_container_width=True, hide_index=True)

        st.subheader("Vendas")
        vendas = df_query("""
            SELECT id, pedido, data_venda AS data, cliente, produto, valor_total,
                   valor_recebido, (valor_total - COALESCE(valor_recebido,0)) AS saldo,
                   forma_pagamento, status_pagamento, vencimento
            FROM vendas ORDER BY id DESC
        """)
        st.dataframe(vendas, use_container_width=True, hide_index=True)

        st.subheader("Despesas")
        despesas = df_query("""
            SELECT id, data_desp AS data, categoria, descricao, valor,
                   pagamento, status, vencimento
            FROM despesas ORDER BY id DESC
        """)
        st.dataframe(despesas, use_container_width=True, hide_index=True)

        st.subheader("Contas a pagar")
        cp = df_query("""
            SELECT id, fornecedor, descricao, valor, COALESCE(valor_pago,0) AS pago,
                   MAX(valor-COALESCE(valor_pago,0),0) AS saldo, vencimento, status,
                   origem_tipo, origem_id
            FROM contas_pagar ORDER BY date(vencimento), id DESC
        """)
        st.dataframe(cp, use_container_width=True, hide_index=True)

        st.subheader("Contas a receber")
        cr = df_query("""
            SELECT id, cliente, descricao, valor, COALESCE(valor_recebido,0) AS recebido,
                   MAX(valor-COALESCE(valor_recebido,0),0) AS saldo, vencimento, status,
                   origem_tipo, origem_id
            FROM contas_receber ORDER BY date(vencimento), id DESC
        """)
        st.dataframe(cr, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("➕ Movimentação financeira manual")
    with st.form("financeiro_manual"):
        c1, c2, c3 = st.columns(3)
        data_mov = c1.date_input("Data", value=date.today())
        tipo = c2.selectbox("Tipo", ["Entrada", "Saída"])
        valor = c3.number_input("Valor", min_value=0.0, step=0.01)
        descricao = st.text_input("Descrição")
        forma = st.selectbox("Forma de pagamento", FORMAS_PAGAMENTO)
        salvar = st.form_submit_button("Lançar")
        if salvar:
            if valor <= 0 or not descricao.strip():
                st.error("Informe descrição e valor.")
            else:
                registrar_financeiro(
                    data_mov.strftime("%Y-%m-%d"), descricao, tipo, valor,
                    forma, "manual", None
                )
                st.success("Lançamento realizado.")
                st.rerun()



def pagina_contas_pagar():
    st.title("💸 Contas a Pagar")
    df=df_query("""SELECT id,fornecedor,descricao,valor,COALESCE(valor_pago,0) AS valor_pago,MAX(valor-COALESCE(valor_pago,0),0) AS saldo,vencimento,status,origem_tipo,origem_id FROM contas_pagar ORDER BY date(vencimento),id DESC""")
    if df.empty: st.info("Nenhuma conta a pagar."); return
    pend=df[(df["status"].isin(["Pendente","Parcial"]))&(df["saldo"]>0)]
    if not pend.empty:
        st.subheader("Registrar pagamento")
        op={f"#{int(r.id)} - {r.fornecedor} - {r.descricao} - Saldo {moeda(r.saldo)}":int(r.id) for _,r in pend.iterrows()}; escolha=st.selectbox("Conta",list(op),key="pagar_conta_sel"); valor_pago=st.number_input("Valor pago",min_value=0.0,step=0.01,key="pagar_valor"); forma=st.selectbox("Forma",FORMAS_PAGAMENTO,key="pagar_forma")
        if st.button("Confirmar pagamento",key="btn_pagar_novo"):
            rid=op[escolha]; row=df[df.id==rid].iloc[0]; valor=min(float(valor_pago),float(row.saldo))
            if valor<=0: st.error("Informe um valor maior que zero.")
            else:
                novo=float(row.valor_pago or 0)+valor; status="Pago" if novo>=float(row.valor) else "Parcial"; conn=get_conn(); conn.execute("UPDATE contas_pagar SET valor_pago=?,status=? WHERE id=?",(novo,status,rid)); conn.commit(); conn.close(); registrar_financeiro(hoje(),f"Pagamento conta a pagar #{rid} - {row.descricao}","Saída",valor,forma,"conta_pagar",rid); st.success("Pagamento registrado."); st.rerun()
    _grid_contas("contas_pagar","Contas a Pagar","fornecedor","valor_pago")


def pagina_contas_receber():
    st.title("💵 Contas a Receber")
    df=df_query("""SELECT id,cliente,descricao,valor,COALESCE(valor_recebido,0) AS valor_recebido,MAX(valor-COALESCE(valor_recebido,0),0) AS saldo,vencimento,status,origem_tipo,origem_id FROM contas_receber ORDER BY date(vencimento),id DESC""")
    if df.empty: st.info("Nenhuma conta a receber."); return
    pend=df[(df["status"].isin(["Pendente","Parcial"]))&(df["saldo"]>0)]
    if not pend.empty:
        st.subheader("Registrar recebimento")
        op={f"#{int(r.id)} - {r.cliente} - {r.descricao} - Saldo {moeda(r.saldo)}":int(r.id) for _,r in pend.iterrows()}; escolha=st.selectbox("Conta",list(op),key="receber_conta_sel"); valor_recebido=st.number_input("Valor recebido",min_value=0.0,step=0.01,key="receber_valor"); forma=st.selectbox("Forma",FORMAS_PAGAMENTO,key="receber_forma")
        if st.button("Confirmar recebimento",key="btn_receber_novo"):
            rid=op[escolha]; row=df[df.id==rid].iloc[0]; valor=min(float(valor_recebido),float(row.saldo))
            if valor<=0: st.error("Informe um valor maior que zero.")
            else:
                novo=float(row.valor_recebido or 0)+valor; status="Pago" if novo>=float(row.valor) else "Parcial"; conn=get_conn(); conn.execute("UPDATE contas_receber SET valor_recebido=?,status=? WHERE id=?",(novo,status,rid)); conn.commit(); conn.close(); registrar_financeiro(hoje(),f"Recebimento conta a receber #{rid} - {row.descricao}","Entrada",valor,forma,"conta_receber",rid); st.success("Recebimento registrado."); st.rerun()
    _grid_contas("contas_receber","Contas a Receber","cliente","valor_recebido")

def pagina_despesas():
    st.title("🧾 Despesas Gerais")
    with st.form("nova_despesa"):
        c1, c2, c3 = st.columns(3)
        data_desp = c1.date_input("Data", value=date.today())
        categoria = c2.text_input("Categoria")
        valor = c3.number_input("Valor", min_value=0.0, step=0.01)
        descricao = st.text_input("Descrição")
        forma = st.selectbox("Pagamento", FORMAS_PAGAMENTO)
        status = st.selectbox("Status", STATUS_PAGAMENTO)
        valor_pago = st.number_input(
            "Valor já pago (use em pagamento parcial)",
            min_value=0.0, max_value=max(float(valor), 0.0), step=0.01
        )
        venc = st.date_input("Vencimento", value=date.today())
        salvar = st.form_submit_button("Registrar despesa")

        if salvar:
            if valor <= 0:
                st.error("Informe o valor.")
            else:
                if status == "Pago":
                    valor_pago_final = float(valor)
                elif status == "Parcial":
                    valor_pago_final = min(float(valor_pago), float(valor))
                else:
                    valor_pago_final = 0.0

                status_final = (
                    "Pago" if valor_pago_final >= float(valor)
                    else ("Parcial" if valor_pago_final > 0 else "Pendente")
                )

                conn = get_conn()
                cur = conn.execute("""
                    INSERT INTO despesas
                    (data_desp,categoria,descricao,valor,pagamento,status,vencimento)
                    VALUES (?,?,?,?,?,?,?)
                """, (data_desp.strftime("%Y-%m-%d"), categoria, descricao, valor,
                      forma, status_final, venc.strftime("%Y-%m-%d")))
                desp_id = cur.lastrowid
                conn.commit()
                conn.close()

                # DESPESA -> CAIXA pelo valor já pago.
                if valor_pago_final > 0:
                    registrar_financeiro(
                        data_desp.strftime("%Y-%m-%d"),
                        f"Despesa #{desp_id}: {categoria} - {descricao}",
                        "Saída", valor_pago_final, forma, "despesa", desp_id
                    )

                # DESPESA -> CONTAS A PAGAR pelo saldo.
                saldo = float(valor) - valor_pago_final
                if saldo > 0:
                    garantir_conta_pagar(
                        "", f"Despesa #{desp_id}: {categoria} - {descricao}",
                        saldo, venc.strftime("%Y-%m-%d"), "despesa", desp_id
                    )

                st.success("Despesa integrada ao Financeiro.")
                st.rerun()

    _grid_simples("despesas","Despesas",["data_desp","categoria","descricao","valor","pagamento","status","vencimento"],["id"])


def pagina_entregas():
    st.title("🚚 Entregas")
    vendas = df_query("SELECT pedido, cliente FROM vendas ORDER BY id DESC")
    pedidos = [f"{r['pedido']} - {r['cliente']}" for _, r in vendas.iterrows()] if not vendas.empty else []

    with st.form("nova_entrega"):
        pedido_display = st.selectbox("Pedido", [""] + pedidos)
        cliente = ""
        if pedido_display:
            pedido = pedido_display.split(" - ", 1)[0]
            row = vendas[vendas["pedido"] == pedido].iloc[0]
            cliente = row["cliente"]
        else:
            pedido = ""
        st.text_input("Cliente", value=cliente, disabled=True)

        c1, c2, c3 = st.columns(3)
        data_ent = c1.date_input("Data", value=date.today())
        bairro = c2.text_input("Bairro")
        cidade = c3.text_input("Cidade")
        endereco = st.text_input("Endereço")
        c4, c5, c6 = st.columns(3)
        entregador = c4.text_input("Entregador")
        taxa = c5.number_input("Taxa de entrega", min_value=0.0, step=0.01)
        status = c6.selectbox("Status", STATUS_ENTREGA)
        obs = st.text_area("Observações")
        salvar = st.form_submit_button("Cadastrar entrega")

        if salvar:
            conn = get_conn()
            conn.execute("""
                INSERT INTO entregas
                (pedido,cliente,data_ent,endereco,bairro,cidade,entregador,taxa_entrega,status,observacoes)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (pedido, cliente, data_ent.strftime("%Y-%m-%d"), endereco, bairro,
                  cidade, entregador, taxa, status, obs))
            conn.commit()
            conn.close()
            st.success("Entrega cadastrada.")
            st.rerun()

    _grid_simples("entregas","Entregas",["pedido","cliente","data_ent","endereco","bairro","cidade","entregador","taxa_entrega","status","observacoes"],["id"])
    return


def pagina_relatorios():
    st.title("📊 Relatórios Gerenciais")

    vendas = df_query("SELECT * FROM vendas")
    compras = df_query("SELECT * FROM compras")
    despesas = df_query("SELECT * FROM despesas")
    financeiro = obter_extrato_realizado()

    faturamento = float(vendas["valor_total"].sum()) if not vendas.empty else 0
    custo_compras = float(compras["valor_total"].sum()) if not compras.empty else 0
    total_despesas = float(despesas["valor"].sum()) if not despesas.empty else 0

    # Aproximação gerencial pelo período total. O custo exato por venda depende do método
    # de custeio escolhido; o sistema mantém custo médio dos produtos para evolução futura.
    lucro_bruto_aprox = faturamento - custo_compras
    lucro_liquido_aprox = faturamento - custo_compras - total_despesas

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faturamento", moeda(faturamento))
    c2.metric("Compras", moeda(custo_compras))
    c3.metric("Despesas", moeda(total_despesas))
    c4.metric("Lucro líquido aprox.", moeda(lucro_liquido_aprox))

    st.warning(
        "O lucro acima é uma visão gerencial aproximada do período total. "
        "Para lucro por venda, o sistema deve usar custo médio/PEPS por lote."
    )

    if not vendas.empty:
        st.subheader("Vendas por produto")
        resumo = vendas.groupby("produto").agg(
            quantidade=("qtd_kg", "sum"),
            faturamento=("valor_total", "sum")
        ).reset_index()
        st.dataframe(resumo, use_container_width=True, hide_index=True)

    if not financeiro.empty:
        st.subheader("Fluxo de caixa realizado")
        fx = financeiro.copy()
        fx["valor"] = pd.to_numeric(fx["valor"], errors="coerce").fillna(0)
        fluxo = fx.groupby(["data", "tipo"])["valor"].sum().reset_index()
        st.dataframe(fluxo, use_container_width=True, hide_index=True)


def pagina_normas():
    st.title("📋 Normas e Procedimentos")
    st.markdown("""
### Higiene e manipulação
- Utilizar EPIs adequados.
- Manter bancadas, utensílios e equipamentos higienizados.
- Manter a cadeia de frio adequada ao produto.
- Conferir peso, temperatura e integridade no recebimento.

### Estoque
- Aplicar PEPS/FIFO sempre que possível.
- Registrar entradas, saídas, perdas e ajustes.
- Conferir lote e validade.
- Não vender quantidade superior ao estoque disponível.

### Vendas
- Toda saída deve possuir pedido.
- Registrar forma de pagamento.
- Registrar valor efetivamente recebido.
- Vendas a prazo devem gerar conta a receber.

### Financeiro
- Caixa realizado representa apenas dinheiro efetivamente recebido/pago.
- Contas pendentes ficam separadas como compromissos futuros.
- Evitar lançar manualmente novamente uma movimentação que já foi gerada pelo sistema.
""")


def pagina_importar():
    st.title("📥 Importar dados da planilha Kero Fish")
    st.info("A planilha Kero_Fish_Versao_9_Nosso_Projeto.xlsx é a fonte dos registros históricos. A importação coloca cada registro no respectivo módulo do ERP.")

    arquivo = Path(PLANILHA_BASE)
    if not arquivo.exists():
        # procura também no diretório atual por segurança
        candidatos = list(Path('.').glob('Kero_Fish_Versao_9_Nosso_Projeto.xlsx')) + list(Path('.').glob('Kero_Fish*.xlsx'))
        if candidatos:
            arquivo = candidatos[0]

    if arquivo.exists():
        st.success(f"Planilha encontrada: {arquivo.name}")
        st.markdown("**Serão importados:** Produtos, Clientes, Fornecedores, Compras, Vendas e Financeiro. Compras entram no estoque e vendas saem do estoque.")
        if st.button("🚀 IMPORTAR TODOS OS DADOS DA PLANILHA", type="primary", key="importar_todos_base"):
            try:
                resultado = importar_planilha_base(str(arquivo))
                if resultado.get("erro"):
                    st.error(resultado["erro"])
                else:
                    c = resultado.get("importados", {})
                    st.success(
                        f"Importação concluída: {c.get('produtos',0)} produtos, "
                        f"{c.get('clientes',0)} clientes, {c.get('fornecedores',0)} fornecedores, "
                        f"{c.get('compras',0)} compras, {c.get('vendas',0)} vendas e "
                        f"{c.get('financeiro',0)} lançamentos financeiros."
                    )
                    st.info("O estoque agora é calculado automaticamente por Compras − Vendas + Ajustes.")
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao importar a planilha: {e}")
    else:
        st.error("A planilha Kero_Fish_Versao_9_Nosso_Projeto.xlsx não foi encontrada na pasta do programa.")
        st.warning("Coloque a planilha junto do arquivo Python e abra novamente o aplicativo.")

    st.markdown("---")
    st.subheader("📊 Registros atuais no banco")
    conn = get_conn()
    try:
        for tabela, rotulo in [("produtos","Produtos"),("clientes","Clientes"),("fornecedores","Fornecedores"),("compras","Compras"),("vendas","Vendas"),("financeiro","Financeiro")]:
            qtd = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            st.write(f"**{rotulo}:** {qtd}")
    finally:
        conn.close()


# Inicialização segura: primeiro localiza/reutiliza o banco correto e cria
# uma cópia antes de qualquer migração de estrutura.
garantir_banco_correto()
if os.path.exists(DB_FILE):
    try:
        if _db_record_count(DB_FILE) > 0:
            # backup de segurança antes da migração desta versão
            backups_existentes=list(Path(BACKUP_DIR).glob("kerofish_pre_update_*.db")) if Path(BACKUP_DIR).exists() else []
            if not backups_existentes:
                backup_db("pre_update")
    except Exception:
        pass
init_db()

# IMPORTAÇÃO AUTOMÁTICA DA PLANILHA BASE
# A planilha Versão 9 é a fonte oficial dos dados históricos do nosso projeto.
# A rotina é idempotente: pode ser executada novamente sem duplicar compras/vendas.
# Assim, se a implantação estiver com banco vazio ou incompleto, os registros
# históricos são incorporados ao ERP automaticamente.
try:
    if PLANILHA_BASE.exists():
        importar_planilha_base(str(PLANILHA_BASE))
except Exception as _e_import:
    # Não interrompe o ERP caso a planilha ainda não esteja disponível ou
    # exista alguma incompatibilidade; a importação manual continua disponível.
    pass

# Logo
st.sidebar.title("Kero Fish")
st.sidebar.caption(f"Banco: {Path(DB_FILE).name}")
logo_encontrada = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]:
    if os.path.exists(f"logo.{ext}"):
        logo_encontrada = f"logo.{ext}"
        break

if logo_encontrada:
    st.sidebar.image(logo_encontrada, use_container_width=True)
else:
    uploaded_logo = st.sidebar.file_uploader("Enviar logo", type=["png", "jpg", "jpeg"])
    if uploaded_logo is not None:
        with open("logo.png", "wb") as f:
            f.write(uploaded_logo.getbuffer())
        st.success("Logo salva.")
        st.rerun()

opcao = st.sidebar.radio(
    "Navegação",
    [
        "Painel Geral",
        "Produtos",
        "Fornecedores",
        "Compras",
        "Estoque",
        "Clientes",
        "Vendas",
        "Financeiro",
        "Despesas",
        "Contas a Pagar",
        "Contas a Receber",
        "Entregas",
        "Relatórios",
        "Normas",
        "Importar Planilha",
        "Backup",
    ]
)

if opcao == "Painel Geral":
    painel()
elif opcao == "Produtos":
    pagina_produtos()
elif opcao == "Fornecedores":
    pagina_fornecedores()
elif opcao == "Compras":
    pagina_compras()
elif opcao == "Estoque":
    pagina_estoque()
elif opcao == "Clientes":
    pagina_clientes()
elif opcao == "Vendas":
    pagina_vendas()
elif opcao == "Financeiro":
    pagina_financeiro()
elif opcao == "Despesas":
    pagina_despesas()
elif opcao == "Contas a Pagar":
    pagina_contas_pagar()
elif opcao == "Contas a Receber":
    pagina_contas_receber()
elif opcao == "Entregas":
    pagina_entregas()
elif opcao == "Relatórios":
    pagina_relatorios()
elif opcao == "Normas":
    pagina_normas()
elif opcao == "Importar Planilha":
    pagina_importar()
elif opcao == "Backup":
    pagina_backup()
