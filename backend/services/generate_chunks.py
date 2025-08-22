import os
import argparse
from pathlib import Path
import pandas as pd
from langchain.docstore.document import Document
import nltk
import json

nltk.download("punkt")
from nltk.tokenize import sent_tokenize

def load_text_pages(text_dir: Path):
    text_pages = {}
    for txt_file in sorted(text_dir.glob("page*.txt")):
        try:
            page_num = int(txt_file.stem.replace("page", ""))
            with open(txt_file, encoding="utf-8") as f:
                text_pages[page_num] = f.read().strip()
        except:
            continue
    return text_pages

def split_text_by_sentences(text, max_chars=500, overlap_chars=100):
    sents = sent_tokenize(text)
    chunks = []
    current = ""

    for sent in sents:
        if len(current) + len(sent) > max_chars:
            chunks.append(current.strip())
            current = current[-overlap_chars:] + " " + sent
        else:
            current += " " + sent
    if current:
        chunks.append(current.strip())
    return chunks

def make_gri_chunks(base_dir: Path, max_chars=500, overlap_chars=100):
    text_dir = base_dir / "text"
    table_dir = base_dir / "tables_gpt"
    
    if not text_dir.exists():
        print(f"❌ 텍스트 없음: {text_dir}")
        return []

    # 텍스트 로드
    text_data = load_text_pages(text_dir)
    if not text_data:
        print(f"⚠️ 빈 텍스트 파일: {base_dir}")
        return []
    text_content = "\n".join(text_data.values())

    # 표 로드
    tables = []  # 표가 없어도 괜찮음
    table_files = []
    if table_dir.exists():
        for html_file in sorted(table_dir.glob("*.html")):
            table_files.append(str(html_file))
            with open(html_file, encoding="utf-8") as f:
                tables.append(f.read())

    full_text = text_content + "\n\n" + "\n\n".join(tables)
    split_chunks = split_text_by_sentences(full_text, max_chars=max_chars, overlap_chars=overlap_chars)

    documents = []
    for i, chunk in enumerate(split_chunks):
        documents.append(Document(
            page_content=chunk,
            metadata={
                "chunk_id": f"{base_dir.name}_{i+1:02}",
                "title": base_dir.name,
                "tables": table_files,
                "images": [],
                "pages": list(text_data.keys())
            }
        ))
    return documents

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="엑셀 미리보기 저장 위치")
    args = parser.parse_args()

    EXTRACTED_ROOT = Path("extracted/sasb")
    all_documents = []

    for sasb_folder in sorted(EXTRACTED_ROOT.iterdir()):
        if not sasb_folder.is_dir():
            continue

        print(f"📂 처리 중: {sasb_folder.name}")
        docs = make_gri_chunks(sasb_folder)
        all_documents.extend(docs)

    df = pd.DataFrame([{
        "chunk_id": doc.metadata["chunk_id"],
        "title": doc.metadata["title"],
        "tables": doc.metadata["tables"],
        "images": doc.metadata["images"],
        "pages": doc.metadata["pages"],
        "text": doc.page_content
    } for doc in all_documents])

    df.to_excel(args.output, index=False)
    print(f"✅ 완료: {args.output} 저장")
