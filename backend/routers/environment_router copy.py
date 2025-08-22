from fastapi import APIRouter, Body, Request
from pydantic import BaseModel
from services.vector_loader import load_vectorstore
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Optional
import json
from key import key
import re
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from services.draft_store import save_draft, load_draft
from fastapi import HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
import difflib
from difflib import SequenceMatcher
from typing import Dict, Any
from services.draft_store import save_input_data, load_input_data
from services.db import draft_collection, input_collection 


router = APIRouter()
print("✅ environment_router (fetch-only) loaded")

TABLE_DIR = Path(__file__).resolve().parent.parent / "extracted/2025_Sustainable_Management_Manual_split/tables"

class DeleteDraftRequest(BaseModel):
    topic: str
    company: str

class HistoryItem(BaseModel):
    date: str
    description: str

class FetchDataRequest(BaseModel):
    topic: str
    company: Optional[str] = ""
    department: Optional[str] = ""
    history: Optional[str] = ""
# ✅ 작성 내용 블록 추출 함수 (추가)
def extract_작성내용(chunks: List[str]) -> str:
    lines = "\n".join(chunks).splitlines()
    capture = False
    result = []

    for line in lines:
        stripped = line.strip()
        if "작성 내용" in stripped:
            capture = True
        elif stripped.startswith("▶") or stripped.startswith("KBZ-"):
            if capture:
                break
        if capture:
            result.append(stripped)

    return "\n".join(result).strip()

# 입력값 임시저장 모델
class SaveInputsRequest(BaseModel):
    topic: str
    company: str
    inputs: dict
    table: dict
    improvement: Optional[str] = ""



@router.post("/save-inputs")
def save_inputs(req: SaveInputsRequest):
    data = {
        "inputs": req.inputs,
        "table": req.table,
        "improvement": req.improvement,
    }
    save_input_data(f"{req.topic}__input", req.company, data)
    return {"message": "✅ 입력값 임시 저장됨"}

@router.get("/load-inputs")
def load_inputs(topic: str, company: str):
    data = load_input_data(f"{topic}__input", company)
    return {"inputs": data or {}}

@router.post("/fetch-data")
def fetch_data(req: FetchDataRequest):
    from services.vector_loader import load_vectorstore
    from bs4 import BeautifulSoup
    import json

    # ✅ 1. 벡터스토어 로딩
    vectorstore = load_vectorstore("esg_Manual")
    all_docs = list(vectorstore.docstore._dict.values())

    # ✅ 2. topic으로 필터링
    filtered = [
        doc for doc in all_docs
        if req.topic in (doc.metadata.get("title") or "")
    ]
    filtered = sorted(filtered, key=lambda d: d.metadata.get("chunk_id", ""))

    # ✅ 3. 관련 페이지 추출
    pages = set()
    for doc in filtered:
        raw_pages = doc.metadata.get("pages", [])
        if isinstance(raw_pages, list):
            pages.update(raw_pages)
        elif isinstance(raw_pages, int):
            pages.add(raw_pages)
        elif isinstance(raw_pages, str):
            try:
                parsed = json.loads(raw_pages) if raw_pages.startswith("[") else eval(raw_pages)
                if isinstance(parsed, list):
                    pages.update(parsed)
                elif isinstance(parsed, int):
                    pages.add(parsed)
            except Exception as e:
                print(f"❌ pages 파싱 실패: {raw_pages} → {e}")

    # ✅ 4. 표 로딩 (여러 개 대응)
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

    print("📄 추출된 페이지:", sorted(pages))
    print("📊 로딩된 표 개수:", len(table_htmls))

    # ✅ 5. 최종 응답 반환
    return {
        "topic": req.topic,
        "company": req.company,
        "department": req.department,
        "history": req.history,
        "chunk_count": len(filtered),
        "chunks": [doc.page_content for doc in filtered],
        "table_htmls": table_htmls,        # ✅ 배열 형태로 반환
        "table_paths": table_paths,
        "table_texts": table_texts,
        "pages": sorted(pages)
    }



from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

class InferDataRequest(BaseModel):
    topic: str
    chunks: List[str]
    table_texts: List[str]

from typing import List, Dict, Any
import re

