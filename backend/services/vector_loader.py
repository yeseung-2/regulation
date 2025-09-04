from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
from pathlib import Path

# ✅ 임베딩 객체 생성
    embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

def load_vectorstore(index_name: str):
    path = Path(f"vectorstores/{index_name}")
    if not path.exists():
        raise FileNotFoundError(f"❌ 벡터스토어 경로 없음: {path}")
    
    return FAISS.load_local(str(path), embedding, allow_dangerous_deserialization=True)
