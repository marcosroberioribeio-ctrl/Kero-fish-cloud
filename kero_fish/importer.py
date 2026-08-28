from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import hashlib
import pandas as pd
from .db import connect, backup_db
from .utils import norm_text, norm_key, to_float, to_iso_date

@dataclass
class ImportReport:
    source:str
    inserted:dict=field(default_factory=lambda:{k:0 for k in ['produtos','clientes','fornecedores','compras','vendas','despesas','financeiro','contas_pagar','contas_receber','entregas']})
    skipped:int=0
    warnings:list=field(default_factory=list)
    def total_inserted(self): return sum(self.inserted.values())

def _read(xls,name):
    hit=next((s for s in xls.sheet_names if norm_key(s)==norm_key(name)),None)
    if not hit:return pd.DataFrame()
    d=pd.read_excel(xls,sheet_name=hit).dropna(axis=1,how='all'); d.columns=[norm_text(c) for c in d.columns]; return d

def _get(row,df,*names):
    m={norm_key(c):c for c in df.columns}
    for n in names:
        if norm_key(n) in m:return row.get(m[norm_key(n)],'')
    return ''

def _key(*parts): return hashlib.sha1('|'.join(norm_text(x) for x in parts).encode()).hexdigest()
def _cat(p):
    k=norm_key(p)
    if 'camarao' in k:return 'Camarão'
    if any(x in k for x in ['peixe','tilapia','salmao','sardinha','atum','pargo']):return 'Peixe'
    return 'Outros'