def parse_markdown_to_fields(markdown: str) -> List[Dict[str, Any]]:
    rows = []
    lines = markdown.strip().splitlines()
    current_field = {}

    for line in lines:
        line = line.strip()

        # ✅ 1. 항목명 감지 (별표 유무 모두 처리)
        match_item = re.match(r"^\d+\.\s+(?:\*\*)?(.+?)(?:\*\*)?$", line)
        if match_item:
            if current_field and "항목" in current_field:
                rows.append(current_field)
            current_field = {"항목": match_item.group(1).strip()}
            continue

        # ✅ 2. 단위 감지
        if "**단위**" in line:
            match = re.search(r"\*\*단위\*\*:\s*(.+)", line)
            if match:
                current_field["단위"] = match.group(1).strip()

        # ✅ 3. 연도 감지
        elif "**연도별 데이터**" in line:
            match = re.search(r"\*\*연도별 데이터\*\*:\s*(.+)", line)
            if match:
                current_field["연도"] = match.group(1).strip()

        # ✅ 4. 설명 감지
        elif "**설명**" in line:
            match = re.search(r"\*\*설명\*\*:\s*(.+)", line)
            if match:
                current_field["설명"] = match.group(1).strip()

    # ✅ 마지막 항목 누락 방지
    if current_field and "항목" in current_field:
        rows.append(current_field)

    return rows


def clean_and_split_fieldnames(text: str) -> List[str]:
    # 줄바꿈 제거, 괄호 내용 제거, 특수문자 제거
    text = text.replace("\\n", " ").replace("\n", " ")
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"[^\w\sㄱ-ㅎ가-힣a-zA-Z0-9]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 의미 있는 단위로 분할 (예: 4~6자 이상 한글 묶음)
    candidates = re.findall(r"[가-힣]{3,10}(?:\s[가-힣]{2,10})*", text)

    # 필터링: 너무 짧은 건 제거
    return [c.strip() for c in candidates if len(c.strip()) >= 4]


def extract_table_fieldnames(table_texts: List[str]) -> List[str]:
    """HTML + 텍스트 기반 표에서 항목명 추출 (줄바꿈, 괄호 등 제거 포함)"""
    def clean_fieldname(text: str) -> str:
        # 줄바꿈 제거 후 괄호 내용, 특수문자 제거
        text = text.replace("\n", " ")  # 줄바꿈 공백 처리
        text = re.sub(r"\(.*?\)", "", text)  # 괄호 안 제거
        text = re.sub(r"[^\w\sㄱ-ㅎ가-힣a-zA-Z0-9]", "", text)  # 특수문자 제거
        text = re.sub(r"\s+", " ", text).strip()  # 중복 공백 정리
        return text

    fieldnames = set()

    for html_or_text in table_texts:
        # 1️⃣ HTML 기반 추출
        try:
            soup = BeautifulSoup(html_or_text, "html.parser")
            table = soup.find("table")
            if table:
                thead = table.find("thead")
                if thead:
                    header_row = thead.find("tr")
                    if header_row:
                        for cell in header_row.find_all(["th", "td"]):
                            text = clean_fieldname(cell.get_text(strip=True))
                            if text and len(text) <= 50:
                                fieldnames.add(text)
                else:
                    tbody = table.find("tbody")
                    if tbody:
                        for row in tbody.find_all("tr"):
                            cells = row.find_all(["td", "th"])
                            if cells:
                                first_col = clean_fieldname(cells[0].get_text(strip=True))
                                if first_col and len(first_col) <= 50:
                                    fieldnames.add(first_col)
                continue  # HTML 추출 성공 시 텍스트 추출 생략
        except:
            pass

        # 2️⃣ 텍스트 기반 추출 (줄 하나에 여러 항목이 붙은 경우 분리 처리)
        lines = html_or_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line or len(line) < 4:
                continue
            if line.startswith("구분") or line.startswith("단위"):
                continue
            if any(unit in line for unit in ["톤", "TJ", "%", "tCO2eq", "백만원"]) and any(char.isdigit() for char in line):
                continue
            if re.search(r"\d{4}", line):  # 연도 포함 줄 제외
                continue

            # ✅ 의미 있는 항목 덩어리들을 분리해 추출
            fieldname_candidates = clean_and_split_fieldnames(line)
            for f in fieldname_candidates:
                if len(f) >= 3:
                    fieldnames.add(f)


    return sorted(fieldnames)

