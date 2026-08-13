# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(page_title="Kero Fish - Peixe e Camarao", page_icon="ðŸŸ", layout="wide")

# Exibe a foto oficial do logo
st.sidebar.image("Screenshot_20260813_084749_WhatsApp.jpg", use_container_width=True)

opcao = st.sidebar.radio(
    "Navegacao",
    ["Inicio", "Cadastro", "Estoque / Producao", "Vendas", "Financeiro"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("ðŸ“ž **Contatos:**\n- (85) 98502-6019\n- (85) 99277-6984")
st.sidebar.markdown("ðŸ“· **Instagram:** @kerofish")

# Tela de Inicio
if opcao == "Inicio":
    st.title("Kero Fish - Peixe e Camarao")
    st.write("Sistema de Gestao Integrada")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vendas do Mes", "R$ 0,00")
    col2.metric("Estoque Atual", "0 kg")
    col3.metric("Clientes Ativos", "0")

# Tela de Cadastro
elif opcao == "Cadastro":
    st.title("Cadastro Geral")
    tipo = st.selectbox("O que deseja cadastrar?", ["Cliente", "Produto (Peixe / Camarao)", "Fornecedor"])
    
    nome = st.text_input("Nome / Descricao")
    telefone = st.text_input("Telefone / Contato")
    
    if st.button("Salvar Cadastro"):
        st.success(f"{tipo} '{nome}' cadastrado com sucesso!")

# Outras telas
else:
    st.title(f"{opcao}")
    st.info("Modulo em desenvolvimento. Em breve novos recursos aqui!")
