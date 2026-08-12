 import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="Kero Fish", page_icon="🐟", layout="wide")

st.title("🐟 Kero Fish - Sistema de Gestão")
st.write("Aplicativo conectado ao banco de dados Supabase.")

# Exemplo de interface inicial
st.success("Conexão e estrutura prontas para uso!")