def is_redundant(llm_field: str, table_fields: List[str], threshold=0.8) -> bool:
    llm_norm = normalize(llm_field)

    for table_field in table_fields:
        table_norm = normalize(table_field)

        # 1. 기존 유사도 기준
        ratio = difflib.SequenceMatcher(None, llm_norm, table_norm).ratio()
        if ratio >= threshold:
            return True

        # ✅ 2. 포함 관계 기준 (한쪽이 다른 쪽에 포함되면 중복으로 간주)
        if llm_norm in table_norm or table_norm in llm_norm:
            return True

    return False


def normalize(text: str) -> str:
    return re.sub(r"[\s()%/+\-.,]", "", text).lower()

def is_similar(a: str, b: str, threshold=0.8) -> bool:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio() >= threshold

def remove_duplicate_fields(required_fields, table_fieldnames):
    return [
        field for field in required_fields
        if all(not is_similar(field["항목"], tf) for tf in table_fieldnames)
    ]


@router.post("/infer-required-data")
def infer_required_data(req: InferDataRequest):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        max_tokens=1024,
        openai_api_key=key["OPENAI_API_KEY"]
    )

    # 🧠 시스템 지침
    system = SystemMessage(content="""
    너는 ESG 보고서 작성 지원 도우미야.

    사용자가 제공한 지표 설명(청크), 작성 가이드, 표 예시를 바탕으로,
    **이 지표를 작성하기 위해 반드시 입력받아야 할 데이터를** 정리해줘.

    📌 특히 주의할 점:
    - 반드시 **'작성 내용' 항목**을 우선적으로 분석해서, 해당 내용을 보고하기 위해 필요한 입력 항목을 빠짐없이 추출해줘.
    - 작성 내용에 있는 항목은 표에 없어도 반드시 포함해.
    - **표는 참고 자료일 뿐이야. 작성 내용이 중요해.**

    📛 또한, 표에 이미 존재하는 항목명과 90% 이상 유사한 항목은 추천하지 마.
    - 예: 표에 ‘근로손실재해율’이 있다면, ‘근로손실재해율 (LTIFR)’처럼 중복될 수 있는 항목도 생략해.
    - 표 항목과 유사성 판단 시 문장 전체의 의미를 기준으로 해.
                           
    🧠 작성 내용이 예시 형식(예: '정책, 절차, 활동 등')이라 하더라도,
    그 항목들을 실제 입력 필드로 바꿔서 구체적으로 정리해줘.

    예를 들어, ‘법적 보호종 현황’이 작성 내용에 있으면 
    → 입력 필드: “법적 보호종 존재 여부”, “보호종명”, “서식지 위치” 등으로 세분화해줘.


    📋 출력 형식 (이 형식을 반드시 지켜야 해! 아래 포맷 외의 응답은 금지야.)
    1. 필요한 데이터 항목명 (단위 포함 금지)
    2. 단위 (가능하면 추정)
    3. 어떤 연도별 데이터가 필요한지 (예: 2021~2023)
    4. 설명 (왜 필요한지 간단히)
                           
    예:
    1. **총 온실가스 배출량**
    - **단위**: tCO2eq
    - **연도별 데이터**: 2021~2023
    - **설명**: 조직의 온실가스 배출 총량을 파악하기 위해 필요함

    지표를 보고하기 위해 **입력 폼을 만든다고 생각하고**, 구체적이고 누락 없이 추천해줘.
    """)

    # ✅ 기존 청크 + 작성 내용 추출 + 표 텍스트
    chunk_text = "\n".join(req.chunks)
    table_text = "\n".join(req.table_texts)
    작성_블록 = extract_작성내용(req.chunks)

    print("📝 작성 내용 블록:\n", 작성_블록)

    # ✅ 사용자 메시지 구성 (📝 작성 내용 블록 추가됨)
    user = HumanMessage(content=f"""[지표 ID: {req.topic}]

📘 지표 설명 텍스트:
{chunk_text}

📝 작성 내용 요약 (작성 내용에 반드시 기반하여 입력 항목을 추천해야 함):
{작성_블록}

📊 표 내용 (참고용):
{table_text}
""")

    # ✅ 표 항목명 추출
    table_fieldnames = extract_table_fieldnames(req.table_texts)

    try:
        response = llm.invoke([system, user])
        print("📤 LLM 응답 원문:\n", response.content)
        parsed_fields = parse_markdown_to_fields(response.content)

        # ✅ 중복 필터링 적용
        filtered_fields = [f for f in parsed_fields if "항목" in f and not is_redundant(f["항목"], table_fieldnames)]
        print("✅ 필터링 후 남은 항목:", [f["항목"] for f in filtered_fields])

        # ✅ 로그 추가 (이 아래 줄들)
        print("📌 LLM 추천 항목:", [f["항목"] for f in parsed_fields])

        table_fieldnames = extract_table_fieldnames(req.table_texts)
        print("📋 추출된 표 항목:", table_fieldnames)

        filtered_fields = remove_duplicate_fields(parsed_fields, table_fieldnames)
        print("✅ 필터링 후 남은 항목:", [f["항목"] for f in filtered_fields])

        return {
            "topic": req.topic,
            "required_data": response.content,
            "required_fields": filtered_fields
        }
    except Exception as e:
        print(f"❌ infer-required-data 실패: {e}")
        return {
            "topic": req.topic,
            "required_data": "⚠️ LLM 호출 중 오류가 발생했습니다.",
            "required_fields": []
        }



