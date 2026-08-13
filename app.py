import streamlit as st

st.set_page_config(page_title="Kero Fish - Peixe e CamarÃ£o", layout="wide")

# Exibe a foto oficial do logo
st.sidebar.image("Screenshot_20260813_084749_WhatsApp.jpg", use_container_width=True)

opcao = st.sidebar.radio(
    "NavegaÃ§Ã£o",
    ["InÃ­cio", "Cadastro", "Estoque / ProduÃ§Ã£o", "Vendas", "Financeiro"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Contatos:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("**Instagram:** @kerofish")

# Tela de InÃ­cio
if opcao == "InÃ­cio":
    st.title("Kero Fish - Peixe e CamarÃ£o")
    st.write("Sistema de GestÃ£o Integrada")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do MÃªs", "R$ 0,00")
    col2.metric("Estoque Atual", "0 kg")
    col3.metric("Clientes Ativos", "0")

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("Cadastro Geral")
    tipo = st.selectbox("O que deseja cadastrar?", ["Cliente", "Produto (Peixe / CamarÃ£o)", "Fornecedor"])
    
    nome = st.text_input("Nome / DescriÃ§Ã£o")
    telefone = st.text_input("Telefone / Contato")
    
    if st.button("Salvar Cadastro"):
        st.success(f"{tipo} '{nome}' cadastrado com sucesso!")
