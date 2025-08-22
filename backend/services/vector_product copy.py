import pandas as pd
from pathlib import Path
from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os

# ✅ .env 파일에서 OPENAI_API_KEY 불러오기
load_dotenv()

# ✅ 경로 설정
CHUNK_PATH = Path("sasb_chunks.xlsx")
VECTORSTORE_PATH = Path("vectorstores/sasb")

# ✅ 엑셀 로드
print("📄 청크 미리보기 로딩 중...")
df = pd.read_excel(CHUNK_PATH)

# ✅ LangChain 문서 객체로 변환
documents = []
for _, row in df.iterrows():
    if pd.isna(row["text"]):
        continue  # NaN 청크는 건너뜀

    metadata = {
        "chunk_id": row["chunk_id"],
        "title": row["title"],
        "pages": row["pages"],
        "tables": row["tables"],
    }
    documents.append(Document(page_content=str(row["text"]), metadata=metadata))


# ✅ 임베딩 모델 설정
print("🔍 임베딩 생성 중...")
embedding = OpenAIEmbeddings()

# ✅ FAISS 벡터스토어 생성 및 저장
print("💾 FAISS 벡터스토어 저장 중...")

if VECTORSTORE_PATH.exists() and (VECTORSTORE_PATH / "index.faiss").exists():
    print("⚠️ 이미 벡터스토어가 존재합니다. 재임베딩하지 않습니다.")
    exit()

VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
vectorstore = FAISS.from_documents(documents, embedding)
vectorstore.save_local(str(VECTORSTORE_PATH))
print(f"✅ 저장 완료: {VECTORSTORE_PATH}/index.faiss")
