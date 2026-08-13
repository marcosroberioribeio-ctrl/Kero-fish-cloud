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

# Tela de InÃ­cio
if opcao == "In\u00edcio":
    st.title("Kero Fish - Peixe e Camar\u00e3o")
    st.write("Sistema de Gest\u00e3o Integrada")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do M\u00eas", "R$ 0,00")
    col2.metric("Estoque Atual", "0 kg")
    col3.metric("Clientes Ativos", "0")

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("Cadastro Geral")
    tipo = st.selectbox("O que deseja cadastrar?", ["Cliente", "Produto (Peixe / Camar\u00e3o)", "Fornecedor"])
    
    nome = st.text_input("Nome / Descri\u00e7\u00e3o")
    telefone = st.text_input("Telefone / Contato")
    
    if st.button("Salvar Cadastro"):
        st.success(f"{tipo} '{nome}' cadastrado com sucesso!")
