import streamlit as st

st.set_page_config(page_title="Kero Fish", page_icon="🐟", layout="wide")

# Menu Lateral
st.sidebar.title("🐟 Kero Fish")
opcao = st.sidebar.radio(
    "Navegação",
    ["Início", "Cadastro", "Estoque / Produção", "Vendas", "Financeiro"]
)

# Tela de Início
if opcao == "Início":
    st.title("📊 Painel Geral - Kero Fish")
    st.write("Bem-vindo ao sistema de gestão!")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do Mês", "R$ 0,00")
    col2.metric("Estoque Atual", "0 kg")
    col3.metric("Clientes Ativos", "0")

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("📝 Cadastro Geral")
    tipo = st.selectbox("O que deseja cadastrar?", ["Cliente", "Produto / Peixe", "Fornecedor"])
    
    nome = st.text_input("Nome / Descrição")
    telefone = st.text_input("Telefone / Contato")
    
    if st.button("Salvar Cadastro"):
        st.success(f"{tipo} '{nome}' cadastrado com sucesso! (Exemplo)")

# Outras telas
else:
    st.title(f"📌 {opcao}")
    st.info("Módulo em desenvolvimento. Em breve novos recursos aqui!")
