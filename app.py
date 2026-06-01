import streamlit as st
import requests
import re

# 1. PUXANDO A CHAVE (SECRET)
try:
    API_KEY = st.secrets["DATAJUD_API_KEY"]
except KeyError:
    API_KEY = None
    st.error("❌ API Key não encontrada no Streamlit Cloud.")

st.title("⚖️ Buscador de Processos - Datajud")
st.write("Consulta pública processual via CNJ")

# 2. GERANDO A LISTA COMPLETA DE TRIBUNAIS
lista_tribunais = {
    "Superior Tribunal de Justiça (STJ)": "stj",
    "Tribunal Superior do Trabalho (TST)": "tst",
    "Tribunal Superior Eleitoral (TSE)": "tse",
    "Superior Tribunal Militar (STM)": "stm"
}

ufs = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC', 'SE', 'SP', 'TO']

# Gerando TJs
for uf in ufs:
    lista_tribunais[f"Tribunal de Justiça - {uf} (TJ{uf})"] = f"tj{uf.lower()}"

# Gerando TRFs (1 a 6)
for i in range(1, 7):
    lista_tribunais[f"Tribunal Regional Federal da {i}ª Região (TRF{i})"] = f"trf{i}"

# Gerando TRTs (1 a 24)
for i in range(1, 25):
    lista_tribunais[f"Tribunal Regional do Trabalho da {i}ª Região (TRT{i})"] = f"trt{i}"

# Gerando TREs
for uf in ufs:
    lista_tribunais[f"Tribunal Regional Eleitoral - {uf} (TRE-{uf})"] = f"tre{uf.lower()}"

# Gerando TJMs (Existem em SP, MG e RS)
for uf in ['SP', 'MG', 'RS']:
    lista_tribunais[f"Tribunal de Justiça Militar - {uf} (TJM{uf})"] = f"tjm{uf.lower()}"

nomes_tribunais = list(lista_tribunais.keys())

# Procurando o índice do TJRS para deixar como padrão no dropdown
try:
    index_padrao = nomes_tribunais.index("Tribunal de Justiça - RS (TJRS)")
except ValueError:
    index_padrao = 0

nome_tribunal = st.selectbox("Selecione o Tribunal:", nomes_tribunais, index=index_padrao)
sigla_tribunal = lista_tribunais[nome_tribunal]

# 3. CAMPO PARA O NÚMERO DO PROCESSO
numero_processo_input = st.text_input("Digite o número do processo:", placeholder="Ex: 50016282720268210014")

# Limpeza automática: remove pontos e traços, deixando só números
numero_processo = re.sub(r'[^0-9]', '', numero_processo_input)

# 4. BOTÃO E REQUISIÇÃO (ENVIANDO O CÓDIGO RAW)
if st.button("Buscar Processo"):
    if not API_KEY:
        st.warning("⚠️ O sistema precisa da API Key para funcionar.")
    elif not numero_processo:
        st.warning("⚠️ Por favor, digite um número de processo.")
    else:
        with st.spinner(f"Consultando o {nome_tribunal} no Datajud..."):
            
            # Nota: Consultas que enviam body ("raw") no Datajud exigem o final /_search na URL
            url_api = f"https://api-publica.datajud.cnj.jus.br/api_publica_{sigla_tribunal}/_search"
            
            headers = {
                "Authorization": f"APIKey {API_KEY}",
                "Content-Type": "application/json"
            }
            
            # O código raw exato que você pediu
            payload = {
                "query": {
                    "match": {
                        "numeroProcesso": numero_processo
                    }
                }
            }
            
            try:
                # Usamos requests.post() em vez de get() porque estamos enviando um payload (dados)
                response = requests.post(url_api, headers=headers, json=payload)
                
                if response.status_code == 200:
                    dados = response.json()
                    st.success("✅ Busca concluída!")
                    
                    # Exibe o resultado bruto e completo na tela
                    st.json(dados)
                else:
                    st.error(f"Erro na requisição: Status {response.status_code}")
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"Ocorreu um erro ao conectar com a API: {e}")
