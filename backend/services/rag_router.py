from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain.schema import Document, SystemMessage, HumanMessage, AIMessage
from services.vector_loader import load_vectorstore
from key import key
import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from bs4 import BeautifulSoup
import torch

# ✅ 번역 캐시용
CACHE_PATH = Path("translation_cache.json")
translation_cache = {"ko2en": {}, "en2ko": {}}

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_cache():
    global translation_cache
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            translation_cache = json.load(f)

def save_cache():
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(translation_cache, f, ensure_ascii=False, indent=2)

def extract_clean_table_html(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    h3 = soup.find("h3")
    table = soup.find("table")
    if h3 and table:
        return f"{str(h3)}\n{str(table)}"
    return ""

# ✅ GPT 번역 with 캐싱
def translate_to_english(text: str) -> str:
    if text in translation_cache["ko2en"]:
        return translation_cache["ko2en"][text]

    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=key["OPENAI_API_KEY"])
    prompt = [
        SystemMessage(content="Translate the following Korean text to English. Respond only with the translated English."),
        HumanMessage(content=text)
    ]
    translated = llm.invoke(prompt).content
    translation_cache["ko2en"][text] = translated
    return translated

def translate_to_korean(text: str) -> str:
    if text in translation_cache["en2ko"]:
        cached = translation_cache["en2ko"][text]
        if "훈련되었습니다" in cached or "데이터" in cached:
            print(f"❌ fallback 번역 감지됨 → 캐시 무시하고 재번역합니다: {cached}")
        else:
            return cached

    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=key["OPENAI_API_KEY"])
    prompt = [
        SystemMessage(content="다음 영어 문장을 자연스러운 한국어로 번역해줘. 반드시 번역된 문장만 응답해."),
        HumanMessage(content=text)
    ]
    translated = llm.invoke(prompt).content

    # 다시 한번 fallback 탐지 (응답까지 의심스러울 수 있음)
    if "훈련되었습니다" in translated or "데이터" in translated:
        print("❌ 재번역도 fallback 탐지됨 → 응답 그대로 사용하지 않음")
        return "아래는 요청하신 GRI 원문 번역본 입니다.\n\n" + text

    translation_cache["en2ko"][text] = translated
    return translated

def clean_translation_cache(fallback_keywords=None):
    fallback_keywords = fallback_keywords or ["훈련되었습니다", "데이터", "2023년", "model"]
    cleaned = False

    for direction in ["en2ko", "ko2en"]:
        original = dict(translation_cache[direction])  # 복사
        for k, v in original.items():
            if any(kw in v for kw in fallback_keywords):
                print(f"🧹 캐시 제거됨 → {k} → {v}")
                del translation_cache[direction][k]
                cleaned = True

    if cleaned:
        save_cache()
        print("✅ translation_cache.json 정화 완료 및 저장됨")
    else:
        print("🧼 정화할 캐시 없음")

# ✅ GPT 기반 질문 분류
def classify_query(question: str) -> str:
    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=key["OPENAI_API_KEY"])
    system_prompt = """
너는 ESG 문서를 다루는 AI 문서 분류기야.

사용자의 질문을 읽고, 반드시 아래 4가지 중 하나를 선택해 JSON 형식으로 답해야 해. 다른 말은 절대 하지 마.

가능한 값:
- esg_Manual: 기본적인 질문, ESG 보고서 작성 예시, GRI 지표에 대한 일반 설명
- GRI_Standards: 질문에 '원문'이라는 단어가 있을 때만 선택 (예: "GRI 305-1 원문 보여줘")
- esg_templates: '규정', '규정안', '지침', '템플릿'과 같은 문구가 있으면 선택
- esg_sample1: 특정 기업의 실제 사례를 물을 때 선택 (예: "파나시아의 ESG 경영 사례 알려줘")

반드시 아래 형식으로 응답해:
{ "index": "선택값" }

예시:
질문: "GRI 305-1 원문 알려줘"
응답: { "index": "GRI_Standards" }

질문: "환경경영 규정안 양식 알려줘"
응답: { "index": "esg_templates" }

질문: "SK는 어떻게 대응했어?"
응답: { "index": "esg_sample1" }

질문: "중대성 평가 항목은 뭐야?"
응답: { "index": "esg_Manual" }
"""
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ]).content

    try:
        index = json.loads(response)["index"]
        print(f"✅ 선택된 벡터스토어 index_name: {index}")
        return index
    except Exception:
        print("❌ GPT 분류 실패 → 기본값 'esg_manual'")
        return "esg_Manual"

