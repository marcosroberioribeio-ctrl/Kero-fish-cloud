from __future__ import annotations
from datetime import datetime
from typing import Iterable
import pandas as pd
from .db import connect

def query_df(sql: str, params: Iterable = ()) -> pd.DataFrame:
    with connect() as conn: return pd.read_sql_query(sql, conn, params=tuple(params))
def scalar(sql: str, params: Iterable = (), default=0):
    with connect() as conn:
        row=conn.execute(sql,tuple(params)).fetchone(); return row[0] if row and row[0] is not None else default

def stock_df():
    return query_df("""SELECT p.nome AS Produto,p.categoria AS Categoria,p.unidade AS Unidade,ROUND(COALESCE(c.compras,0),3) AS Compras,ROUND(COALESCE(v.vendas,0),3) AS Vendas,ROUND(COALESCE(a.ajuste_entrada,0)-COALESCE(a.ajuste_saida,0),3) AS Ajustes,ROUND(COALESCE(c.compras,0)-COALESCE(v.vendas,0)+COALESCE(a.ajuste_entrada,0)-COALESCE(a.ajuste_saida,0),3) AS Estoque,p.estoque_minimo AS Minimo,CASE WHEN COALESCE(c.compras,0)-COALESCE(v.vendas,0)+COALESCE(a.ajuste_entrada,0)-COALESCE(a.ajuste_saida,0)<0 THEN 'NEGATIVO' WHEN COALESCE(c.compras,0)-COALESCE(v.vendas,0)+COALESCE(a.ajuste_entrada,0)-COALESCE(a.ajuste_saida,0)<=p.estoque_minimo THEN 'BAIXO' ELSE 'OK' END AS Situacao,p.custo_medio AS Custo_medio,p.preco_venda AS Preco_venda FROM produtos p LEFT JOIN (SELECT produto,SUM(qtd) compras FROM compras GROUP BY produto)c ON c.produto=p.nome LEFT JOIN (SELECT produto,SUM(qtd_kg) vendas FROM vendas GROUP BY produto)v ON v.produto=p.nome LEFT JOIN (SELECT produto,SUM(CASE WHEN origem_tipo='manual' AND tipo='Ajuste Entrada' THEN quantidade ELSE 0 END) ajuste_entrada,SUM(CASE WHEN origem_tipo='manual' AND tipo IN ('Ajuste Saída','Perda') THEN quantidade ELSE 0 END) ajuste_saida FROM movimentos_estoque GROUP BY produto)a ON a.produto=p.nome WHERE p.ativo=1 ORDER BY p.nome""")

def dashboard_metrics():
    entradas=float(scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Entrada'")); saidas=float(scalar("SELECT COALESCE(SUM(valor),0) FROM financeiro WHERE tipo='Saída'")); receber=float(scalar("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_recebido,0),0)),0) FROM contas_receber WHERE status IN ('Pendente','Parcial')")); pagar=float(scalar("SELECT COALESCE(SUM(MAX(valor-COALESCE(valor_pago,0),0)),0) FROM contas_pagar WHERE status IN ('Pendente','Parcial')")); vendas=float(scalar("SELECT COALESCE(SUM(valor_total),0) FROM vendas")); compras=float(scalar("SELECT COALESCE(SUM(valor_total),0) FROM compras")); return {"entradas":entradas,"saidas":saidas,"saldo":entradas-saidas,"receber":receber,"pagar":pagar,"vendas":vendas,"compras":compras,"qtd_vendas":int(scalar("SELECT COUNT(*) FROM vendas")),"qtd_compras":int(scalar("SELECT COUNT(*) FROM compras"))}

def register_sale(cliente,produto,qtd,preco,desconto,data_venda,forma,recebido,vencimento,observacoes):
    total=max(0.0,qtd*preco-desconto); recebido=min(max(recebido,0.0),total); status="Pago" if total>0 and recebido>=total else ("Parcial" if recebido>0 else "Pendente")
    with connect() as conn:
        last=conn.execute("SELECT COALESCE(MAX(id),0) FROM vendas").fetchone()[0]; pedido=f"KF-{datetime.now().year}-{int(last)+1:06d}"; cur=conn.execute("INSERT INTO vendas(pedido,cliente,produto,qtd_kg,preco_kg,desconto,valor_total,data_venda,forma_pagamento,status_pagamento,valor_recebido,vencimento,observacoes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(pedido,cliente,produto,qtd,preco,desconto,total,data_venda,forma,status,recebido,vencimento,observacoes)); vid=cur.lastrowid
        if recebido>0: conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id) VALUES (?,?,?,?,?,?,?)",(data_venda,f"Venda {pedido} - recebimento","Entrada",recebido,forma,"venda",vid))
        saldo=total-recebido
        if saldo>0: conn.execute("INSERT INTO contas_receber(cliente,descricao,valor,valor_recebido,vencimento,status,origem_tipo,origem_id) VALUES (?,?,?,?,?,?,?,?)",(cliente,f"Venda {pedido}",total,recebido,vencimento or data_venda,status,"venda",vid))
        conn.execute("INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",(datetime.now().isoformat(timespec='seconds'),"CREATE","venda",vid,pedido)); return vid

def register_purchase(fornecedor,produto,qtd,preco,data_compra,lote,validade,forma,status,vencimento,observacoes):
    total=qtd*preco
    with connect() as conn:
        cur=conn.execute("INSERT INTO compras(fornecedor,produto,qtd,preco_kg,valor_total,data_compra,lote,validade,forma_pagamento,status_pagamento,vencimento,observacoes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(fornecedor,produto,qtd,preco,total,data_compra,lote,validade,forma,status,vencimento,observacoes)); cid=cur.lastrowid
        if status=="Pago": conn.execute("INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id) VALUES (?,?,?,?,?,?,?)",(data_compra,f"Compra #{cid}: {produto}","Saída",total,forma,"compra",cid))
        else: conn.execute("INSERT INTO contas_pagar(fornecedor,descricao,valor,valor_pago,vencimento,status,origem_tipo,origem_id) VALUES (?,?,?,?,?,?,?,?)",(fornecedor,f"Compra #{cid}: {produto}",total,0,vencimento or data_compra,"Pendente","compra",cid))
        conn.execute("INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",(datetime.now().isoformat(timespec='seconds'),"CREATE","compra",cid,produto)); return cid

def save_grid(table,original,edited,editable):
    if original.empty or edited.empty:return 0
    orig=original.set_index("id",drop=False); changed=0; allowed={"clientes","fornecedores","produtos","compras","vendas","despesas","contas_pagar","contas_receber","entregas"}; numeric={"qtd","qtd_kg","preco_kg","valor_total","desconto","valor_recebido","valor","valor_pago","taxa_entrega","estoque_minimo","preco_venda","custo_medio"}
    if table not in allowed: raise ValueError("Tabela não permitida")
    with connect() as conn:
        for _,row in edited.iterrows():
            rid=int(row["id"])
            if rid not in orig.index:continue
            old=orig.loc[rid]
            if not any(str(row.get(c,""))!=str(old.get(c,"")) for c in editable):continue
            sets=[];params=[]
            for c in editable:
                v=row.get(c,""); v="" if pd.isna(v) else v; v=float(v or 0) if c in numeric else v; sets.append(f"{c}=?");params.append(v)
            params.append(rid);conn.execute(f"UPDATE {table} SET {', '.join(sets)} WHERE id=?",params);changed+=1;conn.execute("INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",(datetime.now().isoformat(timespec='seconds'),"UPDATE",table,rid,"edição direta no grid"))
    return changed
