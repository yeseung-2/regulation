from fastapi import APIRouter
from pydantic import BaseModel
from services.vector_loader import load_vectorstore
from pathlib import Path
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import re
from dotenv import load_dotenv
from key import key
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from difflib import SequenceMatcher
from fastapi.responses import FileResponse
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from pathlib import Path
import uuid
from typing import List, Optional
import requests
from .models.draft_model import Draft
from pymongo import MongoClient
import os


load_dotenv()

router = APIRouter()
print("✅ template_router loaded")

client = MongoClient(os.getenv("MONGO_URI"))
db = client["esg_templates_db"]
drafts = db["drafts"]

def call_hyperclova_llm(system_msg: SystemMessage, human_msg: HumanMessage) -> str:
    prompt = f"{system_msg.content.strip()}\n\n{human_msg.content.strip()}"

    headers = {
        "Authorization": f"Bearer {key['HUGGINGFACE_API_TOKEN']}",
        "Content-Type": "application/json"
    }

    url = "https://api-inference.huggingface.co/models/naver-hyperclovax/HyperCLOVAX-SEED-Text-Base-3B"
    payload = {
        "inputs": prompt
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()[0]["generated_text"]
    except Exception as e:
        print(f"❌ Hugging Face LLM 호출 실패: {e}")
        return "⚠️ 모델 호출 중 오류가 발생했습니다."
    
class HistoryItem(BaseModel):
    date: str
    description: str

class TemplateRequest(BaseModel):
    company: str
    topic: str
    department: Optional[str] = ""
    history: Optional[List[HistoryItem]] = []

class HtmlToPdfRequest(BaseModel):
    topic: str
    company: str
    department: str
    html: str
    history: List[HistoryItem]

@router.post("/generate")
def generate_template(req: TemplateRequest):
    from difflib import SequenceMatcher

    vectorstore = load_vectorstore("esg_templates")

    # ✅ 청크 필터링 및 정렬
    all_docs = list(vectorstore.docstore._dict.values())
    filtered = [d for d in all_docs if d.metadata.get("title") == req.topic]
    if not filtered:
        return {"template": "❌ 해당 주제에 대한 규정안이 없습니다."}
    filtered = sorted(filtered, key=lambda d: d.metadata.get("chunk_id", ""))

    # ✅ 표 로딩
    table_paths, table_htmls, table_texts, seen = [], [], [], set()
    max_table_count = len(table_htmls)
    print(f"맥스테이블:{max_table_count}")
    for doc in filtered:
        t_raw = doc.metadata.get("tables", [])
        t_list = eval(t_raw) if isinstance(t_raw, str) else t_raw
        for path in t_list:
            if path not in seen:
                seen.add(path)
                table_paths.append(path)
                try:
                    soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
                    h3 = soup.find("h3")
                    table = soup.find("table")
                    if table:
                        combined = str(h3) + "\n" if h3 else ""
                        combined += str(table)
                        table_htmls.append(combined)
                        table_texts.append(soup.get_text(separator="\n", strip=True))
                except Exception as e:
                    print(f"❌ 표 읽기 실패: {path} → {e}")

    # ✅ LLM 준비 (GPT는 마커/표 출력 금지)
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.2,
        max_tokens=2048,
        openai_api_key=key["OPENAI_API_KEY"]
    )
    system_msg = SystemMessage(content=f"""\
너는 ESG 규정안 문서를 정돈하는 도우미야.

📌 반드시 아래 지침을 따라야 해:

1. 문서의 제목, 조문 구조, 항목 순서를 바꾸거나 요약하지 마.
2. 각 표가 들어갈 위치에 정확히 `[[TABLE_N]]` 마커를 포함시켜. 절대 누락하거나 수정하지 마.
3. 단, 사용할 수 있는 표 마커는 `[[TABLE_1]]`부터 `[[TABLE_{max_table_count}]]`개 까지만이야. 그 이상은 절대 만들지 마.
4. 표 HTML(<table>, <tr>, <td> 등)은 절대 본문에 출력하지 마. 마커만 넣어.
5. 청크가 조문이나 문단 중간에서 끊겨서 어색한 경우, 자연스럽게 이어지도록 문장을 정리해줘.
6. 문장 순서나 의미는 바꾸지 말고, 끊김ssssssss이 느껴지는 부분만 자연스럽게 보완해.
7. 조문은 1조, 2조, 3조 ... 숫자가 끊김 없이 이어지도록 정돈해.
8. 문단 간 줄바꿈이나 들여쓰기는 보기 좋게 정리해도 좋아.
""")

    # ✅ 청크 그룹 나누기
    CHUNKS_PER_REQUEST = 10
    chunk_groups = [
        filtered[i:i + CHUNKS_PER_REQUEST]
        for i in range(0, len(filtered), CHUNKS_PER_REQUEST)
    ]
    print(f"📚 {len(chunk_groups)}개 그룹으로 분할됨 (그룹당 최대 {CHUNKS_PER_REQUEST}개)")

    # ✅ 그룹별 GPT 호출
    results = []
    for group_idx, group in enumerate(chunk_groups):
        chunk_ids = [d.metadata.get("chunk_id", "?") for d in group]
        print(f"🔹 그룹 {group_idx+1}: chunk_ids = {chunk_ids}")

        group_text = "\n\n".join([d.page_content for d in group])
        print(f"📄 그룹 {group_idx+1} 텍스트 시작:\n{group_text[:300]}...\n")

        group_text = (
            group_text.replace("[기업명]", req.company)
                      .replace("{회사명}", req.company)
                      .replace("기업명 은", f"{req.company}은")
                      .replace("㈜△△△사", req.company)
                      .replace("기업명", req.company)
        )
        group_text = re.sub(r"\n{2,}", "\n\n", group_text)

        human_msg = HumanMessage(content=f"""
📄 규정안 원문:
{group_text}
""")
        try:
            response = llm.invoke([system_msg, human_msg])
            print(f"📤 그룹 {group_idx+1} 응답 길이: {len(response.content)}")
            results.append(response.content)
        except Exception as e:
            print(f"❌ GPT 그룹 {group_idx+1} 호출 실패:", e)
            results.append("⚠️ GPT 응답 실패 (일부)")

    # ✅ GPT가 실수로 table을 넣었을 경우 제거
    cleaned_results = []
    for r in results:
        for html in table_htmls:
            r = r.replace(html, "")
        cleaned_results.append(r)

    output_text = "\n\n".join(cleaned_results)

    # ✅ 마커 삽입 함수
    def insert_marker_safely(text, marker, table_text):
        if marker in text:
            print(f"⚠️ 마커 {marker} 이미 존재 → 삽입 생략")
            return text

        paragraphs = text.split("\n\n")
        best_score, best_idx = 0, -1
        for i, para in enumerate(paragraphs):
            score = SequenceMatcher(None, para, table_text).ratio()
            if score > best_score:
                best_score, best_idx = score, i

        if best_score > 0.5:
            print(f"✅ 유사도 {best_score:.2f} → 마커 {marker} 삽입 (문단 {best_idx})")
            paragraphs[best_idx] += f"\n\n{marker}"
        else:
            print(f"⚠️ 유사 문단 없음 → 마커 {marker} 본문 끝에 삽입")
            paragraphs.append(marker)

        return "\n\n".join(paragraphs)

    # ✅ 마커 삽입 (백엔드 전담)
    for i, table_text in enumerate(table_texts):
        marker = f"[[TABLE_{i+1}]]"
        if marker not in output_text:
            print(f"❌ 마커 {marker} 없음 → 삽입 시도")
            output_text = insert_marker_safely(output_text, marker, table_text)
        else:
            print(f"✅ 마커 {marker} 이미 존재 → 삽입 생략")

    # ✅ 마커를 실제 table로 치환
    for i, html in enumerate(table_htmls):
        marker = f"[[TABLE_{i+1}]]"
        if marker in output_text:
            output_text = output_text.replace(marker, html)
            print(f"✅ 마커 {marker} → <table> 삽입 완료")
        else:
            print(f"⚠️ 마커 {marker} 없음 → <table> 삽입 생략")

    return {
        "template": output_text,
        "topic": req.topic,
        "company": req.company,
        "department": req.department,
        "history": req.history,
        "chunk_count": len(filtered),
        "table_html": "",
        "table_paths": table_paths,
    }