class DraftRequest(BaseModel):
    topic: str
    inputs: dict
    chunks: List[str]
    table_texts: List[str]
    improvement: Optional[str] = None

@router.post("/generate-draft")
def generate_draft(req: DraftRequest):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        max_tokens=1500,
        openai_api_key=key["OPENAI_API_KEY"]
    )

    def format_inputs(inputs: dict) -> str:
        lines = []

        # ✅ 사용자가 작성한 표 HTML 직접 삽입
        if "filled_table_html" in inputs:
            lines.append("\n\n📊 사용자가 작성한 표:\n")
            lines.append(inputs["filled_table_html"])  # 그대로 삽입

        # ✅ 기존 tableInputs 기반 행렬 방식 (선택 유지 가능)
        if "table" in inputs:
            table_data = inputs["table"]
            rows = {}

            for key, val in table_data.items():
                # key 예시: page1_table0_r2_c3
                m = re.match(r"page\d+_table\d+_r(\d+)_c(\d+)", key)
                if m:
                    r, c = int(m.group(1)), int(m.group(2))
                    rows.setdefault(r, {})[c] = val

            # 행렬 방식으로 표 재조립 (원한다면 주석처리해도 됨)
            lines.append("\n\n<table>")
            for r in sorted(rows):
                lines.append("<tr>")
                for c in sorted(rows[r]):
                    cell_value = rows[r][c].strip()
                    lines.append(f"<td>{cell_value}</td>")
                lines.append("</tr>")
            lines.append("</table>\n")

        # ✅ 나머지 일반 입력값 처리
        for 항목, 내용 in inputs.items():
            if 항목 in ("table", "filled_table_html"):
                continue
            # ✅ 새 이미지 배열 처리
            if 항목 == "관련 이미지" and isinstance(내용, list):
                for item in 내용:
                    url = item.get("url")
                    title = item.get("title", "")
                    description = item.get("description", "")
                    if url:
                        lines.append(f"\n\n![{title}]({url})\n**{title}**\n{description}")
                continue

            # 기존 dict 처리
            if isinstance(내용, dict):
                if "url" in 내용:
                    lines.append(f"- {항목}: ![이미지]({내용['url']})")
                else:
                    for 연도, 값 in 내용.items():
                        if isinstance(val := 값, dict) and "url" in val:
                            lines.append(f"- {연도}년 {항목}: ![이미지]({val['url']})")
                        else:
                            lines.append(f"- {연도}년 {항목}: {값}")
            elif isinstance(내용, str):
                lines.append(f"- {항목}: {내용}")

        return "\n".join(lines)




    formatted_inputs = format_inputs(req.inputs)

    system = SystemMessage(content="""
    너는 ESG 보고서를 작성하는 전문 컨설턴트야.

    사용자가 제공한 지표 설명 텍스트와 표 내용은 보고서 작성 가이드에서 발췌한 것이며,
    너는 이를 바탕으로 해당 지표의 보고서 초안을 작성해야 해.

    ▶ 전반 톤&스타일
    - 공식적·객관적 문체: 3인칭, 정중한 현재·과거 시제 사용 (예: “감소하였습니다”, “증가하였습니다”)
    - 경영진 대상 비즈니스 레포트 어조
    - GRI, TCFD, SASB 등 국제·국내 프레임워크 언급 가능
    - 사실·수치 중심
    - 문장 연결 허용: “…하고, 이에 따라…”, “…하며…” 등 복문 형태로 사실을 유기적으로 연결 가능
    - 부사·접속사 활용 장려: “특히”, “한편”, “또한” 등 강조 부사 및 접속사 사용을 허용해 리듬감 부여
    - 복문 일부 허용: 두 개 이상의 사실을 하나의 문장에서 연결할 수 있도록 허용
    - 격식체 종결어미 사용: 모든 문장은 “감소하였습니다”, “확인되었습니다”, “추진하고 있습니다” 등의 정중한 어미로 끝맺기

    ▶ 금지사항
    - 추측성 문장(“~으로 보입니다”, “~로 해석됩니다”) 사용 금지
    - 절대 추측, 원인 해석(“생산 활동이 활발해진 결과”) 사용 금지
    - 데이터 미제공 항목에 대한 이유 추측 금지
    - 메타 표현 금지 (예: “이 표는 회사의 노력을 보여준다” 등)

    초안을 작성할 때 다음 지침을 반드시 따라야 해:

    1. 섹션 제목
    - 예: “생물다양성 보호 정책”, “법적 보호종 관리”

    2. 핵심 테마 소제목 구성
    - 입력값 항목이 많을 경우 소제목은 2개 이상으로 자유롭게 나누고, 의미상 유사한 항목은 묶어서 설명해.
    - 예: "보호 정책 및 영향 측정", "법적 보호종 관리", "지역사회 의견 수렴"

    3. 소제목별 문단 구성
    - 소제목 아래에 관련 입력값을 문장으로 자연스럽게 연결해. 항목명을 그대로 나열하지 말고 재구성해서 표현해.
    - 예: “법적 보호종 존재 여부: 예” → “법적 보호종이 존재하여 관련 보호 조치를 시행하였습니다.”
    - 단답형 입력값(예/아니오, 텍스트)도 마치 보고서 문장처럼 연결하여 작성해.
    - 항목을 나열하지 말고, 논리적으로 연결된 흐름의 서술형 문단을 구성해.

    4. 표
    - 사용자가 입력한 표가 존재하면, HTML 형식으로 본문에 그대로 삽입해.
    - 예: `📊 아래 표는 ___의 사용 현황을 보여줍니다.` 같은 문장으로 시작한 후, `<table>...</table>` 삽입

    5. 이미지
    - 입력값에 이미지가 포함된 경우, 반드시 `![설명](URL)` 마크다운 이미지 형식으로 삽입해.
    - 특히, `관련 이미지` 항목이 배열인 경우, 각 이미지에 대해 다음과 같은 형식으로 출력해:
    - ![제목](이미지 링크)
    - 제목은 굵게 (`**제목**`)
    - 설명은 제목 아래 한 문단으로 작성
    - 절대 `[텍스트](URL)`처럼 링크만 쓰지 말고, 실제 이미지가 표시되도록 출력할 것.

    6. 마지막 단락 구성
    - 사용자가 입력한 ‘개선 노력 및 활동’ 내용이 있을 경우 마지막 단락에 자연스럽게 연결하고, 소제목은 자유롭게 설정.
    - 예: “또한, ___ 활동을 통해 ___ 관리 강화를 위한 노력을 지속하고 있습니다.”

    📝 출력 형식
    - 2~3문단 이상의 서술형으로 작성
    - 의미별 소제목으로 구분
    - 필요 시 사용자 데이터 기반 표를 하나 포함
                           
    📌 추가 지침 (정확성·문장화 강화)
    - 사용자가 입력하지 않은 항목을 임의로 생성하거나 확장하지 마. (예: “국제 협약의 포괄성 여부” 등)
    - '예/아니오'로 끝나는 단답형 표현은 지양하고, 그 의미를 정책·활동·조치 등과 연결된 서술형 문장으로 자연스럽게 표현해.
    - 예: “법적 보호종 존재 여부: 예” → “법적 보호종이 확인되어, 이에 따른 보호 조치를 수립하였습니다.”처럼 바꿔 써.
    - “존재하지 않았다”, “적용되지 않았다” 등의 표현도 가능하면 완곡하게 표현하고, 불필요한 부정 표현은 피할 것.

                           
    ▶ 수치 및 표 작성 규칙

    - 표에 포함된 수치는 본문에 다시 서술하지 않습니다.
    - 본문은 구체적 수치보다는 **변화 경향(예: 증가, 감소, 유지)** 과 **의미 요약** 중심으로 작성합니다.
    - 예시 문장: “최근 3년간 원부자재 사용량이 증가 추세를 보였습니다”, “사용 효율이 개선되며 집약도가 완화되었습니다” 등.
    - 수치의 비교 및 구체적인 변화량은 **본문이 아닌 표를 통해 시각적으로 전달**합니다.
    - 이를 통해 본문은 수치가 아닌 정책, 대응 전략, 활동 중심으로 구성됩니다.
                           
    """)



    joined_chunks = "\n".join(req.chunks)
    joined_tables = "\n".join(req.table_texts)

    user = HumanMessage(content=f"""
    [지표 ID: {req.topic}]

    📘 지표 설명 텍스트:
    {joined_chunks}

    📊 작성 가이드 표:
    {joined_tables}

    📥 사용자 입력 데이터:
    {formatted_inputs}

    📈 개선 노력 및 활동:
    {req.improvement or '없음'}
    """)

    try:
        response = llm.invoke([system, user])
        return {
            "draft": response.content.strip()
        }
    except Exception as e:
        print("❌ 초안 생성 실패:", e)
        return {
            "draft": "⚠️ 초안 생성 중 오류가 발생했습니다."
        }



