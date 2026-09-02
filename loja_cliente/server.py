from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from kero_fish.db import connect

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
STATIC_DIR = BASE_DIR / "static"
LOGO_PATH = ROOT_DIR / "IMG-20260826-WA0013 (1).jpg"

app = FastAPI(title="Kero Fish Loja", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class OrderItem(BaseModel):
    product_id: int
    name: str = Field(min_length=1, max_length=180)
    quantity: float = Field(gt=0, le=999)
    unit_price: float = Field(ge=0)


class CustomerData(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    phone: str = Field(min_length=8, max_length=30)
    cep: str = Field(min_length=8, max_length=10)
    address: str = Field(min_length=3, max_length=250)
    number: str = Field(min_length=1, max_length=30)
    complement: str = Field(default="", max_length=120)
    neighborhood: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=120)
    notes: str = Field(default="", max_length=500)


class OrderIn(BaseModel):
    customer: CustomerData
    items: list[OrderItem] = Field(min_length=1, max_length=60)
    payment_method: Literal["PIX", "DINHEIRO", "CARTAO_ENTREGA"]


def _ensure_online_schema() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pedidos_online (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                criado_em TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'NOVO',
                cliente_nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                cep TEXT,
                endereco TEXT,
                numero TEXT,
                complemento TEXT,
                bairro TEXT,
                cidade TEXT,
                observacoes TEXT,
                forma_pagamento TEXT NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                taxa_entrega REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                itens_json TEXT NOT NULL,
                origem TEXT NOT NULL DEFAULT 'LOJA_PWA'
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_online_status ON pedidos_online(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pedidos_online_criado ON pedidos_online(criado_em)")
        conn.commit()


def _product_rows():
    with connect() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(produtos)").fetchall()}
        select = ["id", "nome", "COALESCE(preco_venda,0) AS preco_venda"]
        if "categoria" in cols:
            select.append("COALESCE(categoria,'Outros') AS categoria")
        else:
            select.append("'Outros' AS categoria")
        sql = f"SELECT {', '.join(select)} FROM produtos ORDER BY nome"
        return conn.execute(sql).fetchall()


@app.on_event("startup")
def startup() -> None:
    _ensure_online_schema()


@app.get("/api/health")
def health():
    return {"ok": True, "service": "kero-fish-loja", "version": "0.1.0"}


@app.get("/api/products")
def products():
    try:
        rows = _product_rows()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail="Catálogo temporariamente indisponível") from exc

    return [
        {
            "id": int(r[0]),
            "name": str(r[1]),
            "price": float(r[2] or 0),
            "category": str(r[3] or "Outros"),
        }
        for r in rows
    ]


@app.post("/api/orders", status_code=201)
def create_order(order: OrderIn):
    _ensure_online_schema()

    product_ids = {item.product_id for item in order.items}
    with connect() as conn:
        placeholders = ",".join("?" for _ in product_ids)
        rows = conn.execute(
            f"SELECT id,nome,COALESCE(preco_venda,0) FROM produtos WHERE id IN ({placeholders})",
            tuple(product_ids),
        ).fetchall()
        catalog = {int(r[0]): {"name": str(r[1]), "price": float(r[2] or 0)} for r in rows}

        if len(catalog) != len(product_ids):
            raise HTTPException(status_code=400, detail="Um ou mais produtos não estão disponíveis")

        normalized_items = []
        subtotal = 0.0
        for item in order.items:
            product = catalog[item.product_id]
            price = product["price"]
            if price <= 0:
                raise HTTPException(status_code=400, detail=f"Preço indisponível para {product['name']}")
            line_total = round(price * item.quantity, 2)
            subtotal += line_total
            normalized_items.append(
                {
                    "product_id": item.product_id,
                    "name": product["name"],
                    "quantity": item.quantity,
                    "unit_price": price,
                    "line_total": line_total,
                }
            )

        subtotal = round(subtotal, 2)
        delivery_fee = 0.0
        total = round(subtotal + delivery_fee, 2)
        created_at = datetime.now().isoformat(timespec="seconds")

        cursor = conn.execute(
            """
            INSERT INTO pedidos_online (
                codigo, criado_em, status, cliente_nome, telefone, cep, endereco, numero,
                complemento, bairro, cidade, observacoes, forma_pagamento, subtotal,
                taxa_entrega, total, itens_json, origem
            ) VALUES (NULL, ?, 'NOVO', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'LOJA_PWA')
            """,
            (
                created_at,
                order.customer.name.strip(),
                order.customer.phone.strip(),
                order.customer.cep.strip(),
                order.customer.address.strip(),
                order.customer.number.strip(),
                order.customer.complement.strip(),
                order.customer.neighborhood.strip(),
                order.customer.city.strip(),
                order.customer.notes.strip(),
                order.payment_method,
                subtotal,
                delivery_fee,
                total,
                json.dumps(normalized_items, ensure_ascii=False),
            ),
        )
        order_id = int(cursor.lastrowid)
        code = f"KF-WEB-{datetime.now():%Y}-{order_id:06d}"
        conn.execute("UPDATE pedidos_online SET codigo=? WHERE id=?", (code, order_id))
        conn.commit()

    return {
        "ok": True,
        "order_id": order_id,
        "code": code,
        "status": "NOVO",
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
    }


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(STATIC_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")


@app.get("/logo.jpg")
def logo():
    if LOGO_PATH.exists():
        return FileResponse(LOGO_PATH, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Logo não encontrado")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
