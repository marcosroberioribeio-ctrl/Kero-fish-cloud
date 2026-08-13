import streamlit as st

st.set_page_config(page_title="Kero Fish - Peixe e Camar\u00e3o", layout="wide")

# Exibe a foto oficial do logo
st.sidebar.image("Screenshot_20260813_084749_WhatsApp.jpg", use_container_width=True)

opcao = st.sidebar.radio(
    "Navega\u00e7\u00e3o",
    ["In\u00edcio", "Cadastro", "Estoque / Produ\u00e7\u00e3o", "Vendas", "Financeiro"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Contatos:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("**Instagram:** @kerofish")

# Initializing Session States for persistence within current session
if "clientes" not in st.session_state:
    st.session_state.clientes = []
if "produtos" not in st.session_state:
    st.session_state.produtos = []
if "estoque" not in st.session_state:
    st.session_state.estoque = []

# Tela de InÃ­cio
if opcao == "In\u00edcio":
    st.title("Kero Fish - Peixe e Camar\u00e3o")
    st.caption("Sistema de Gest\u00e3o Integrada")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do M\u00eas", "R$ 0,00")
    
    total_kg = sum(item.get("quantidade_kg", 0) for item in st.session_state.estoque)
    col2.metric("Estoque Atual", f"{total_kg:.1f} kg")
    col3.metric("Clientes Cadastrados", len(st.session_state.clientes))

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("Cadastro Geral")
    st.markdown("---")
    
    tipo = st.selectbox("Selecione o tipo de cadastro:", ["Cliente", "Produto (Peixe / Camar\u00e3o)", "Fornecedor"])
    
    with st.form("form_cadastro", clear_on_submit=True):
        if tipo == "Cliente":
            nome = st.text_input("Nome / Raz\u00e3o Social")
            telefone = st.text_input("Telefone / WhatsApp")
            cidade = st.text_input("Cidade / Bairro")
            submitted = st.form_submit_button("Cadastrar Cliente")
            if submitted and nome:
                st.session_state.clientes.append({"nome": nome, "telefone": telefone, "cidade": cidade})
                st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                
        elif tipo == "Produto (Peixe / Camar\u00e3o)":
            nome_prod = st.text_input("Nome do Produto (ex: Camar\u00e3o Vanei, Til\u00e1pia Inteira)")
            categoria = st.selectbox("Categoria", ["Camar\u00e3o", "Peixe", "Outros"])
            preco = st.number_input("Pre\u00e7o Sugerido por kg (R$)", min_value=0.0, step=1.0)
            submitted = st.form_submit_button("Cadastrar Produto")
            if submitted and nome_prod:
                st.session_state.produtos.append({"nome": nome_prod, "categoria": categoria, "preco": preco})
                st.success(f"Produto '{nome_prod}' cadastrado com sucesso!")
                
        elif tipo == "Fornecedor":
            nome_forn = st.text_input("Nome do Fornecedor / Fazenda")
            contato = st.text_input("Contato / Telefone")
            submitted = st.form_submit_button("Cadastrar Fornecedor")
            if submitted and nome_forn:
                st.success(f"Fornecedor '{nome_forn}' cadastrado com sucesso!")

# Tela de Estoque / ProduÃ§Ã£o
elif opcao == "Estoque / Produ\u00e7\u00e3o":
    st.title("Controle de Estoque e Produ\u00e7\u00e3o")
    st.markdown("---")
    
    st.subheader("Lan\u00e7ar Entrada / Sa\u00edda de Estoque")
    
    lista_produtos = [p["nome"] for p in st.session_state.produtos] if st.session_state.produtos else ["Camar\u00e3o Fresco", "Peixe Inteiro", "Fil\u00e9 de Peixe"]
    
    with st.form("form_estoque", clear_on_submit=True):
        col_prod, col_tipo, col_qtd = st.columns(3)
        prod_sel = col_prod.selectbox("Produto", lista_produtos)
        mov_tipo = col_tipo.selectbox("Tipo de Movimenta\u00e7\u00e3o", ["Entrada (Compra/Produ\u00e7\u00e3o)", "Sa\u00edda (Perda/Ajuste)"])
        qtd_kg = col_qtd.number_input("Quantidade (kg)", min_value=0.1, step=0.5)
        
        submitted_est = st.form_submit_button("Registrar Movimenta\u00e7\u00e3o")
        if submitted_est:
            fator = 1 if "Entrada" in mov_tipo else -1
            st.session_state.estoque.append({"produto": prod_sel, "quantidade_kg": qtd_kg * fator})
            st.success(f"Movimenta\u00e7\u00e3o de {qtd_kg} kg de '{prod_sel}' registrada!")

    if st.session_state.estoque:
        st.markdown("---")
        st.subheader("Hist\u00f3rico do Estoque Atual")
        st.dataframe(st.session_state.estoque)

# Outras telas
else:
    st.title(f"{opcao}")
    st.info("M\u00f3dulo em desenvolvimento. Em breve novos recursos aqui!")
