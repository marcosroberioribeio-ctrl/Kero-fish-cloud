from __future__ import annotations

import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]

def resolve_db_path() -> Path:
    env = os.getenv("KERO_DB_PATH", "").strip()
    if env: return Path(env).expanduser().resolve()
    return APP_ROOT / "kerofish.db"

DB_PATH = resolve_db_path()
BACKUP_DIR = APP_ROOT / "backups"

@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30); conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON"); conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn; conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

def _columns(conn, table): return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
def _add_column(conn, table, name, definition):
    if name not in _columns(conn, table): conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,telefone TEXT DEFAULT '',cidade TEXT DEFAULT '',endereco TEXT DEFAULT '',data_cad TEXT DEFAULT '',observacoes TEXT DEFAULT '',ativo INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS fornecedores (id INTEGER PRIMARY KEY AUTOINCREMENT,fornecedor TEXT NOT NULL,contato TEXT DEFAULT '',telefone TEXT DEFAULT '',endereco TEXT DEFAULT '',produto_fornecido TEXT DEFAULT '',prazo_pagamento TEXT DEFAULT '',observacoes TEXT DEFAULT '',ativo INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL UNIQUE,categoria TEXT DEFAULT 'Outros',unidade TEXT DEFAULT 'kg',preco_venda REAL DEFAULT 0,custo_medio REAL DEFAULT 0,estoque_minimo REAL DEFAULT 0,ativo INTEGER DEFAULT 1,fornecedor_padrao TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT,fornecedor TEXT DEFAULT '',produto TEXT NOT NULL,qtd REAL DEFAULT 0,preco_kg REAL DEFAULT 0,valor_total REAL DEFAULT 0,data_compra TEXT DEFAULT '',lote TEXT DEFAULT '',validade TEXT DEFAULT '',forma_pagamento TEXT DEFAULT 'A prazo',status_pagamento TEXT DEFAULT 'Pendente',vencimento TEXT DEFAULT '',observacoes TEXT DEFAULT '',source_key TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT,pedido TEXT UNIQUE,cliente TEXT DEFAULT '',produto TEXT NOT NULL,qtd_kg REAL DEFAULT 0,preco_kg REAL DEFAULT 0,desconto REAL DEFAULT 0,valor_total REAL DEFAULT 0,data_venda TEXT DEFAULT '',forma_pagamento TEXT DEFAULT 'Pix',status_pagamento TEXT DEFAULT 'Pago',valor_recebido REAL DEFAULT 0,vencimento TEXT DEFAULT '',observacoes TEXT DEFAULT '',source_key TEXT DEFAULT '',status_pedido TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT,data_desp TEXT DEFAULT '',categoria TEXT DEFAULT '',descricao TEXT DEFAULT '',valor REAL DEFAULT 0,pagamento TEXT DEFAULT 'Pix',status TEXT DEFAULT 'Pago',vencimento TEXT DEFAULT '',observacoes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS contas_pagar (id INTEGER PRIMARY KEY AUTOINCREMENT,fornecedor TEXT DEFAULT '',descricao TEXT DEFAULT '',valor REAL DEFAULT 0,valor_pago REAL DEFAULT 0,vencimento TEXT DEFAULT '',status TEXT DEFAULT 'Pendente',origem_tipo TEXT DEFAULT '',origem_id INTEGER);
        CREATE TABLE IF NOT EXISTS contas_receber (id INTEGER PRIMARY KEY AUTOINCREMENT,cliente TEXT DEFAULT '',descricao TEXT DEFAULT '',valor REAL DEFAULT 0,valor_recebido REAL DEFAULT 0,vencimento TEXT DEFAULT '',status TEXT DEFAULT 'Pendente',origem_tipo TEXT DEFAULT '',origem_id INTEGER);
        CREATE TABLE IF NOT EXISTS entregas (id INTEGER PRIMARY KEY AUTOINCREMENT,pedido TEXT DEFAULT '',cliente TEXT DEFAULT '',data_ent TEXT DEFAULT '',endereco TEXT DEFAULT '',bairro TEXT DEFAULT '',cidade TEXT DEFAULT '',entregador TEXT DEFAULT '',taxa_entrega REAL DEFAULT 0,status TEXT DEFAULT 'Aguardando',observacoes TEXT DEFAULT '',origem_id INTEGER);
        CREATE TABLE IF NOT EXISTS financeiro (id INTEGER PRIMARY KEY AUTOINCREMENT,data_mov TEXT DEFAULT '',descricao TEXT DEFAULT '',tipo TEXT DEFAULT 'Entrada',valor REAL DEFAULT 0,forma_pagamento TEXT DEFAULT '',origem_tipo TEXT DEFAULT '',origem_id INTEGER);
        CREATE TABLE IF NOT EXISTS movimentos_estoque (id INTEGER PRIMARY KEY AUTOINCREMENT,data_mov TEXT DEFAULT '',produto TEXT NOT NULL,tipo TEXT NOT NULL,quantidade REAL DEFAULT 0,custo_unitario REAL DEFAULT 0,origem_tipo TEXT DEFAULT '',origem_id INTEGER,observacoes TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS import_log (id INTEGER PRIMARY KEY AUTOINCREMENT,source_file TEXT NOT NULL,source_sheet TEXT NOT NULL,source_key TEXT NOT NULL,entity_type TEXT NOT NULL,entity_id INTEGER,imported_at TEXT NOT NULL,UNIQUE(source_file,source_sheet,source_key,entity_type));
        CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT,event_time TEXT NOT NULL,action TEXT NOT NULL,entity_type TEXT DEFAULT '',entity_id INTEGER,detail TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS app_meta (key TEXT PRIMARY KEY,value TEXT DEFAULT '');
        """)
        additions={
        "clientes":[("telefone","TEXT DEFAULT ''"),("cidade","TEXT DEFAULT ''"),("endereco","TEXT DEFAULT ''"),("data_cad","TEXT DEFAULT ''"),("observacoes","TEXT DEFAULT ''"),("ativo","INTEGER DEFAULT 1")],
        "fornecedores":[("contato","TEXT DEFAULT ''"),("telefone","TEXT DEFAULT ''"),("endereco","TEXT DEFAULT ''"),("produto_fornecido","TEXT DEFAULT ''"),("prazo_pagamento","TEXT DEFAULT ''"),("observacoes","TEXT DEFAULT ''"),("ativo","INTEGER DEFAULT 1")],
        "produtos":[("fornecedor_padrao","TEXT DEFAULT ''"),("unidade","TEXT DEFAULT 'kg'"),("preco_venda","REAL DEFAULT 0"),("custo_medio","REAL DEFAULT 0"),("estoque_minimo","REAL DEFAULT 0"),("ativo","INTEGER DEFAULT 1")],
        "compras":[("source_key","TEXT DEFAULT ''"),("preco_kg","REAL DEFAULT 0"),("lote","TEXT DEFAULT ''"),("validade","TEXT DEFAULT ''"),("forma_pagamento","TEXT DEFAULT 'A prazo'"),("status_pagamento","TEXT DEFAULT 'Pendente'"),("vencimento","TEXT DEFAULT ''"),("observacoes","TEXT DEFAULT ''")],
        "vendas":[("source_key","TEXT DEFAULT ''"),("status_pedido","TEXT DEFAULT ''"),("pedido","TEXT"),("preco_kg","REAL DEFAULT 0"),("desconto","REAL DEFAULT 0"),("forma_pagamento","TEXT DEFAULT 'Pix'"),("status_pagamento","TEXT DEFAULT 'Pago'"),("valor_recebido","REAL DEFAULT 0"),("vencimento","TEXT DEFAULT ''"),("observacoes","TEXT DEFAULT ''")],
        "despesas":[("observacoes","TEXT DEFAULT ''"),("status","TEXT DEFAULT 'Pago'"),("vencimento","TEXT DEFAULT ''")],"contas_pagar":[("valor_pago","REAL DEFAULT 0")],"contas_receber":[("valor_recebido","REAL DEFAULT 0")],"entregas":[("origem_id","INTEGER")],"financeiro":[("forma_pagamento","TEXT DEFAULT ''"),("origem_tipo","TEXT DEFAULT ''"),("origem_id","INTEGER")]}
        for table,cols in additions.items():
            for name,definition in cols: _add_column(conn,table,name,definition)
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome)")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_compras_source_key ON compras(source_key) WHERE source_key<>''")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_vendas_source_key ON vendas(source_key) WHERE source_key<>''")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_fin_origem ON financeiro(origem_tipo, origem_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cp_origem ON contas_pagar(origem_tipo, origem_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cr_origem ON contas_receber(origem_tipo, origem_id)")

def backup_db(reason="manual"):
    if not DB_PATH.exists(): return None
    BACKUP_DIR.mkdir(parents=True,exist_ok=True); stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    target=BACKUP_DIR/f"kerofish_{reason}_{stamp}.db"; shutil.copy2(DB_PATH,target); return target
