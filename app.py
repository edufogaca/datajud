import streamlit as st
import requests

# 1. ABRINDO O COFRE NA NUVEM
# No GitHub/Streamlit Cloud, usamos st.secrets em vez de .env
# Isso vai puxar a chave que vamos configurar no painel de controle depois
try:
    API_KEY = st.secrets["DATAJUD_API_KEY"]
except KeyError:
    API_KEY = None
    st.error("❌ API Key não encontrada. Configure o painel de Secrets.")

# 2. CONSTRUINDO A TELA
st.title("⚖️ Buscador de Processos - Datajud")
st.write("Sistema seguro utilizando API Pública do CNJ.")

# 3. CRIANDO O DROPDOWN
lista_tribunais = {
    "TRF 1ª Região (TRF1)": "trf1",
    "Tribunal Superior do Trabalho (TST)": "tst",
    "Tribunal de Justiça de SP (TJSP)": "tjsp",
    "Tribunal Regional Eleitoral de MG (TRE-MG)": "tremg"
}

nome_tribunal = st.selectbox("Selecione o Tribunal desejado:", list(lista_tribunais.keys()))
sigla_tribunal = lista_tribunais[nome_tribunal]

# 4. MONTANDO A URL DINÂMICA
url_api = f"https://api-publica.datajud.cnj.jus.br/api_publica_{sigla_tribunal}/"

st.info(f"🔗 O sistema fará a busca no endpoint: {url_api}")

if API_KEY:
    st.success("✅ Chave Secreta (API Key) conectada com sucesso!")