@router.post("/summarize-indicator")
def summarize_indicator(req: InferDataRequest):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    system = SystemMessage(content="""
너는 ESG 보고서를 작성하는 전문가야.

아래 지표 설명 텍스트를 바탕으로 다음과 같이 요약해줘:

- 이 지표의 목적과 의미를 1문장으로 설명하고, *줄을 바꾼 후에* 작성 방법이나 보고 시 유의할 점을 1~2문장으로 요약해줘
- 화려한 문구 없이 명확하고 실용적으로 써줘
- 반드시 지표 설명 텍스트의 내용을 기반으로, 지어내지 말고 써줘

    """)

    chunks = "\n".join(req.chunks)
    user = HumanMessage(content=f"[지표 ID: {req.topic}]\n\n{chunks}")

    try:
        res = llm.invoke([system, user])
        return {"summary": res.content.strip()}
    except Exception as e:
        print("❌ 요약 실패:", e)
        return {"summary": "요약 실패"}
    

# ⬇️ 초안 저장 API
@router.post("/save-draft")
async def save_draft_api(req: Request):  # ✅ async def
    data = await req.json()              # ✅ await 추가
    topic = data.get("topic")
    company = data.get("company")
    draft = data.get("draft")
    save_draft(topic, company, draft)
    return {"message": "✅ Draft saved"}

