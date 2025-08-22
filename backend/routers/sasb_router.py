from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List, Optional
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import json
import re
from key import key
from services.draft_store import save_draft, load_draft
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

router = APIRouter()
print("✅ sasb_router loaded")

CHUNK_PATH = Path(__file__).resolve().parent.parent / "SASB/sasb_chunks.xlsx"
TABLE_DIR = Path(__file__).resolve().parent.parent / "SASB/sasb_tables"

chunk_df = pd.read_excel(CHUNK_PATH)
chunk_df.columns = chunk_df.columns.str.strip()

class FetchDataRequest(BaseModel):
    topic: str
    company: str
    department: Optional[str] = ""
    history: Optional[List[dict]] = []

@router.post("/fetch-data")
def fetch_data(req: FetchDataRequest):
    filtered = chunk_df[chunk_df["title"].str.strip() == req.topic]
    chunks = filtered["chunk"].tolist()
    pages = set(filtered["page"].dropna().astype(int).tolist())

    table_htmls, table_texts, table_paths = [], [], []
    for page in sorted(pages):
        for path in TABLE_DIR.glob(f"page{page}_table*.html"):
            try:
                soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
                table = soup.find("table")
                if table:
                    table_htmls.append(str(table))
                    table_texts.append(soup.get_text(separator="\n", strip=True))
                    table_paths.append(str(path))
            except Exception as e:
                print(f"❌ 표 파싱 실패: {path} → {e}")

    return {
        "topic": req.topic,
        "company": req.company,
        "department": req.department,
        "history": req.history,
        "chunk_count": len(chunks),
        "chunks": chunks,
        "table_htmls": table_htmls,
        "table_paths": table_paths,
        "table_texts": table_texts,
        "pages": sorted(pages)
    }

class InferDataRequest(BaseModel):
    topic: str
    chunks: List[str]
    table_texts: List[str]

def parse_markdown_to_fields(markdown: str):
    lines = markdown.splitlines()
    results, current = [], {}
    for line in lines:
        line = line.strip()
        if re.match(r"^\d+\.\s+\*{2,3}(.+?)\*{2,3}", line):
            if current: results.append(current); current = {}
            current["항목"] = re.match(r"^\d+\.\s+\*{2,3}(.+?)\*{2,3}", line).group(1).strip()
        elif "단위" in line:
            current["단위"] = line.split(":", 1)[-1].strip()
        elif "연도" in line:
            raw = line.split(":", 1)[-1].strip()
            years = set()
            for part in re.split(r"[,\s]+", raw):
                if "~" in part:
                    try:
                        s, e = map(int, part.split("~"))
                        years.update(range(s, e + 1))
                    except: continue
                elif part.isdigit(): years.add(int(part))
            current["연도"] = sorted(years)
        elif "설명" in line:
            current["설명"] = line.split(":", 1)[-1].strip()
    if current: results.append(current)
    for item in results:
        item.setdefault("단위", ""); item.setdefault("연도", []); item.setdefault("설명", "")
    return results

@router.post("/infer-required-data")
def infer_required_data(req: InferDataRequest):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3, openai_api_key=key["OPENAI_API_KEY"])

    system = SystemMessage(content="너는 ESG 보고서 작성 지원 도우미야. 지표 설명 텍스트와 표를 참고해서 어떤 입력값이 필요한지 추론해줘. 출력은 마크다운 목록 형식이며, 각 항목에 항목명/단위/연도/설명을 포함해.")
    user = HumanMessage(content=f"[지표 ID: {req.topic}]\n\n" + "\n".join(req.chunks) + "\n\n표 내용:\n" + "\n".join(req.table_texts))

    try:
        res = llm.invoke([system, user])
        return {
            "topic": req.topic,
            "required_data": res.content,
            "required_fields": parse_markdown_to_fields(res.content)
        }
    except Exception as e:
        print("❌ infer-required-data 실패:", e)
        return {"topic": req.topic, "required_data": "⚠️ 오류"}

class DraftRequest(BaseModel):
    topic: str
    inputs: dict
    chunks: List[str]
    table_texts: List[str]
    improvement: Optional[str] = None

@router.post("/generate-draft")
def generate_draft(req: DraftRequest):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3, max_tokens=1500, openai_api_key=key["OPENAI_API_KEY"])

    def format_inputs(inputs: dict) -> str:
        lines = []
        for 항목, 내용 in inputs.items():
            if isinstance(내용, dict):
                if "url" in 내용:
                    lines.append(f"- {항목}: ![이미지]({내용['url']})")
                else:
                    for 키, 값 in 내용.items():
                        if isinstance(val := 값, dict) and "url" in val:
                            lines.append(f"- {키}년 {항목}: ![이미지]({val['url']})")
                        else:
                            lines.append(f"- {키}년 {항목}: {val}")
            else:
                lines.append(f"- {항목}: {내용}")
        return "\n".join(lines)

    formatted_inputs = format_inputs(req.inputs)
    user = HumanMessage(content=f"[지표 ID: {req.topic}]\n\n지표 설명 텍스트:\n" + "\n".join(req.chunks) +
                        "\n\n작성 가이드 표:\n" + "\n".join(req.table_texts) +
                        "\n\n사용자 입력 데이터:\n" + formatted_inputs +
                        "\n\n개선 노력 및 활동:\n" + (req.improvement or ""))

    system = SystemMessage(content="너는 ESG 보고서를 작성하는 전문 컨설턴트야. 지표 설명과 표, 입력값을 바탕으로 서술형 초안을 생성해줘.")

    try:
        res = llm.invoke([system, user])
        return {"draft": res.content.strip()}
    except Exception as e:
        print("❌ 초안 생성 실패:", e)
        return {"draft": "⚠️ 초안 생성 오류"}