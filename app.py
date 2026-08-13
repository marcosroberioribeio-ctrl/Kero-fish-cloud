import streamlit as st

st.set_page_config(page_title="Kero Fish - Peixe e Camar\u00e3o", layout="wide")

# Exibe a foto oficial do logo
st.sidebar.image("Screenshot_20260813_084749_WhatsApp.jpg", use_container_width=True)

opcao = st.sidebar.radio(
    "Navega\u00e7\u00e3o",
    ["In\u00edcio", "Cadastro", "Estoque / Produ\u00e7\u00e3o", "Vendas / Devolu\u00e7\u00e3o", "Financeiro"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Contatos:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("**Instagram:** @kerofish")

# Estrutura de dados na sessao
if "clientes" not in st.session_state:
    st.session_state.clientes = []
if "produtos" not in st.session_state:
    st.session_state.produtos = [
        {"nome": "Camar\u00e3o P", "categoria": "Camar\u00e3o"},
        {"nome": "Camar\u00e3o G", "categoria": "Camar\u00e3o"},
        {"nome": "Camar\u00e3o GG", "categoria": "Camar\u00e3o"},
        {"nome": "Pargo", "categoria": "Peixe"},
        {"nome": "Salm\u00e3o", "categoria": "Peixe"},
        {"nome": "Til\u00e1pia", "categoria": "Peixe"},
        {"nome": "Atum", "categoria": "Peixe"},
        {"nome": "Sardinha", "categoria": "Peixe"},
        {"nome": "Castanha de Caju", "categoria": "Produtos Regionais"},
        {"nome": "Caju\u00edna", "categoria": "Produtos Regionais"},
        {"nome": "Temperos", "categoria": "Produtos Regionais"},
        {"nome": "Manteiga da Terra", "categoria": "Produtos Regionais"},
        {"nome": "Queijo", "categoria": "Produtos Regionais"},
    ]
if "estoque" not in st.session_state:
    st.session_state.estoque = []
if "vendas" not in st.session_state:
    st.session_state.vendas = []

# Tela de InÃ­cio
if opcao == "In\u00edcio":
    st.title("Kero Fish - Peixe, Camar\u00e3o e Regionais")
    st.caption("Sistema de Gest\u00e3o Integrada")
    st.markdown("---")
    
    total_vendas = sum(v.get("valor_total", 0.0) for v in st.session_state.vendas)
    total_kg_vendidos = sum(v.get("qtd", 0.0) for v in st.session_state.vendas)
    total_est = sum(item.get("quantidade", 0.0) for item in st.session_state.estoque) - total_kg_vendidos
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do M\u00eas", f"R$ {total_vendas:,.2f}")
    col2.metric("Estoque Geral", f"{max(total_est, 0.0):.1f} un/kg")
    col3.metric("Clientes Cadastrados", len(st.session_state.clientes))

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("Cadastro Geral")
    st.markdown("---")
    
    tipo = st.selectbox("Selecione o tipo de cadastro:", ["Cliente", "Novo Produto", "Fornecedor"])
    
    with st.form("form_cadastro", clear_on_submit=True):
        if tipo == "Cliente":
            nome = st.text_input("Nome / Raz\u00e3o Social")
            telefone = st.text_input("Telefone / WhatsApp")
            cidade = st.text_input("Cidade / Bairro")
            submitted = st.form_submit_button("Cadastrar Cliente")
            if submitted and nome:
                st.session_state.clientes.append({"nome": nome, "telefone": telefone, "cidade": cidade})
                st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                
        elif tipo == "Novo Produto":
            nome_prod = st.text_input("Nome do Produto (ex: Camar\u00e3o M, Queijo Coalho)")
            categoria = st.selectbox("Categoria", ["Camar\u00e3o", "Peixe", "Produtos Regionais", "Outros"])
            submitted = st.form_submit_button("Cadastrar Produto")
            if submitted and nome_prod:
                st.session_state.produtos.append({"nome": nome_prod, "categoria": categoria})
                st.success(f"Produto '{nome_prod}' cadastrado com sucesso!")
                
        elif tipo == "Fornecedor":
            nome_forn = st.text_input("Nome do Fornecedor / Produtor")
            contato = st.text_input("Contato / Telefone")
            submitted = st.form_submit_button("Cadastrar Fornecedor")
            if submitted and nome_forn:
                st.success(f"Fornecedor '{nome_forn}' cadastrado com sucesso!")

# Tela de Estoque / ProduÃ§Ã£o
elif opcao == "Estoque / Produ\u00e7\u00e3o":
    st.title("Controle de Estoque")
    st.markdown("---")
    
    lista_produtos = [p["nome"] for p in st.session_state.produtos]
    
    with st.form("form_estoque", clear_on_submit=True):
        col_prod, col_tipo, col_qtd = st.columns(3)
        prod_sel = col_prod.selectbox("Produto", lista_produtos)
        mov_tipo = col_tipo.selectbox("Tipo de Movimenta\u00e7\u00e3o", ["Entrada (Compra/Produ\u00e7\u00e3o)", "Sa\u00edda (Perda/Ajuste)"])
        qtd = col_qtd.number_input("Quantidade (kg ou Unidades)", min_value=0.1, step=0.5)
        
        submitted_est = st.form_submit_button("Registrar no Estoque")
        if submitted_est:
            fator = 1 if "Entrada" in mov_tipo else -1
            st.session_state.estoque.append({"produto": prod_sel, "quantidade": qtd * fator})
            st.success(f"Estoque de '{prod_sel}' atualizado em {qtd}!")

    if st.session_state.estoque:
        st.markdown("---")
        st.subheader("Hist\u00f3rico de Entradas/Ajustes de Estoque")
        st.dataframe(st.session_state.estoque)

# Tela de Vendas e DevoluÃ§Ã£o
elif opcao == "Vendas / Devolu\u00e7\u00e3o":
    st.title("Vendas e Devolu\u00e7\u00f5es")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["ðŸ›’ Registrar Venda", "ðŸ”„ Registrar Devolu\u00e7\u00e3o / Estorno"])
    
    lista_cli = [c["nome"] for c in st.session_state.clientes] if st.session_state.clientes else ["Cliente Avulso"]
    lista_prod = [p["nome"] for p in st.session_state.produtos]
    
    with tab1:
        with st.form("form_vendas", clear_on_submit=True):
            col_c, col_p = st.columns(2)
            cli_sel = col_c.selectbox("Cliente", lista_cli)
            prod_sel = col_p.selectbox("Produto Vendido", lista_prod)
            
            col_k, col_v = st.columns(2)
            qtd_venda = col_k.number_input("Quantidade Vendida (kg ou Unidade)", min_value=0.1, step=0.5)
            preco_unit = col_v.number_input("Pre\u00e7o por kg/Unidade (R$)", min_value=0.0, step=1.0)
            
            sub_venda = st.form_submit_button("Finalizar Venda")
            if sub_venda:
                v_total = qtd_venda * preco_unit
                st.session_state.vendas.append({
                    "tipo": "Venda",
                    "cliente": cli_sel,
                    "produto": prod_sel,
                    "qtd": qtd_venda,
                    "valor_total": v_total
                })
                st.success(f"Venda de R$ {v_total:,.2f} para {cli_sel} registrada com sucesso!")

    with tab2:
        st.write("Registre devolu\u00e7\u00f5es de produtos. O valor ser\u00e1 abatido do faturamento e a quantidade retornar\u00e1 ao estoque.")
        with st.form("form_devolucao", clear_on_submit=True):
            col_dc, col_dp = st.columns(2)
            cli_dev = col_dc.selectbox("Cliente que est\u00e1 devolvendo", lista_cli)
            prod_dev = col_dp.selectbox("Produto Devolvido", lista_prod)
            
            col_dk, col_dv = st.columns(2)
            qtd_dev = col_dk.number_input("Quantidade Devolvida", min_value=0.1, step=0.5)
            valor_dev = col_dv.number_input("Valor a Estornar/Devolver (R$)", min_value=0.0, step=1.0)
            
            sub_dev = st.form_submit_button("Confirmar Devolu\u00e7\u00e3o")
            if sub_dev:
                st.session_state.vendas.append({
                    "tipo": "Devolu\u00e7\u00e3o",
                    "cliente": cli_dev,
                    "produto": prod_dev,
                    "qtd": -qtd_dev,
                    "valor_total": -valor_dev
                })
                st.warning(f"Devolu\u00e7\u00e3o de R$ {valor_dev:,.2f} do cliente {cli_dev} registrada com sucesso!")

    if st.session_state.vendas:
        st.markdown("---")
        st.subheader("Hist\u00f3rico de Movimenta\u00e7\u00f5es Comerciais")
        st.dataframe(st.session_state.vendas)

# Tela de Financeiro
elif opcao == "Financeiro":
    st.title("Painel Financeiro")
    st.markdown("---")
    
    total_faturado = sum(v.get("valor_total", 0.0) for v in st.session_state.vendas)
    qtd_vendas = len([v for v in st.session_state.vendas if v.get("tipo") == "Venda"])
    
    c1, c2 = st.columns(2)
    c1.metric("Faturamento L\u00edquido (Vendas - Devolu\u00e7\u00f5es)", f"R$ {total_faturado:,.2f}")
    c2.metric("Total de Vendas Realizadas", qtd_vendas)
