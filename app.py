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
                    
                    # --- INÍCIO DA FORMATAÇÃO VISUAL ---
                    
                    # 1. Entrando na "gaveta" correta do JSON
                    hits = dados.get("hits", {}).get("hits", [])
                    
                    if len(hits) > 0:
                        # Pegamos o primeiro resultado (índice 0) e a chave "_source"
                        processo = hits[0].get("_source", {})
                        
                        # 2. Extraindo as informações principais
                        numero = processo.get("numeroProcesso", "N/A")
                        classe = processo.get("classe", {}).get("nome", "N/A")
                        orgao = processo.get("orgaoJulgador", {}).get("nome", "N/A")
                        sigilo = processo.get("nivelSigilo", 0)
                        
                        # A data de ajuizamento vem num formato estranho (Ex: 20260227165132). Vamos formatar para DD/MM/YYYY.
                        data_raw = processo.get("dataAjuizamento", "")
                        data_ajuizamento = f"{data_raw[6:8]}/{data_raw[4:6]}/{data_raw[:4]}" if len(data_raw) >= 8 else "N/A"
                        
                        # 3. Desenhando o Cabeçalho
                        st.subheader(f"📄 Processo: {numero}")
                        
                        # Criando colunas para organizar a tela
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Classe:** {classe}")
                            st.markdown(f"**Data de Ajuizamento:** {data_ajuizamento}")
                        with col2:
                            st.markdown(f"**Órgão Julgador:** {orgao}")
                            st.markdown(f"**Nível de Sigilo:** {sigilo}")
                            
                        # 4. Desenhando as Tags de Assuntos
                        assuntos = processo.get("assuntos", [])
                        if assuntos:
                            st.write("**Assuntos:**")
                            # Cria uma linha com as tags
                            tags = " | ".join([assunto.get("nome", "") for assunto in assuntos])
                            st.info(tags)
                            
                        st.divider() # Linha separadora
                        
                        # 5. Criando a Linha do Tempo (Movimentações)
                        movimentos = processo.get("movimentos", [])
                        if movimentos:
                            st.subheader("⏱️ Histórico de Movimentações")
                            
                            # Opcional: Ordenar as movimentações da mais recente para a mais antiga
                            mov_ordenados = sorted(movimentos, key=lambda x: x.get("dataHora", ""), reverse=True)
                            
                            for mov in mov_ordenados:
                                nome_mov = mov.get("nome", "Movimentação")
                                data_hora_raw = mov.get("dataHora", "")
                                
                                # A data vem assim: 2026-04-22T03:34:18.000Z. Vamos quebrar e pegar só o DD/MM/YYYY
                                if data_hora_raw:
                                    partes_data = data_hora_raw[:10].split("-")
                                    data_mov = f"{partes_data[2]}/{partes_data[1]}/{partes_data[0]}"
                                else:
                                    data_mov = "Data indisponível"
                                
                                # Usamos o st.expander para criar "caixinhas" que abrem e fecham
                                with st.expander(f"{data_mov} - {nome_mov}"):
                                    st.write(f"**Lançado por:** {mov.get('orgaoJulgador', {}).get('nome', 'N/A')}")
                                    
                                    # Se a movimentação tiver detalhes extras (complementos)
                                    complementos = mov.get("complementosTabelados", [])
                                    for comp in complementos:
                                        st.write(f"- *Detalhe:* {comp.get('nome', '')} ({comp.get('descricao', '')})")
                        else:
                            st.info("Nenhuma movimentação encontrada para este processo.")
                    else:
                        st.warning("A API retornou sucesso, mas não encontrou o detalhamento deste processo.")
                    
                    # --- FIM DA FORMATAÇÃO VISUAL ---
