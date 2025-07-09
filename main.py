import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, \
    BackgroundTasks
from pydantic import BaseModel
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from llm_config import get_llm

import asyncio
import sys
import traceback
import platform
import uuid
from typing import Dict
import locale

load_dotenv()

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("DEBUG: Política de loop de eventos definida para WindowsProactorEventLoopPolicy.")

app = FastAPI(
    title="KlarosAI - Assistente de Conhecimento Interno",
    description="API para interação com a base de conhecimento interna da empresa.",
    version="0.0.1",
)

DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH")
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

if not DOCUMENTS_PATH:
    raise ValueError("DOCUMENTS_PATH não está definido no arquivo .env")
if not CHROMA_PERSIST_DIRECTORY:
    raise ValueError("CHROMA_PERSIST_DIRECTORY não está definido no arquivo .env")

class ChatRequest(BaseModel):
    query: str


class IngestionStatusResponse(BaseModel):
    task_id: str
    status: str
    message: str = None

qa_chain = None
ingestion_tasks: Dict[str, Dict] = {}

PROMPT_TEMPLATE = """Use os seguintes trechos de contexto para responder à pergunta do usuário.
Se você não souber a resposta, apenas diga que não sabe, não tente inventar uma resposta.
Mantenha a resposta concisa e precisa, citando a página de onde a informação foi retirada, se possível.

Contexto:
{context}

Pergunta: {question}
"""
QA_CHAIN_PROMPT = PromptTemplate.from_template(PROMPT_TEMPLATE)

async def _initialize_qa_chain():
    """
    Inicializa a cadeia de QA (RetrievalQA) carregando o LLM, embeddings
    e a base de dados ChromaDB.
    """
    global qa_chain
    print("Tentando inicializar/re-inicializar a cadeia de QA...")
    try:
        llm = get_llm()
        print("LLM carregado.")

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        print("Modelo de embeddings carregado.")


        if not os.path.exists(CHROMA_PERSIST_DIRECTORY):
            print(
                f"Diretório ChromaDB não encontrado: {CHROMA_PERSIST_DIRECTORY}. Certifique-se de ter executado ingest.py primeiro.")
            vectorstore = Chroma(
                embedding_function=embeddings,
                persist_directory=CHROMA_PERSIST_DIRECTORY
            )
        else:
            vectorstore = Chroma(
                persist_directory=CHROMA_PERSIST_DIRECTORY,
                embedding_function=embeddings
            )
        print("ChromaDB carregado.")

        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 10}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
            verbose=True
        )
        print("Cadeia de QA inicializada com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar a cadeia de QA: {e}")
        traceback.print_exc()
        qa_chain = None

@app.on_event("startup")
async def startup_event():
    """
    Executa durante a inicialização da aplicação FastAPI.
    Inicializa a cadeia de QA.
    """
    await _initialize_qa_chain()