@router.get("/indicator-status", response_model=Dict[str, str])
def get_indicator_status():
    raw = list(draft_collection.find(
        {}, {"_id": 0, "topic": 1, "status": 1, "draft": 1}
    ))
    result = {}

    for doc in raw:
        code = doc["topic"]
        if doc.get("status") == "completed":
            result[code] = "completed"
        elif doc.get("status") == "saved":
            result[code] = "saved"
        elif doc.get("draft"):
            result[code] = "saved"
        else:
            # ✅ 추가: draft_inputs 확인
            input_doc = input_collection.find_one({"topic": code})
            if input_doc and (
                input_doc.get("inputs") or input_doc.get("table") or input_doc.get("improvement")
            ):
                result[code] = "saved"  # ✅ 입력값만 있어도 저장됨 처리
            else:
                result[code] = "empty"

    return result


@router.post("/complete-indicator/{code}")
def complete_indicator(code: str):
    try:
        result = draft_collection.update_one(
            {"topic": code},
            {"$set": {"status": "completed"}},
            upsert=True
        )
        if not result.acknowledged:
            raise RuntimeError("완료 처리 실패")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ⬇️ 초안 불러오기 API
@router.get("/load-draft")
def load_draft_api(topic: str, company: str):
    draft = load_draft(topic, company)
    return {"draft": draft or ""}


@router.delete("/delete-draft")
async def delete_draft_api(req: DeleteDraftRequest):
    # services/draft_store.py 에 delete 함수가 없으면 바로 pymongo 코드로 구현
    from services.draft_store import delete_draft  # 혹은 직접 MongoDB delete 로직
    deleted = delete_draft(req.topic, req.company)
    if not deleted:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"deleted": True}