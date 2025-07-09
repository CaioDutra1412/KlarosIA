import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Configuração do LLM (Large Language Model)

def get_llm():
    """
    Retorna uma instância do Large Language Model (LLM) configurado.
    Por padrão, usa a API do Google Gemini.
    """
    # Para usar o Google Gemini, certifique-se de que GOOGLE_API_KEY está definida no seu .env
    # Troque para um dos modelos listados no seu testAPI.py que suporte 'generateContent'.
    # Usando o 'gemini-2.5-flash' para melhor performance e custo-benefício para assistentes.
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", # <--- Alterado para 'gemini-2.5-flash'
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7 # Ajuste para controlar a criatividade da resposta (0.0 a 1.0)
    )
    return llm

# Exemplo de como usar o LLM (apenas para demonstração/teste interno)
if __name__ == "__main__":
    print("Testando a configuração do LLM do Google Gemini...")
    try:
        test_llm = get_llm()
        response = test_llm.invoke("Olá, qual é o seu propósito?")
        print(f"Resposta do LLM: {response.content}")
    except Exception as e:
        print(f"Erro ao testar o LLM: {e}")
        print("Certifique-se de que sua GOOGLE_API_KEY está correta e que o modelo especificado está disponível.")