# ✅ 메타데이터에서 표/이미지 추출
def extract_metadata(documents: list[Document]) -> dict:
    tables, images = [], []
    seen_table_paths = set()
    seen_image_paths = set()

    for doc in documents:
        # 📌 표 처리
        t_raw = doc.metadata.get("tables", [])
        t = eval(t_raw) if isinstance(t_raw, str) else t_raw

        for table_path in t:
            if table_path in seen_table_paths:
                continue
            seen_table_paths.add(table_path)

            full_path = Path(table_path)
            if full_path.exists():
                table_html = full_path.read_text(encoding="utf-8")
                tables.append(table_html)

        # 📌 이미지 처리
        i_raw = doc.metadata.get("images", [])
        i = eval(i_raw) if isinstance(i_raw, str) else i_raw
        for img in i:
            if img not in seen_image_paths:
                seen_image_paths.add(img)
                images.append(img)

    return {
        "tables": tables,
        "images": images
    }

def extract_page_number_from_path(path: str) -> int | None:
    name = Path(path).stem
    if name.startswith("page") and "_" in name:
        return int(name.replace("page", "").split("_")[0])
    return None

def select_best_page(answer: str, table_paths: list[str], user_question: str = "") -> int | None:
    infos = []
    seen = set()
    for path in table_paths:
        if path in seen or not Path(path).exists():
            continue
        seen.add(path)

        soup = BeautifulSoup(Path(path).read_text(encoding="utf-8"), "html.parser")
        title = soup.find("h3").text.strip() if soup.find("h3") else ""
        headers = [th.get_text(strip=True) for th in soup.find_all("th")]
        cells = [td.get_text(strip=True) for td in soup.find_all("td")]
        content = " ".join(cells[:20])[:300]

        summary = f"{title}\n{', '.join(headers)}\n{content}"
        infos.append({"path": path, "summary": summary})

    if not infos:
        return None

    # ✅ 질문도 포함
    query = f"{answer}\n\n{user_question}".strip()
    query_embedding = model.encode(query, convert_to_tensor=True)
    table_embeddings = [model.encode(i["summary"], convert_to_tensor=True) for i in infos]
    table_embeddings = torch.stack(table_embeddings)

    scores = util.cos_sim(query_embedding, table_embeddings)[0]
    best_idx = scores.argmax().item()

    best_path = infos[best_idx]["path"]
    page = extract_page_number_from_path(best_path)
    print(f"📄 유사한 표 경로: {best_path} → page{page}")
    return page


# ✅ 페이지 단위 리소스 로딩
def load_resources_for_page(base_dir: str, page: int) -> tuple[list[str], list[str]]:
    table_dir = Path(base_dir) / "tables_gpt"
    tables = [str(p) for p in table_dir.glob(f"page{page}_table*.html")]

    image_dir = Path(base_dir) / "images"
    images = [str(p) for p in image_dir.glob(f"*page{page}*") if p.suffix.lower() in [".png", ".jpg", ".jpeg"]]

    return tables, images

def generate_suggested_questions(context_snippet: str, user_question: str, index_name: str) -> list[str]:
    # 🔒 특정 index는 질문 생성 제외
    if index_name in ["esg_templates", "esg_sample1"]:
        return []

    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=key["OPENAI_API_KEY"])
    prompt = [
        SystemMessage(content="""아래는 사용자의 질문과 관련 문서 내용입니다.
이 둘을 참고하여, 사용자가 이어서 할 수 있는 ESG 관련 실무 질문을 3개 추천해 주세요.
- 질문은 간결하고 구체적으로 작성해 주세요.
- 질문 외 다른 설명은 하지 마세요.
"""),
        HumanMessage(content=f"""[사용자 질문]
{user_question.strip()}

[문서 내용]
{context_snippet.strip()}""")
    ]
    try:
        response = llm.invoke(prompt).content
        lines = [line.strip("-•0123456789. ") for line in response.strip().split("\n") if line.strip()]
        return lines[:3]
    except Exception as e:
        print("❌ 추천 질문 생성 실패:", e)
        return ["이 항목에 대해 자세히 알려줘요.", "관련 사례가 있나요?", "작성할 때 주의할 점은 뭔가요?"]


