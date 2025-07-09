# KlarosAI - Assistente de Conhecimento Interno

O KlarosAI é uma aplicação robusta desenvolvida para atuar como um assistente de conhecimento interno, permitindo que usuários interajam com uma base de dados de documentos por meio de uma interface de chat intuitiva. A aplicação é capaz de ingerir diversos formatos de documentos (PDF, TXT, DOCX), processá-los, criar embeddings e armazená-los em um banco de dados vetorial (ChromaDB). Posteriormente, os usuários podem fazer perguntas em linguagem natural, e a IA (alimentada pelo Google Gemini) recuperará informações relevantes dos documentos ingeridos para fornecer respostas precisas e contextualizadas.

## Funcionalidades Principais

- **Chat com IA:** Interaja com seus documentos de forma conversacional, fazendo perguntas e recebendo respostas baseadas no conteúdo da sua base de conhecimento.
- **Ingestão de Documentos:** Carregue facilmente documentos nos formatos PDF, TXT e DOCX. O sistema processa esses documentos em segundo plano, extraindo o texto, dividindo-o em chunks e criando embeddings para armazenamento no ChromaDB.
- **Processamento Assíncrono:** A ingestão de documentos é realizada em segundo plano, garantindo que a interface do usuário permaneça responsiva e que o processo de upload não bloqueie outras operações.
- **Base de Conhecimento Vetorial:** Utiliza ChromaDB para armazenar os embeddings dos documentos, permitindo uma busca semântica eficiente e recuperação de informações altamente relevante.
- **Geração de Respostas Contextualizadas:** Alavanca o poder do Google Gemini (via LangChain) para gerar respostas inteligentes e concisas, citando as fontes (documentos e páginas) sempre que possível.
- **Interface Intuitiva:** Um frontend construído com Streamlit oferece uma experiência de usuário simples e eficaz para upload de arquivos e interação via chat.

## Tecnologias Utilizadas

O KlarosAI é construído com uma combinação de tecnologias modernas para garantir escalabilidade, eficiência e uma experiência de usuário rica:

- **Backend (API):**
  - **FastAPI:** Um framework web moderno e rápido para construir APIs com Python, conhecido por sua alta performance e facilidade de uso.
  - **LangChain:** Um framework poderoso para desenvolver aplicações alimentadas por modelos de linguagem. Utilizado para orquestrar o fluxo de ingestão, criação de embeddings e a cadeia de QA (Question Answering).
  - **Google Gemini (via `langchain-google-genai`):** O modelo de linguagem grande (LLM) responsável pela compreensão das perguntas e geração das respostas. O modelo `gemini-2.5-flash` é configurado para um bom equilíbrio entre performance e custo.
  - **GoogleGenerativeAIEmbeddings:** Utilizado para criar representações vetoriais (embeddings) dos documentos, essenciais para a busca semântica.
  - **ChromaDB (via `langchain-chroma`):** Um banco de dados vetorial leve e eficiente, utilizado para armazenar os embeddings dos documentos e permitir a recuperação rápida de informações relevantes.
  - **Uvicorn:** Um servidor ASGI de alta performance para rodar a aplicação FastAPI.
  - **Python-dotenv:** Para gerenciar variáveis de ambiente de forma segura e organizada.
  - **Pydantic:** Para validação de dados e serialização/deserialização de modelos de requisição e resposta da API.
  - **Requests:** Para fazer requisições HTTP (utilizado internamente pelo frontend para se comunicar com o backend).

- **Frontend (Interface do Usuário):**
  - **Streamlit:** Um framework Python para criar rapidamente aplicações web interativas e dashboards. Oferece uma maneira simples de construir a interface de chat e upload de arquivos.

- **Processamento de Documentos:**
  - **PyPDF:** Para extrair texto de arquivos PDF.
  - **Python-docx:** Para extrair texto de arquivos DOCX.
  - **Docopt:** Para parsing de argumentos de linha de comando (utilizado pelo script de ingestão).