def import_excel(path,create_backup=True):
    path=Path(path); r=ImportReport(path.name)
    if create_backup: backup_db('pre_import')
    x=pd.ExcelFile(path); vendas=_read(x,'Vendas'); compras=_read(x,'Compras'); estoque=_read(x,'Estoque'); fornecedores=_read(x,'Fornecedores'); despesas=_read(x,'Despesas'); cp=_read(x,'Contas_Pagar'); cr=_read(x,'Contas_Receber'); entregas=_read(x,'Entregas')
    products=set()
    for d in [vendas,compras,estoque]:
        for _,row in d.iterrows():
            p=norm_text(_get(row,d,'Produto'))
            if p:products.add(p)
    costs={};prices={};supp={}
    for _,row in compras.iterrows():
        p=norm_text(_get(row,compras,'Produto')); c=to_float(_get(row,compras,'Custo Unitário','Custo Unitario','Preço Unitário')) ; f=norm_text(_get(row,compras,'Fornecedor'))
        if p and c:costs[norm_key(p)]=c
        if p and f:supp[norm_key(p)]=f
    for _,row in vendas.iterrows():
        p=norm_text(_get(row,vendas,'Produto')); unit=to_float(_get(row,vendas,'Valor Unitário','Valor Unitario','Preço Unitário'))
        if p and unit:prices[norm_key(p)]=unit
    with connect() as c:
        for p in sorted(products,key=norm_key):
            ex=c.execute('SELECT id FROM produtos WHERE lower(trim(nome))=lower(trim(?))',(p,)).fetchone(); k=norm_key(p)
            if ex:c.execute('UPDATE produtos SET categoria=?,custo_medio=?,preco_venda=?,fornecedor_padrao=? WHERE id=?',(_cat(p),costs.get(k,0),prices.get(k,0),supp.get(k,''),ex['id']))
            else:c.execute('INSERT INTO produtos(nome,categoria,unidade,custo_medio,preco_venda,ativo,fornecedor_padrao) VALUES (?,?,?,?,?,1,?)',(p,_cat(p),'kg',costs.get(k,0),prices.get(k,0),supp.get(k,'')));r.inserted['produtos']+=1
        clients=sorted({norm_text(_get(row,vendas,'Cliente')) for _,row in vendas.iterrows() if norm_text(_get(row,vendas,'Cliente'))},key=norm_key)
        for n in clients:
            if not c.execute('SELECT 1 FROM clientes WHERE lower(nome)=lower(?)',(n,)).fetchone():c.execute('INSERT INTO clientes(nome,data_cad,ativo) VALUES (?,?,1)',(n,datetime.now().strftime('%Y-%m-%d')));r.inserted['clientes']+=1
        snames={norm_text(_get(row,compras,'Fornecedor')) for _,row in compras.iterrows() if norm_text(_get(row,compras,'Fornecedor'))}
        snames|={norm_text(_get(row,fornecedores,'Fornecedor','Nome')) for _,row in fornecedores.iterrows() if norm_text(_get(row,fornecedores,'Fornecedor','Nome'))}
        for n in sorted(snames,key=norm_key):
            if not c.execute('SELECT 1 FROM fornecedores WHERE lower(fornecedor)=lower(?)',(n,)).fetchone():c.execute('INSERT INTO fornecedores(fornecedor,ativo) VALUES (?,1)',(n,));r.inserted['fornecedores']+=1
        for i,row in compras.iterrows():
            f=norm_text(_get(row,compras,'Fornecedor'));p=norm_text(_get(row,compras,'Produto'));q=to_float(_get(row,compras,'Quantidade','Quantidade Comprada (KG)'));u=to_float(_get(row,compras,'Custo Unitário','Custo Unitario','Preço Unitário'));d=to_iso_date(_get(row,compras,'Data'));total=to_float(_get(row,compras,'Valor Total','Total')) or q*u;sk=_key('C',i,d,f,p,q,u,total)
            if not p or q<=0:continue
            if c.execute('SELECT 1 FROM compras WHERE source_key=?',(sk,)).fetchone():r.skipped+=1;continue
            c.execute('INSERT INTO compras(fornecedor,produto,qtd,preco_kg,valor_total,data_compra,forma_pagamento,status_pagamento,source_key,observacoes) VALUES (?,?,?,?,?,?,?,"Pago",?,?)',(f,p,q,u,total,d,norm_text(_get(row,compras,'Forma Pagamento','Pagamento')) or 'Não informado',sk,'Importado da planilha completa'));r.inserted['compras']+=1
        for i,row in vendas.iterrows():
            cli=norm_text(_get(row,vendas,'Cliente'));p=norm_text(_get(row,vendas,'Produto'));q=to_float(_get(row,vendas,'Quantidade'));u=to_float(_get(row,vendas,'Valor Unitário','Valor Unitario','Preço Unitário'));gross=to_float(_get(row,vendas,'Valor Venda','Total')) or q*u;liq=to_float(_get(row,vendas,'Valor Líquido','Valor Liquido'));total=liq if liq>0 else gross;d=to_iso_date(_get(row,vendas,'Data'));forma=norm_text(_get(row,vendas,'Forma Pagamento','Pagamento')) or 'Não informado';sk=_key('V',i,d,cli,p,q,u,total)
            if not p or q<=0:continue
            if c.execute('SELECT 1 FROM vendas WHERE source_key=?',(sk,)).fetchone():r.skipped+=1;continue
            pedido=f'KF-HIST-{i+1:06d}';cur=c.execute('INSERT INTO vendas(pedido,cliente,produto,qtd_kg,preco_kg,valor_total,data_venda,forma_pagamento,status_pagamento,valor_recebido,source_key,status_pedido,observacoes) VALUES (?,?,?,?,?,?,?,?,"Pago",?,?,?,?)',(pedido,cli,p,q,u,total,d,forma,total,sk,norm_text(_get(row,vendas,'Status Entrega','Status')),'Importado da planilha completa'));r.inserted['vendas']+=1;c.execute('INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id) VALUES (?,?,?,?,?,?,?)',(d,f'Venda {pedido}','Entrada',total,forma,'venda',cur.lastrowid));r.inserted['financeiro']+=1
        for i,row in despesas.iterrows():
            cat=norm_text(_get(row,despesas,'Categoria'));desc=norm_text(_get(row,despesas,'Descrição','Descricao'));v=to_float(_get(row,despesas,'Valor'));d=to_iso_date(_get(row,despesas,'Data'));pg=norm_text(_get(row,despesas,'Forma Pagamento','Pagamento')) or 'Não informado';sk=_key('D',i,d,cat,desc,v)
            if not desc or v<=0 or norm_key(cat) in {'produto','produtos'}:continue
            if c.execute("SELECT 1 FROM audit_log WHERE entity_type='despesa_import' AND detail=?",(sk,)).fetchone():r.skipped+=1;continue
            cur=c.execute("INSERT INTO despesas(data_desp,categoria,descricao,valor,pagamento,status,vencimento,observacoes) VALUES (?,?,?,?,?,'Pago',?,?)",(d,cat,desc,v,pg,d,'Importado da planilha completa'));r.inserted['despesas']+=1;c.execute('INSERT INTO financeiro(data_mov,descricao,tipo,valor,forma_pagamento,origem_tipo,origem_id) VALUES (?,?,?,?,?,?,?)',(d,desc,'Saída',v,pg,'despesa',cur.lastrowid));r.inserted['financeiro']+=1;c.execute("INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",(datetime.now().isoformat(),'IMPORT','despesa_import',cur.lastrowid,sk))
        for i,row in cp.iterrows():
            f=norm_text(_get(row,cp,'Fornecedor'));desc=norm_text(_get(row,cp,'Descrição','Descricao'));v=to_float(_get(row,cp,'Valor'));ven=to_iso_date(_get(row,cp,'Vencimento'));st=norm_text(_get(row,cp,'Status'));sk=_key('CP',i,f,desc,v,ven)
            if not desc or v<=0:continue
            if c.execute("SELECT 1 FROM audit_log WHERE entity_type='cp_import' AND detail=?",(sk,)).fetchone():r.skipped+=1;continue
            paid=norm_key(st) in {'pg','pago','quitado'};cur=c.execute('INSERT INTO contas_pagar(fornecedor,descricao,valor,valor_pago,vencimento,status,origem_tipo) VALUES (?,?,?,?,?,?,?)',(f,desc,v,v if paid else 0,ven,'Pago' if paid else 'Pendente','planilha'));r.inserted['contas_pagar']+=1;c.execute("INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",(datetime.now().isoformat(),'IMPORT','cp_import',cur.lastrowid,sk))
        for i,row in cr.iterrows():
            cli=norm_text(_get(row,cr,'Cliente'));desc=norm_text(_get(row,cr,'Descrição','Descricao'));v=to_float(_get(row,cr,'Valor'));ven=to_iso_date(_get(row,cr,'Vencimento'));sk=_key('CR',i,cli,desc,v,ven)
            if not desc or v<=0:continue
            if c.execute("SELECT 1 FROM audit_log WHERE entity_type='cr_import' AND detail=?",(sk,)).fetchone():r.skipped+=1;continue
            cur=c.execute("INSERT INTO contas_receber(cliente,descricao,valor,valor_recebido,vencimento,status,origem_tipo) VALUES (?,?,?,0,?,'Pendente','planilha')",(cli,desc,v,ven));r.inserted['contas_receber']+=1;c.execute("INSERT INTO audit_log(event_time,action,entity_type,entity_id,detail) VALUES (?,?,?,?,?)",(datetime.now().isoformat(),'IMPORT','cr_import',cur.lastrowid,sk))
        c.execute("INSERT OR REPLACE INTO app_meta(key,value) VALUES('last_import_file',?)",(path.name,));c.execute("INSERT OR REPLACE INTO app_meta(key,value) VALUES('last_import_at',?)",(datetime.now().isoformat(timespec='seconds'),))
    return r
