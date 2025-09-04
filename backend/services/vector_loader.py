from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings
import os
from pathlib import Path

# ✅ 임베딩 객체 생성
embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))

def load_vectorstore(index_name: str):
    # Qdrant 클라우드 연결
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        raise ValueError("❌ QDRANT_URL과 QDRANT_API_KEY 환경변수가 필요합니다.")
    
    # Qdrant 클라이언트 생성
    client = Qdrant(
        url=qdrant_url,
        api_key=qdrant_api_key,
        collection_name=index_name,
        embeddings=embedding
    )
    
    return client
