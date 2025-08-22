import pandas as pd
from pathlib import Path
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings  # ✅ 최신 버전
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os

# ✅ .env 파일 로드
load_dotenv()

# ✅ 경로 설정
CHUNK_PATH = Path("sasb_chunks.xlsx")  # sasb용 청크 미리보기
VECTORSTORE_PATH = Path("vectorstores/sasb")  # 저장할 벡터스토어 경로

# ✅ 엑셀 로드
print("📄 청크 미리보기 로딩 중...")
df = pd.read_excel(CHUNK_PATH)

# ✅ LangChain 문서 객체로 변환
documents = []
for _, row in df.iterrows():
    if pd.isna(row["text"]):
        continue

    metadata = {
        "chunk_id": row["chunk_id"],
        "title": row["title"],
        "pages": row["pages"],
        "tables": row["tables"],
        "images": row["images"]
    }
    documents.append(Document(page_content=str(row["text"]), metadata=metadata))

# ✅ 임베딩 모델 설정
print("🔍 임베딩 생성 중...")
embedding = OpenAIEmbeddings()

# ✅ 벡터스토어 생성 (배치 처리로 토큰 초과 방지)
def batch(iterable, n=1000):
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]

vectorstore = None
for i, doc_batch in enumerate(batch(documents, n=100)):
    print(f"🔢 배치 {i+1} 처리 중... ({len(doc_batch)}개 청크)")
    if vectorstore is None:
        vectorstore = FAISS.from_documents(doc_batch, embedding)
    else:
        new_store = FAISS.from_documents(doc_batch, embedding)
        vectorstore.merge_from(new_store)

# ✅ 저장
print("💾 FAISS 벡터스토어 저장 중...")
VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
vectorstore.save_local(str(VECTORSTORE_PATH))
print(f"✅ 저장 완료: {VECTORSTORE_PATH}/index.faiss")
