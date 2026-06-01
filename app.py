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

for uf in ufs:
    lista_tribunais[f"Tribunal de Justiça - {uf} (TJ{uf})"] = f"tj{uf.lower()}"
for i in range(1, 7):
    lista_tribunais[f"Tribunal Regional Federal da {i}ª Região (TRF{i})"] = f"trf{i}"
for i in range(1, 25):
    lista_tribunais[f"Tribunal Regional do Trabalho da {i}ª Região (TRT{i})"] = f"trt{i}"
for uf in ufs:
    lista_tribunais[f"Tribunal Regional Eleitoral - {uf} (TRE-{uf})"] = f"tre{uf.lower()}"
for uf in ['SP', 'MG', 'RS']:
    lista_tribunais[f"Tribunal de Justiça Militar - {uf} (TJM{uf})"] = f"tjm{uf.lower()}"

nomes_tribunais = list(lista_tribunais.keys())

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
            
            url_api = f"https://api-publica.datajud.cnj.jus.br/api_publica_{sigla_tribunal}/_search"
            
            headers = {
                "Authorization": f"APIKey {API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": {
                    "match": {
                        "numeroProcesso": numero_processo
                    }
                }
            }
            
            # --- BLOCO TRY / EXCEPT CORRIGIDO ---
            try:
                response = requests.post(url_api, headers=headers, json=payload)
                
                if response.status_code == 200:
                    dados = response.json()
                    st.success("✅ Busca concluída!")
                    
                    # --- INÍCIO DA FORMATAÇÃO VISUAL ---
                    hits = dados.get("hits", {}).get("hits", [])
                    
                    if len(hits) > 0:
                        processo = hits[0].get("_source", {})
                        
                        numero = processo.get("numeroProcesso", "N/A")
                        classe = processo.get("classe", {}).get("nome", "N/A")
                        orgao = processo.get("orgaoJulgador", {}).get("nome", "N/A")
                        sigilo = processo.get("nivelSigilo", 0)
                        
                        data_raw = processo.get("dataAjuizamento", "")
                        data_ajuizamento = f"{data_raw[6:8]}/{data_raw[4:6]}/{data_raw[:4]}" if len(data_raw) >= 8 else "N/A"
                        
                        st.subheader(f"📄 Processo: {numero}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Classe:** {classe}")
                            st.markdown(f"**Data de Ajuizamento:** {data_ajuizamento}")
                        with col2:
                            st.markdown(f"**Órgão Julgador:** {orgao}")
                            st.markdown(f"**Nível de Sigilo:** {sigilo}")
                            
                        assuntos = processo.get("assuntos", [])
                        if assuntos:
                            st.write("**Assuntos:**")
                            tags = " | ".join([assunto.get("nome", "") for assunto in assuntos])
                            st.info(tags)
                            
                        st.divider() 
                        
                        movimentos = processo.get("movimentos", [])
                        if movimentos:
                            st.subheader("⏱️ Histórico de Movimentações")
                            
                            mov_ordenados = sorted(movimentos, key=lambda x: x.get("dataHora", ""), reverse=True)
                            
                            for mov in mov_ordenados:
                                nome_mov = mov.get("nome", "Movimentação")
                                data_hora_raw = mov.get("dataHora", "")
                                
                                if data_hora_raw:
                                    partes_data = data_hora_raw[:10].split("-")
                                    data_mov = f"{partes_data[2]}/{partes_data[1]}/{partes_data[0]}"
                                else:
                                    data_mov = "Data indisponível"
                                
                                with st.expander(f"{data_mov} - {nome_mov}"):
                                    st.write(f"**Lançado por:** {mov.get('orgaoJulgador', {}).get('nome', 'N/A')}")
                                    
                                    complementos = mov.get("complementosTabelados", [])
                                    for comp in complementos:
                                        st.write(f"- *Detalhe:* {comp.get('nome', '')} ({comp.get('descricao', '')})")
                        else:
                            st.info("Nenhuma movimentação encontrada para este processo.")
                    else:
                        st.warning("A API retornou sucesso, mas não encontrou o detalhamento deste processo.")
                    # --- FIM DA FORMATAÇÃO VISUAL ---
                        
                else:
                    st.error(f"Erro na requisição: Status {response.status_code}")
                    st.write(response.text)
                    
            except Exception as e:
                # É este 'except' aqui que havia se perdido na hora de colar!
                st.error(f"Ocorreu um erro ao conectar com a API: {e}")