def ask_with_context(message: str, history: list[dict] = []) -> dict:
    load_cache()
    clean_translation_cache()

    index_name = classify_query(message)

    # 1. query 영어 변환 (GRI만)
    query = translate_to_english(message) if index_name == "GRI_Standards" else message

    print(f"✅ 선택된 벡터스토어 index_name: {index_name}")
    vectorstore = load_vectorstore(index_name)

    # 2. 지표 코드 추출
    gri_codes = re.findall(r"\d{3}-\d+|\d{3}", message)
    code_match = gri_codes[0] if gri_codes else None

    # 3. GRI + 코드가 있는 경우 → 전체 문서 중 해당 지표 포함된 청크만 필터링
    if index_name == "GRI_Standards" and code_match:
        query_for_filter = code_match if code_match else query
        all_docs = vectorstore.similarity_search(query_for_filter, k=100)
        docs = [d for d in all_docs if code_match in d.page_content]
        if not docs:
            print(f"❌ 지표 '{code_match}'가 포함된 청크를 찾지 못했습니다.")
            return {
                "answer": f"해당 문서에서 '{code_match}'에 해당하는 내용을 찾지 못했습니다.",
                "source": index_name,
                "metadata": {},
                "table_html": ""
            }
        print(f"🎯 '{code_match}'가 포함된 청크 개수: {len(docs)}")
    else:
        retriever = vectorstore.as_retriever()
        docs = retriever.get_relevant_documents(query)
        
    print("📄 검색된 문서 제목 목록:")
    for i, d in enumerate(docs):
        title = d.metadata.get("title", "N/A")
        chunk_id = d.metadata.get("chunk_id", f"#{i}")
        print(f"  [{i}] {chunk_id} - {title}")

    # 4. context 생성
    main_title = docs[0].metadata.get("title", "")
    same_title_docs = [d for d in docs if d.metadata.get("title", "") == main_title]
    context = "\n\n".join([d.page_content for d in same_title_docs])
    print("📦 선택된 context 문서 개수:", len(same_title_docs))
    for i, doc in enumerate(same_title_docs):
        print(f"--- 문서 {i+1} ---")
        print("📌 title:", doc.metadata.get("title"))
        print("📄 pages:", doc.metadata.get("pages"))
        print("📁 tables:", doc.metadata.get("tables"))
        print("🖼️ images:", doc.metadata.get("images"))
    print("📚 context preview:")
    print(context[:500])
    print("........")

    # 5. hallucination 필터 (GRI 지표가 질문에 포함됐는데 context에 없으면 차단)
    if index_name == "GRI_Standards" and gri_codes:
        asked_codes = set(re.findall(r"\d{3}-\d+", message))
        context_codes = set(re.findall(r"\d{3}-\d+", context))
        hallucinated = not asked_codes.issubset(context_codes)

        if hallucinated:
            print("❌ GPT 응답 필터링: 질문한 GRI 지표가 context에 없음 → hallucination 가능성")
            return {
                "answer": "해당 문서에 요청하신 GRI 지표에 대한 내용이 없습니다.",
                "source": index_name,
                "metadata": {},
                "table_html": ""
            }
    # 6. table/image 분석
    want_table = any(k in message.lower() for k in ["표", "테이블", "table"])
    want_image = any(k in message.lower() for k in ["이미지", "사진", "image", "그림"])
    metadata = {"tables": [], "images": []}
    table_html = ""

    # 5. GPT에게 메시지 전달
    if index_name == "GRI_Standards":
        format_instruction = """
    📝 반드시 아래 형식을 따라 응답하세요:

    📌 GRI {지표번호} ({지표 제목})

    1. 문서에 포함된 내용을 기반으로 모든 정보를 누락 없이 요약해 주세요.
    - **요약은 짧게 하지 말고**, 항목별로 **충분한 설명**을 포함하세요.
    - **context에 등장한 항목은 모두 포함**하고, 문단 구조를 유지해 정리하세요.
    - **절대 추론하지 말고**, 문서에 있는 정보만 사용하세요.

    2. 아래는 출력 예시입니다 (형식 참고용이며 내용은 지표마다 다릅니다):
    📌 GRI 302-1 (조직 내 에너지 소비)

    1. 보고 조직은 다음 정보를 보고해야 합니다:
    - 비재생/재생 자원으로부터 소비된 연료 총량
    - 전기/난방/냉방/증기 소비 및 판매량
    - 에너지 소비 계산 기준 및 변환 계수

    2. 작성 지침:
    - 재생/비재생 연료를 구분해 보고

    3. 권장사항:
    - 변환 계수 일관 적용, 로컬/일반 계수 우선순위 명시

    """
        
    elif index_name == "esg_sample1":
        format_instruction = """
    🏢 기업명(또는 산업명): {기업 이름이나 산업이름}
    📌 ESG 활동

    - {내용 설명}

    ※ 사용자가 참고할 수 있도록 구체적 사례 위주로 설명해 주세요.
    """
    elif index_name == "esg_Manual":
        format_instruction = """
    📝 {질문에 대한 두괄식 답변}

    - {관련 설명}

    - {관련 설명}
    ...

    """
    else:
        format_instruction = ""  # 예외 없이 fallback

    messages = [
        SystemMessage(content=f"""
        너는 중소기업 ESG 보고서 작성을 도와주는 전문 어시스턴트야.
        사용자는 GRI 원문, 매뉴얼, 템플릿, 예시 등의 문서를 기반으로 실무 중심의 질문을 하고 있어.

        ---

        📌 너의 역할:
        아래 제공되는 문서(context)에 기반해 다음 여섯 가지 질문 유형에 적절하게 응답해.

        [활동 → GRI 지표 찾기]
        사용자 활동이 어떤 GRI 지표에 해당하는지 설명
        GRI 번호와 항목명, 간단한 정의를 제공
        🔍 데이터 출처: esg_Manual

        [GRI 지표 해석 / 작성 방법]
        특정 GRI 번호가 무엇을 의미하는지, 어떤 내용을 작성해야 하는지 설명
        🔍 데이터 출처: esg_Manual

        [작성 예시 요청]
        표가 존재하면 "표를 아래에 보여드릴게요."라고 응답
        <h3>, <table> 태그는 문서에서 가져온 경우만 사용 (직접 생성 금지)
        🔍 데이터 출처: esg_Manual

        [다른 기업 사례 요청]
        중소기업의 실제 ESG 활동 사례를 자세히 설명
        🔍 데이터 출처: esg_sample1

        [ESG 규정 초안 요청]
        템플릿을 바탕으로 간단한 문장형 초안 작성
        🔍 데이터 출처: esg_templates

        [GRI **원문** 요청]
        GRI 원문을 그대로 인용
        🔍 데이터 출처: GRI_Standards
        
        [매뉴얼 내용 설명]
        Context 내의 언급된 내용만 요약
        🔍 데이터 출처: esg_Manual

        ---

        📌 반드시 지켜야 할 응답 규칙:

        문서(context)에 등장하지 않는 정보는 절대 제공하지 마세요.
        추론, 상식, GPT 훈련 정보 사용 금지

        응답은 항상 질문에 대한 직접적인 문장으로 시작하세요.
        예: “GRI 302-1은 에너지 사용을 보고하는 지표입니다.”
        그 후, 문서(context)를 바탕으로 관련 설명, 작성 항목, 정의, 예시 등을 2~3문장 이상 보완하세요.
        전체 응답은 7문장 이내로 구성하세요.

        표 요청이 있을 경우
        문서 기반 표 요구 받을때 context의 간략한 설명과 함께 "표를 아래에 보여드릴게요."라고만 응답
        <h3>, <table>은 시스템이 따로 추가하므로 절대 생성하지 마세요

        다음 표현은 절대 사용하지 마세요:
        "죄송하지만", "훈련 데이터 기준으로는", "알 수 없습니다", "GPT는…" 등
        ---
        📘 문서(context)는 아래에 제공됩니다.  
        ※ 문서에 기반한 설명만 허용되며, 네가 문서를 추론하거나 거짓 응답을 지어내선 안 됩니다.

        {context}
        ---
        가독성을 위한 응답 양식
        {format_instruction}

        """),
        HumanMessage(content=query)
    ]


    llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=key["OPENAI_API_KEY"])
    output = llm.invoke(messages).content
    print("🔍 GPT 응답:", output)

    # 8. table/image 추출
    if want_table or want_image:
        # ✅ 문서 전체에서 테이블/이미지 경로 추출
        extracted = extract_metadata(docs)
        table_paths = extracted["tables"]
        image_paths = extracted["images"]
        table_htmls = []

        if want_table and table_paths:
            seen_tables = set()
            for table_path in table_paths:
                try:
                    # table_path가 html 태그일 경우 그대로 사용
                    if "<table" in table_path and "</table>" in table_path:
                        raw_html = table_path
                    else:
                        raw_html = Path(table_path).read_text(encoding="utf-8")

                    cleaned = extract_clean_table_html(raw_html)
                    if cleaned.strip() and cleaned not in seen_tables:
                        table_htmls.append(cleaned)
                        seen_tables.add(cleaned)

                except Exception as e:
                    print(f"❌ 테이블 읽기 실패: {table_path} → {e}")

        metadata = {"tables": table_paths}
        table_html = "\n<hr/>\n".join(table_htmls)

        print(f"📥 표/이미지 요청 감지됨 → table={want_table}, image={want_image}")
        print(f"📎 table paths: {table_paths}")
        print(f"🖼 image list: {image_paths}")

    # 9. 번역 여부
    final_answer = translate_to_korean(output) if index_name == "GRI_Standards" else output

    save_cache()
    return {
        "answer": final_answer,
        "source": index_name,
        "metadata": metadata,
        "table_html": table_html,
        "suggested_questions": generate_suggested_questions(context, message, index_name)
    }