async def _process_uploaded_file_background(task_id: str, file_path: str):
    """
    Processa o arquivo uploaded em um processo separado para não bloquear a API.
    Atualiza o status da tarefa de ingestão.
    """
    ingestion_tasks[task_id]["status"] = "processing"
    ingestion_tasks[task_id]["message"] = "Iniciando processamento em segundo plano..."
    print(f"Iniciando processamento em segundo plano para: {file_path}")

    try:
        python_executable = sys.executable
        command_args = [python_executable, "ingest.py", file_path]
        print(f"DEBUG: Comando completo a ser executado: {command_args}")

        process = await asyncio.create_subprocess_exec(
            *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        system_encoding = locale.getpreferredencoding(False)

        stdout_decoded = stdout.decode(system_encoding, errors='ignore')
        stderr_decoded = stderr.decode(system_encoding, errors='ignore')

        if process.returncode == 0:
            ingestion_tasks[task_id]["status"] = "completed"
            ingestion_tasks[task_id]["message"] = "Ingestão concluída com sucesso."
            print(f"Ingestão em segundo plano concluída com sucesso para {file_path}.")
            print("Saída do ingest.py (stdout):\n", stdout_decoded)
            print("Re-inicializando a cadeia de QA para carregar os novos documentos...")
            await _initialize_qa_chain()
            print("Cadeia de QA re-inicializada com sucesso.")
        else:
            ingestion_tasks[task_id]["status"] = "failed"
            ingestion_tasks[task_id][
                "message"] = f"Erro na ingestão. Código de saída: {process.returncode}. Erro: {stderr_decoded}"
            print(f"Erro na ingestão em segundo plano para {file_path}. Código de saída: {process.returncode}")
            print("Erro do ingest.py (stderr):\n", stderr_decoded)
            if "Batch size" in stderr_decoded:
                ingestion_tasks[task_id][
                    "message"] = "Erro de tamanho de batch do ChromaDB. O documento pode ser muito grande ou a configuração de chunks precisa ser ajustada."

    except Exception as e:
        ingestion_tasks[task_id]["status"] = "failed"
        ingestion_tasks[task_id]["message"] = f"Exceção durante a ingestão: {e}"
        print(f"Exceção durante a ingestão em segundo plano para {file_path}: {e}")
        traceback.print_exc()


@app.post("/uploadfile/")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Recebe um arquivo, salva-o e inicia o processamento de ingestão em segundo plano.
    """
    if not os.path.exists(DOCUMENTS_PATH):
        os.makedirs(DOCUMENTS_PATH)

    file_location = os.path.join(DOCUMENTS_PATH, file.filename)
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        print(f"Arquivo {file.filename} salvo em {file_location}")

        task_id = str(uuid.uuid4())
        ingestion_tasks[task_id] = {"status": "pending", "message": "Fila para processamento..."}
        background_tasks.add_task(_process_uploaded_file_background, task_id, file_location)

        return {"message": f"Arquivo '{file.filename}' carregado. O processamento foi iniciado em segundo plano.",
                "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar ou processar o arquivo: {e}")


@app.get("/ingestion-status/{task_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(task_id: str):
    """
    Verifica o status de uma tarefa de ingestão em segundo plano.
    """
    task_info = ingestion_tasks.get(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="ID da tarefa não encontrado.")
    return IngestionStatusResponse(
        task_id=task_id,
        status=task_info["status"],
        message=task_info.get("message")
    )


@app.post("/chat/")
async def chat(request: ChatRequest):
    """
    Recebe uma query e retorna uma resposta da IA baseada nos documentos na base de conhecimento.
    """
    print(f"Received chat request with query: {request.query}")
    if qa_chain is None:
        raise HTTPException(status_code=503, detail="A IA ainda não foi inicializada. Tente novamente em instantes.")

    try:
        print(f"Input being sent to qa_chain.ainvoke: {{'query': '{request.query}'}}")
        result = await qa_chain.ainvoke({"query": request.query})

        answer = result.get("result", "Não foi possível gerar uma resposta para sua pergunta.")
        source_documents = result.get("source_documents", [])

        formatted_sources = []
        for doc in source_documents:
            source_path = doc.metadata.get('source', 'Desconhecido')
            source_name = os.path.basename(str(source_path))
            print("--- Documentos de Origem Recuperados (para depuração) ---")
            print(f"Documento: {source_name} - Página: {doc.metadata.get('page', 'N/A')}")
            print(f"Conteúdo (trecho): {doc.page_content[:500]}...")
            print("--------------------")

            formatted_sources.append({
                "content": doc.page_content,
                "source": source_name,
                "page": doc.metadata.get('page', 'N/A')
            })

        return {
            "query": request.query,
            "response": answer,
            "source_documents": formatted_sources
        }
    except Exception as e:
        print(f"Erro ao processar a requisição: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500,
                            detail=f"Erro ao processar a requisição: {e}. Verifique o log do servidor para mais detalhes.")

@app.get("/")
async def root():
    return {"message": "KlarosAI API está rodando!"}