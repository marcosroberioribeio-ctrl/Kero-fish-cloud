import streamlit as st

st.set_page_config(page_title="Kero Fish - Peixe e CamarÃ£o", page_icon="ðŸŸ", layout="wide")

# Exibe a foto oficial do logo
st.sidebar.image("Screenshot_20260813_084749_WhatsApp.jpg", use_container_width=True)

st.sidebar.caption("â€¢ PEIXE E CAMARÃƒO â€¢")

opcao = st.sidebar.radio(
    "NavegaÃ§Ã£o",
    ["InÃ­cio", "Cadastro", "Estoque / ProduÃ§Ã£o", "Vendas", "Financeiro"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("ðŸ“ž **Contatos:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("ðŸ“· **Instagram:** @kerofish")

# Tela de InÃ­cio
if opcao == "InÃ­cio":
    st.title("ðŸ“Š Kero Fish - Peixe e CamarÃ£o")
    st.write("Sistema de GestÃ£o Integrada")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do MÃªs", "R$ 0,00")
    col2.metric("Estoque Atual", "0 kg")
    col3.metric("Clientes Ativos", "0")

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("ðŸ“ Cadastro Geral")
    tipo = st.selectbox("O que deseja cadastrar?", ["Cliente", "Produto (Peixe / CamarÃ£o)", "Fornecedor"])
    
    nome = st.text_input("Nome / DescriÃ§Ã£o")
    telefone = st.text_input("Telefone / Contato")
    
    if st.button("Salvar Cadastro"):
        st.success(f"{tipo} '{nome}' cadastrado com sucesso!")

# Outras telas
else:
    st.title(f"ðŸ“Œ {opcao}")
    st.info("MÃ³dulo em desenvolvimento. Em breve novos recursos aqui!")