@router.post("/generate-pdf")
def generate_template_pdf(req: TemplateRequest):  # 이미 존재할 경우 생략 가능
    result = generate_template(req)
    html_content = result["template"]

    # 템플릿 렌더링
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("esg_template.html")
    rendered_html = template.render(
        topic=req.topic,
        company=req.company,
        department=req.department,
        date=datetime.now().strftime("%Y.%m.%d"),
        content=req.html,
        history=req.history
    )

    # PDF 저장 경로 설정
    output_dir = Path("static/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4()}.pdf"
    pdf_path = output_dir / file_name

    # PDF 생성
    HTML(string=rendered_html).write_pdf(str(pdf_path))

    # 사용자에게 파일 다운로드로 응답
    return FileResponse(
        path=str(pdf_path),
        filename=f"{req.company}_{req.topic}.pdf",
        media_type="application/pdf"
    )

@router.post("/download-pdf-from-html")
def download_pdf_from_html(req: HtmlToPdfRequest):
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("esg_template.html")
    rendered_html = template.render(
        topic=req.topic,
        company=req.company,
        department=req.department,  
        history=req.history,       
        content=req.html
    )


    output_dir = Path("static/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4()}.pdf"
    pdf_path = output_dir / file_name
    HTML(string=rendered_html).write_pdf(str(pdf_path))

    return FileResponse(
        path=str(pdf_path),
        filename=f"{req.company}_{req.topic}.pdf",
        media_type="application/pdf"
    )

@router.get("/list-drafts")
def list_drafts(user_id: str):
    items = drafts.find({"user_id": user_id}, {"_id": 0, "company": 1, "topic": 1, "timestamp": 1, "department": 1})
    return list(items)

@router.post("/save-draft")
def save_draft(draft: Draft):
    draft_dict = draft.dict()
    draft_dict["timestamp"] = datetime.utcnow()
    if "is_final" not in draft_dict:
        draft_dict["is_final"] = False

    drafts.update_one(
        {"user_id": draft.user_id, "topic": draft.topic},
        {"$set": draft_dict},
        upsert=True
    )
    return {"message": "✅ 초안 저장 완료"}

@router.get("/load-draft")
def load_draft(user_id: str, topic: str):
    print(f"📥 load-draft 요청: user_id={user_id}, topic={topic}")
    draft = drafts.find_one({"user_id": user_id, "topic": topic}, {"_id": 0})
    if draft:
        return draft
    return {"message": "❌ 해당 초안 없음"}

@router.delete("/delete-draft")
def delete_draft(user_id: str, topic: str):
    result = drafts.delete_one({"user_id": user_id, "topic": topic})
    if result.deleted_count == 1:
        return {"message": "✅ 초안 삭제 완료"}
    return {"message": "❌ 해당 초안 없음"}