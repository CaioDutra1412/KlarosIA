import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Mantenha GoogleGenerativeAIEmbeddings se estiver usando Gemini para embeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import shutil # Para remover o diretório existente do ChromaDB (ainda útil para recriação manual)
import sys # Nova importação para argumentos de linha de comando

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Define o diretório onde os documentos estão e onde o ChromaDB será salvo
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH")
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

# Verifica se os caminhos estão configurados
if not DOCUMENTS_PATH:
    raise ValueError("DOCUMENTS_PATH não está definido no arquivo .env")
if not CHROMA_PERSIST_DIRECTORY:
    raise ValueError("CHROMA_PERSIST_DIRECTORY não está definido no arquivo .env")

# --- Configuração do Loader de Embeddings ---
# Usando GoogleGenerativeAIEmbeddings como no seu main.py
EMBEDDINGS = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# --- Funções Auxiliares ---
def load_documents(directory_path: str, specific_file: str = None):
    """
    Carrega documentos do diretório especificado ou de um arquivo específico.
    Suporta PDF, TXT e DOCX.
    """
    documents = []
    if specific_file:
        file_path = os.path.join(directory_path, specific_file)
        if not os.path.exists(file_path):
            print(f"Erro: Arquivo '{file_path}' não encontrado.")
            return []
        print(f"Carregando documento específico: {file_path}")
        if file_path.lower().endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.lower().endswith(".txt"):
            loader = TextLoader(file_path)
        elif file_path.lower().endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            print(f"Tipo de arquivo não suportado para {file_path}. Ignorando.")
            return []
        documents.extend(loader.load())
    else:
        print(f"Carregando documentos do diretório: {directory_path}")
        for root, _, files in os.walk(directory_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                print(f"Carregando: {file_path}")
                if file_name.lower().endswith(".pdf"):
                    loader = PyPDFLoader(file_path)
                elif file_name.lower().endswith(".txt"):
                    loader = TextLoader(file_path)
                elif file_name.lower().endswith(".docx"):
                    loader = Docx2txtLoader(file_path)
                else:
                    print(f"Tipo de arquivo não suportado para {file_name}. Ignorando.")
                    continue
                documents.extend(loader.load())
    return documents

def split_documents(documents):
    """
    Divide os documentos em chunks menores para processamento.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def process_documents_and_add_to_vectorstore(specific_file: str = None):
    """
    Carrega, divide em chunks e adiciona documentos ao ChromaDB.
    Se specific_file for fornecido, processa apenas esse arquivo.
    Caso contrário, processa todos os documentos no DOCUMENTS_PATH.
    """
    # 1. Carrega os documentos
    documents = load_documents(DOCUMENTS_PATH, specific_file=specific_file)
    print(f"Total de documentos carregados: {len(documents)}")

    if not documents:
        print("Nenhum documento encontrado ou carregado para ingestão. Verifique o caminho/arquivo e os tipos de arquivo suportados.")
        return

    # 2. Divide em chunks
    print("Documentos divididos em chunks...")
    texts = split_documents(documents)
    print(f"Total de chunks criados: {len(texts)}")

    # 3. Inicializa ou carrega o ChromaDB
    # Verifica se o diretório ChromaDB existe e contém dados válidos
    chroma_db_files_exist = os.path.exists(CHROMA_PERSIST_DIRECTORY) and \
                            os.path.exists(os.path.join(CHROMA_PERSIST_DIRECTORY, "chroma.sqlite3"))

    if not chroma_db_files_exist:
        print(f"Diretório ChromaDB ({CHROMA_PERSIST_DIRECTORY}) está vazio ou não existe completamente. Criando um novo ChromaDB.")
        vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=EMBEDDINGS,
            persist_directory=CHROMA_PERSIST_DIRECTORY
        )
        print("Novo ChromaDB criado e documentos adicionados.")
    else:
        print(f"Carregando ChromaDB existente de: {CHROMA_PERSIST_DIRECTORY}")
        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            embedding_function=EMBEDDINGS
        )
        print(f"Adicionando {len(texts)} chunks ao ChromaDB existente.")
        # Adiciona os novos chunks. ChromaDB irá lidar com a idempotência e os IDs.
        # Ele gerencia automaticamente o batching interno para adição de documentos.
        vectorstore.add_documents(texts)
        print("Chunks adicionados com sucesso ao ChromaDB existente.")

# --- Execução Principal ---
if __name__ == "__main__":
    # Remove o diretório persistente do ChromaDB se for o primeiro argumento 'clean'
    # Use isso para recriar o DB do zero manualmente: python ingest.py clean
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        if os.path.exists(CHROMA_PERSIST_DIRECTORY):
            print(f"Removendo diretório ChromaDB existente: {CHROMA_PERSIST_DIRECTORY}")
            shutil.rmtree(CHROMA_PERSIST_DIRECTORY)
            print("Diretório ChromaDB limpo.")
        else:
            print("Diretório ChromaDB não encontrado para limpeza.")
        sys.exit(0) # Sai após a limpeza

    # Se um caminho de arquivo específico for passado como argumento (do main.py)
    if len(sys.argv) > 1:
        # sys.argv[1] será o caminho completo do arquivo, ex: ./data/CPC.pdf
        # Precisamos extrair apenas o nome do arquivo.
        file_path_arg = sys.argv[1]
        file_name = os.path.basename(file_path_arg)
        process_documents_and_add_to_vectorstore(specific_file=file_name)
    else:
        # Se nenhum argumento for passado (execução manual), processa todos os documentos
        print("Iniciando ingestão de TODOS os documentos no diretório de dados (nenhum arquivo específico fornecido).")
        process_documents_and_add_to_vectorstore()

    print("Processo de ingestão concluído.")