- **Modelos de Embeddings (para `ingest.py` e `main.py`):**
  - **Torch:** Uma biblioteca de aprendizado de máquina de código aberto, utilizada como base para modelos de embeddings.
  - **Transformers (Hugging Face):** Biblioteca para trabalhar com modelos pré-treinados, incluindo modelos de embeddings.
  - **Sentence-Transformers:** Um framework para embeddings de sentenças, parágrafos e imagens.
  - **ONNX Runtime:** Um acelerador de inferência para modelos de aprendizado de máquina.
  - **Accelerate & BitsAndBytes:** Para otimização e aceleração de modelos grandes, especialmente para uso com Transformers.

## Estrutura do Projeto

O projeto KlarosAI é organizado da seguinte forma:

```
KlarosAI/
├── __pycache__/             # Cache de módulos Python
├── chroma_db/               # Diretório persistente para o banco de dados ChromaDB
│   └── <uuid>/              # Subdiretórios gerados pelo ChromaDB
│   └── chroma.sqlite3       # Arquivo de banco de dados SQLite do ChromaDB
├── data/                    # Diretório para armazenar documentos brutos (configurável via .env)
├── frontend.py              # Aplicação Streamlit para a interface do usuário
├── ingest.py                # Script para processar documentos e popular o ChromaDB
├── llm_config.py            # Configuração do Large Language Model (LLM)
├── main.py                  # Aplicação FastAPI principal (backend da API)
├── model/                   # (Vazio no momento) Potencialmente para modelos de IA locais
├── requirements.txt         # Lista de dependências Python do projeto
├── static/                  # Recursos estáticos para o frontend (e.g., imagens)
│   ├── klaros_logo.png
│   └── klaros_logo_page.png
└── venv_klarosai/           # Ambiente virtual Python (gerado automaticamente)
```

- **`main.py`**: O coração do backend, implementa a API FastAPI para chat e gerenciamento de ingestão de documentos. Ele carrega o LLM, o modelo de embeddings e interage com o ChromaDB.
- **`frontend.py`**: A interface do usuário construída com Streamlit. Permite o upload de documentos e a interação via chat com a IA.
- **`ingest.py`**: Um script auxiliar responsável por ler documentos, dividi-los em chunks, criar embeddings e adicioná-los ao ChromaDB. É executado como um subprocesso pelo `main.py`.
- **`llm_config.py`**: Contém a função para inicializar e configurar o modelo de linguagem (LLM), atualmente o Google Gemini.
- **`requirements.txt`**: Lista todas as bibliotecas Python necessárias para o projeto. É fundamental para replicar o ambiente de desenvolvimento.
- **`chroma_db/`**: Este diretório é onde o ChromaDB persiste os embeddings e metadados dos seus documentos. É criado e gerenciado automaticamente pelos scripts.
- **`data/`**: O diretório configurado para armazenar os documentos que serão ingeridos. Você pode alterar o nome ou caminho no arquivo `.env`.
- **`static/`**: Contém imagens e outros recursos estáticos usados pelo frontend.

## Configuração do Ambiente

Para configurar e executar o KlarosAI em sua máquina local, siga os passos abaixo:

### 1. Pré-requisitos

Certifique-se de ter o seguinte software instalado:

- **Python 3.9+** (Recomendado Python 3.10 ou 3.11)
- **Git** (Opcional, para clonar o repositório)

### 2. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do diretório `KlarosAI/` (o mesmo nível de `main.py` e `frontend.py`) com o seguinte conteúdo:

```dotenv
GOOGLE_API_KEY="SUA_CHAVE_API_DO_GOOGLE_GEMINI"
DOCUMENTS_PATH="./data"
CHROMA_PERSIST_DIRECTORY="./chroma_db"
```

