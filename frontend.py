import streamlit as st
import requests
import time
import os

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="KlarosAI - Seu Assistente de Conhecimento",
    page_icon="static/klaros_logo.png",
    layout="centered",
    initial_sidebar_state="auto",
)

col1, col2 = st.columns([0.1, 0.9])

with col1:
    st.image("static/klaros_logo_page.png", width=60)

with col2:
    st.markdown("<h1 style='vertical-align: middle; display: inline-block; margin-left: 10px;'>KlarosAI - Seu Assistente de Conhecimento</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "ingestion_status" not in st.session_state:
    st.session_state.ingestion_status = None
if "ingestion_task_id" not in st.session_state:
    st.session_state.ingestion_task_id = None

def display_message(role, content):
    with st.chat_message(role):
        st.markdown(content)

for message in st.session_state.messages:
    display_message(message["role"], message["content"])

uploaded_file = st.sidebar.file_uploader(
    "Carregar Documento (PDF, TXT, DOCX)",
    type=["pdf", "txt", "docx"],
    accept_multiple_files=False,
    key="file_uploader"
)

if uploaded_file is not None:
    if st.session_state.ingestion_status is None or st.session_state.ingestion_status in ["completed", "failed"]:
        st.sidebar.info("Arquivo carregado. Iniciando ingestão...")
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(f"{API_BASE_URL}/uploadfile/", files=files)
            response.raise_for_status()

            upload_result = response.json()
            st.session_state.ingestion_task_id = upload_result.get("task_id")
            st.session_state.ingestion_status = "pending"
            st.sidebar.success(f"Upload bem-sucedido! ID da Tarefa: {st.session_state.ingestion_task_id}")

        except requests.exceptions.RequestException as e:
            st.sidebar.error(f"Erro ao carregar o arquivo: {e}")
            st.session_state.ingestion_status = "failed"
            st.session_state.ingestion_task_id = None
        except Exception as e:
            st.sidebar.error(f"Ocorreu um erro inesperado durante o upload: {e}")
            st.session_state.ingestion_status = "failed"
            st.session_state.ingestion_task_id = None
    else:
        st.sidebar.warning(f"Já existe uma ingestão em andamento: {st.session_state.ingestion_status.capitalize()}")

if st.session_state.ingestion_task_id and st.session_state.ingestion_status not in ["completed", "failed"]:
    st.sidebar.text(f"Status da Ingestão: {st.session_state.ingestion_status.capitalize()}...")
    try:
        status_response = requests.get(f"{API_BASE_URL}/ingestion-status/{st.session_state.ingestion_task_id}")
        status_response.raise_for_status()
        current_status = status_response.json()

        if current_status["status"] != st.session_state.ingestion_status:
            st.session_state.ingestion_status = current_status["status"]
            if st.session_state.ingestion_status == "completed":
                st.sidebar.success(f"Ingestão concluída: {current_status.get('message', 'Documento processado.')}")
                st.rerun()
            elif st.session_state.ingestion_status == "failed":
                st.sidebar.error(f"Ingestão falhou: {current_status.get('message', 'Verifique os logs do servidor.')}")
            else:
                st.sidebar.info(f"Status atual: {current_status.get('status')} - {current_status.get('message')}")

    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"Erro ao verificar status da ingestão: {e}")
        st.session_state.ingestion_status = "failed"
    time.sleep(1)
    st.rerun()

if prompt := st.chat_input("Pergunte sobre seus documentos aqui..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    display_message("user", prompt)

    with st.spinner("Pensando..."):
        response = None
        try:
            response = requests.post(f"{API_BASE_URL}/chat/", json={"query": prompt})
            response.raise_for_status()

            api_response = response.json()
            assistant_response = api_response.get("response", "Não foi possível obter uma resposta.")
            source_documents = api_response.get("source_documents", [])

            st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            display_message("assistant", assistant_response)

            if source_documents:
                with st.expander("Documentos de Origem Utilizados"):
                    for doc in source_documents:
                        st.write(f"**Fonte:** {doc.get('source', 'Desconhecido')} - Página: {doc.get('page', 'N/A')}")
                        st.code(doc.get('content', '')[:500] + '...' if len(doc.get('content', '')) > 500 else doc.get('content', ''))

        except requests.exceptions.RequestException as e:
            error_message = f"Erro de comunicação com a API: {e}"
            if response is not None:
                try:
                    error_detail = response.json().get("detail", "Nenhum detalhe adicional.")
                    error_message = f"Erro da API: {error_detail}"
                except ValueError:
                    error_message = f"Erro da API: {response.text}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": f"Ocorreu um erro: {error_message}"})
            display_message("assistant", f"Ocorreu um erro: {error_message}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Ocorreu um erro inesperado: {e}"})
            display_message("assistant", f"Ocorreu um erro inesperado: {e}")