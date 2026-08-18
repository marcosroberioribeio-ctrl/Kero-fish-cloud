import pandas as pd
import streamlit as st

st.set_page_config(page_title="Kero Fish - Financeiro", layout="wide")

# Nome exato do arquivo da planilha que você enviou
FILE_PATH = "KERO FISH_Financeira_Completa_Preenchida-4.xlsx"

@st.cache_data
def load_data():
    # Lê a planilha do Excel diretamente
    return pd.read_excel(FILE_PATH)

st.title("🐟 Kero Fish - Sistema Financeiro")

# Carregando os dados
try:
    df = load_data()
    st.success("Planilha carregada com sucesso!")
    
    # Mostra uma prévia dos dados na tela para testar
    st.dataframe(df.head())
    
except Exception as e:
    st.error(f"Erro ao carregar o arquivo: {e}")
