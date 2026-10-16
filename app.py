# MIT License
# Copyright (c) 2026 AI Architect
# Permission is hereby granted, free of charge, to any person obtaining a copy...

import json
import streamlit as st
from openai import AzureOpenAI

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="Extrator de Dados Inteligente (Azure OpenAI)",
    page_icon="🤖",
    layout="centered",
)


@st.cache_resource
def init_azure_client():
  """Inicializa o cliente AzureOpenAI de forma segura usando st.secrets."""
  try:
    endpoint = st.secrets["AZURE_OPENAI_ENDPOINT"]
    api_key = st.secrets["AZURE_OPENAI_API_KEY"]

    # Instancia o cliente oficial do Azure OpenAI
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-02-01",  # Versão estável recomendada
    )
    return client
  except Exception as e:
    st.error(
        "Erro ao carregar as credenciais. Verifique se o arquivo"
        " .streamlit/secrets.toml está configurado corretamente."
    )
    st.stop()


client = init_azure_client()
deployment_name = st.secrets.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")

# Interface do Usuário
st.title("📊 Extrator de Dados Inteligente")
st.markdown(
    "Insira um texto corporativo, feedback ou mensagem abaixo para extração"
    " automatizada de insights usando **Azure OpenAI**."
)

# Campo de texto para entrada
texto_usuario = st.text_area(
    "Texto para Análise:",
    placeholder=(
        "Digite ou cole aqui o texto que deseja processar (ex: relatório de"
        " atendimento, email de cliente...)"
    ),
    height=150,
)

if st.button("Processar Dados", type="primary"):
  if not texto_usuario.strip():
    st.warning("Por favor, insira um texto válido antes de processar.")
  else:
    with st.spinner("Analisando dados com Azure OpenAI..."):
      try:
        # System Prompt rígido exigindo formato JSON válido
        system_prompt = (
            "Você é um assistente especialista em análise de dados e NLP."
            " Analise o texto fornecido e retorne estritamente um JSON válido"
            " contendo as seguintes chaves:\n"
            "1. 'sentimento': o sentimento geral (ex: Positivo, Neutro, Negativo).\n"
            "2. 'porcentagem_sentimento': um número inteiro de 0 a 100 indicando a"
            " intensidade/certeza desse sentimento.\n"
            "3. 'assunto_principal': uma frase curta resumindo o foco do texto.\n"
            "4. 'pessoas_citadas': uma lista (array) contendo os nomes de pessoas"
            " mencionadas no texto (vazia se não houver).\n"
            "5. 'nivel_de_urgencia': estritamente um dos valores: 'Baixo',"
            " 'Medio', ou 'Alto'.\n"
            "Certifique-se de que a resposta seja APENAS o JSON válido."
        )

        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": texto_usuario},
            ],
            response_format={"type": "json_object"},  # Garante retorno em JSON
            temperature=0.1,  # Baixa temperatura para maior determinismo
        )

        # Extração e conversão do conteúdo JSON retornado
        resultado_json = json.loads(response.choices[0].message.content)

        st.success("Processamento concluído com sucesso!")
        st.divider()

        # Exibição Estruturada na Interface
        st.subheader("📋 Resultados Extraídos")

        col1, col2, col3 = st.columns(3)

        with col1:
          st.metric(
              label="Sentimento",
              value=resultado_json.get("sentimento", "N/A"),
          )

        with col2:
          porcentagem = resultado_json.get("porcentagem_sentimento", 0)
          st.metric(label="Intensidade", value=f"{porcentagem}%")

        with col3:
          urgencia = resultado_json.get("nivel_de_urgencia", "Baixo")
          st.metric(label="Nível de Urgência", value=urgencia)

        st.markdown("**Assunto Principal:**")
        st.info(resultado_json.get("assunto_principal", "Não especificado"))

        st.markdown("**Pessoas Citadas:**")
        pessoas = resultado_json.get("pessoas_citadas", [])
        if pessoas:
          for pessoa in pessoas:
            st.markdown(f"- 👤 {pessoa}")
        else:
          st.markdown("_Nenhuma pessoa citada no texto._")

        # Exibição do JSON bruto para auditoria técnica
        with st.expander("Ver JSON Bruto Retornado"):
          st.json(resultado_json)

      except Exception as e:
        st.error(f"Ocorreu um erro durante a comunicação com o Azure OpenAI: {e}")
