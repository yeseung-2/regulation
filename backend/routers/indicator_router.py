from fastapi import APIRouter
import pandas as pd
import os
from services.vector_loader import load_vectorstore

router = APIRouter()

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
industry_map_path = os.path.join(BASE_DIR, "../SASB/sasb_industries_map.xlsx")
kbz_map_path = os.path.join(BASE_DIR, "../SASB/kbz_sasb_eng_topics_map.xlsx")

industry_df = pd.read_excel(industry_map_path)
kbz_df = pd.read_excel(kbz_map_path)

industry_df.columns = industry_df.columns.str.strip()
kbz_df.columns = kbz_df.columns.str.strip()

group_map = {
    "제품 안전": "제품 안전", "제품안전": "제품 안전", "제품 품질 및 안전": "제품 안전",
    "제품 보안": "제품 안전", "제품 환경·보건·안전 성과": "제품 안전",
    "데이터 보안": "데이터 보안", "데이터 프라이버시": "데이터 보안",
    "데이터 프라이버시 및 표현의 자유": "데이터 보안",
    "종업원 보건 및 안전": "종업원 보건 및 안전", "전 종업원 보건 및 안전": "종업원 보건 및 안전",
    "종업원(employee)보건 및 안전": "종업원 보건 및 안전", "전 종업원(workforce) 보건 및 안전": "종업원 보건 및 안전",
    "전 종업원(workforce)보건 및 안전": "종업원 보건 및 안전",
    "온실가스 배출량": "온실가스 배출량", "온실가스 배출 및 에너지 자원 계획": "온실가스 배출량",
    "폐기물 관리": "폐기물 관리", "유해폐기물 관리": "폐기물 관리", "폐기물 및 유해물질 관리": "폐기물 관리",
    "사업 윤리": "사업 윤리", "사업 윤리 및 투명성": "사업 윤리", "기업 윤리": "사업 윤리",
    "공급망 관리": "공급망 관리", "팜유 공급망의 환경적·사회적 영향": "공급망 관리",
    "원료 공급망의 환경적∙사회적 영향": "공급망 관리",
    "에너지 관리": "에너지 관리", "에너지 가격적정성": "에너지 관리",
    "최종 사용 효율 및 수요": "에너지 관리", "소매 및 유통 과정에서의 에너지 관리": "에너지 관리",
    "제품 수명주기 관리": "제품 수명주기 관리", "제품 수명주기(Lifecycle)의 환경적 영향": "제품 수명주기 관리",
    "제품 설계 및 수명주기 관리": "제품 수명주기 관리", "포장재 수명주기 관리": "제품 수명주기 관리",
    "경쟁적 행위": "경쟁적 행위", "경쟁적 행위 및 개방형 인터넷": "경쟁적 행위",
    "지식재산권 보호 및 경쟁적 행위": "경쟁적 행위",
    "지역사회 관계": "지역사회 관계", "신규 개발의 지역사회 영향": "지역사회 관계"
}

@router.get("/recommend-by-name/{industry_name}")
def recommend_by_name(industry_name: str):
    # 1. 업종명으로 기준명 추출
    filtered = industry_df[industry_df["산업명"] == industry_name]
    if filtered.empty:
        return {"error": f"'{industry_name}' 업종을 찾을 수 없습니다."}

    criteria_raw = filtered["Disclosure_Topic"].dropna().unique().tolist()
    required_criteria = list({x.strip() for item in criteria_raw for x in str(item).split(",")})

    # 2. KBZ 매핑
    mapped, matched_criteria = [], set()
    for _, row in kbz_df.iterrows():
        kbz_code = row["KBZ_Code"]
        topic = str(row["Mapped_SASB_Topic"]).strip()
        if topic in required_criteria:
            mapped.append({
                "kbz_code": kbz_code,
                "matched_criteria": topic
            })
            matched_criteria.add(topic)

    # 3. unmapped 처리
    unmapped_criteria = list(set(required_criteria) - matched_criteria)

    sasb_vectorstore = load_vectorstore("sasb")
    all_docs = list(sasb_vectorstore.docstore._dict.values())
    sorted_docs = sorted(all_docs, key=lambda d: d.metadata.get("chunk_id", ""))

    # 블록 추출 함수: 기준명 등장 후 다른 기준명 나오기 전까지
    def extract_block_for_crit(crit: str):
        block = []
        seen_chunk_ids = set()
        found = False
        for doc in sorted_docs:
            content = doc.page_content
            chunk_id = doc.metadata.get("chunk_id")

            if not found and crit in content:
                found = True
                if chunk_id not in seen_chunk_ids:
                    block.append(doc)
                    seen_chunk_ids.add(chunk_id)
                continue

            if found:
                if any(other != crit and other in content for other in unmapped_criteria):
                    break
                if chunk_id not in seen_chunk_ids:
                    block.append(doc)
                    seen_chunk_ids.add(chunk_id)
        return [doc.page_content for doc in block]

    unmapped = []
    for crit in unmapped_criteria:
        crit = crit.strip()
        chunks = extract_block_for_crit(crit)
        unmapped.append({
            "criteria": crit,
            "chunks": chunks
        })

    # 4. 그룹핑
    def group_key(name):
        return group_map.get(name, name)

    grouped_mapped = {}
    for item in mapped:
        key = group_key(item["matched_criteria"])
        grouped_mapped.setdefault(key, []).append(item)

    grouped_unmapped = {}
    for item in unmapped:
        key = group_key(item["criteria"])
        grouped_unmapped.setdefault(key, []).append(item)

    return {
        "industry": industry_name,
        "mapped": mapped,
        "unmapped": unmapped,
        "grouped_mapped": grouped_mapped,
        "grouped_unmapped": grouped_unmapped
    }
