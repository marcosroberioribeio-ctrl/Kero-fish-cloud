import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Kero Fish - Sistema Financeiro", layout="wide")

# Caminho do arquivo (certifique-se de que o nome está idêntico)
FILE_PATH = 'KERO FISH_Financeira_Completa_Preenchida-4.xlsx'

@st.cache_data
def load_data():
    return pd.read_excel(FILE_PATH)

st.title("🐟 Kero Fish - Sistema Financeiro")

try:
    df = load_data()

    # Menu Lateral
    menu = st.sidebar.selectbox("Navegação", ["Visão Geral", "Vendas", "Compras", "Estoque"])

    if menu == "Visão Geral":
        st.subheader("Resumo dos Dados")
        st.dataframe(df)

    elif menu == "Vendas":
        st.subheader("Relatório de Vendas")
        # Ajuste o 'Tipo' e 'Venda' conforme o texto real na sua planilha
        vendas = df[df.astype(str).apply(lambda x: x.str.contains('Venda', case=False)).any(axis=1)]
        st.dataframe(vendas)

    elif menu == "Compras":
        st.subheader("Relatório de Compras")
        compras = df[df.astype(str).apply(lambda x: x.str.contains('Compra', case=False)).any(axis=1)]
        st.dataframe(compras)
        
    elif menu == "Estoque":
        st.subheader("Controle de Estoque")
        estoque = df[df.astype(str).apply(lambda x: x.str.contains('Estoque', case=False)).any(axis=1)]
        st.dataframe(estoque)

except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