- **`GOOGLE_API_KEY`**: Obtenha sua chave de API do Google AI Studio (https://aistudio.google.com/app/apikey). Esta chave é essencial para que o modelo Gemini funcione.
- **`DOCUMENTS_PATH`**: O caminho para o diretório onde seus documentos (PDF, TXT, DOCX) serão armazenados antes da ingestão. Por padrão, é `./data`.
- **`CHROMA_PERSIST_DIRECTORY`**: O caminho para o diretório onde o ChromaDB persistirá seus dados. Por padrão, é `./chroma_db`.

### 3. Instalação de Dependências

Navegue até o diretório `KlarosAI/` no seu terminal e instale as dependências usando `pip`:

```bash
cd KlarosAI/
python -m venv venv_klarosai
source venv_klarosai/bin/activate  # No Windows: .\venv_klarosai\Scripts\activate
pip install -r requirements.txt
```

Este processo criará um ambiente virtual (`venv_klarosai`) e instalará todas as bibliotecas listadas em `requirements.txt`.

## Como Executar a Aplicação

Com o ambiente configurado, você pode iniciar o backend e o frontend da aplicação.

### 1. Iniciar o Backend (API FastAPI)

No diretório `KlarosAI/`, com o ambiente virtual ativado, execute o seguinte comando:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- `--host 0.0.0.0`: Permite que a API seja acessível de outras máquinas na rede (se necessário).
- `--port 8000`: Define a porta em que a API será executada. O frontend está configurado para se comunicar com esta porta.
- `--reload`: Reinicia o servidor automaticamente a cada alteração no código (útil para desenvolvimento).

Você verá mensagens no terminal indicando que o servidor Uvicorn foi iniciado. A API estará acessível em `http://localhost:8000`.

### 2. Iniciar o Frontend (Streamlit)

Abra um **novo terminal**, navegue até o diretório `KlarosAI/` e ative o mesmo ambiente virtual:

```bash
cd KlarosAI/
source venv_klarosai/bin/activate  # No Windows: .\venv_klarosai\Scripts\activate
streamlit run frontend.py
```

Este comando iniciará a aplicação Streamlit. Uma nova aba no seu navegador será aberta automaticamente, exibindo a interface do KlarosAI (geralmente em `http://localhost:8501`).

## Uso da Aplicação

### 1. Upload de Documentos

Na interface do Streamlit, utilize o botão "Carregar Documento (PDF, TXT, DOCX)" na barra lateral para fazer upload dos seus arquivos. O sistema indicará o status da ingestão. Uma vez concluída, os documentos estarão disponíveis para consulta.

### 2. Interação via Chat

Após a ingestão dos documentos, digite suas perguntas no campo de texto na parte inferior da tela de chat e pressione Enter. A IA processará sua pergunta e fornecerá uma resposta baseada nos documentos que você carregou. Se a IA utilizar trechos específicos, você poderá expandir a seção "Documentos de Origem Utilizados" para ver os detalhes da fonte.

## Considerações e Próximos Passos

- **Otimização de Embeddings:** Para grandes volumes de documentos, a escolha e otimização do modelo de embeddings podem ser cruciais para a performance e relevância das respostas.
- **Gerenciamento de Erros:** Embora a aplicação lide com alguns erros de ingestão, um tratamento de erro mais robusto e logging detalhado podem ser implementados para ambientes de produção.
- **Autenticação e Autorização:** Para uso em ambientes corporativos, a adição de um sistema de autenticação e autorização seria fundamental para controlar o acesso aos documentos e à API.
- **Escalabilidade:** Para lidar com um número crescente de usuários e documentos, considerar a implantação em serviços de nuvem (AWS, GCP, Azure) e o uso de soluções de banco de dados vetoriais mais escaláveis (e.g., Pinecone, Weaviate) pode ser necessário.
- **Interface do Usuário:** A interface do Streamlit é funcional, mas pode ser aprimorada com mais recursos de UX/UI para uma experiência mais rica.



