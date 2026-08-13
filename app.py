import streamlit as st

st.set_page_config(page_title="Kero Fish - Peixe e Camarão", page_icon="🐟", layout="wide")

# Menu Lateral
st.sidebar.title("🐟 KERO FISH")
st.sidebar.caption("• PEIXE E CAMARÃO •")

opcao = st.sidebar.radio(
    "Navegação",
    ["Início", "Cadastro", "Estoque / Produção", "Vendas", "Financeiro"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("📞 **Contatos:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("📷 **Instagram:** @kerofish")

# Tela de Início
if opcao == "Início":
    st.title("📊 Kero Fish - Peixe e Camarão")
    st.write("Sistema de Gestão Integrada")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do Mês", "R$ 0,00")
    col2.metric("Estoque Atual", "0 kg")
    col3.metric("Clientes Ativos", "0")

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("📝 Cadastro Geral")
    tipo = st.selectbox("O que deseja cadastrar?", ["Cliente", "Produto (Peixe / Camarão)", "Fornecedor"])
    
    nome = st.text_input("Nome / Descrição")
    telefone = st.text_input("Telefone / Contato")
    
    if st.button("Salvar Cadastro"):
        st.success(f"{tipo} '{nome}' cadastrado com sucesso!")

# Outras telas
else:
    st.title(f"📌 {opcao}")
    st.info("Módulo em desenvolvimento. Em breve novos recursos aqui!")
