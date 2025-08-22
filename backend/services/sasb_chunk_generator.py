import re
import pandas as pd
from pathlib import Path

# 기준 키워드 리스트 (필요시 확장 가능)
criteria_keywords = [
    "가격 책정의 무결성 및 투명성",
    "가격적정성 및 가격 책정",
    "가격적정성 및 가격책정",
    "강화된 생물다양성 영향",
    "건강 및 영양",
    "경쟁적 행위",
    "경쟁적 행위 및 개방형 인터넷",
    "공급망 관리",
    "공정 안전,비상사태 대비 및 대응",
    "공정거래",
    "공중보건",
    "구조적 무결성 및 안전성",
    "그리드 복원력",
    "금융 포용 및 역량 구축",
    "기업 윤리",
    "기술적 중단으로 인한 시스템 위험 관리",
    "기술적 중단으로 인한 시스템상 위험 관리",
    "노동 관계",
    "노동 관행",
    "대기 배출량",
    "대기질",
    "데이터 보안",
    "데이터 프라이버시",
    "데이터 프라이버시 및 표현의 자유",
    "법적 환경 및 규제 환경의 관리",
    "부품 및 자재의 수명주기",
    "사업 윤리",
    "사업 윤리 및 투명성",
    "사고 및 안전 관리",
    "사고 및 안전관리",
    "사회 및 지배구조 요소 포함",
    "사회공헌",
    "산업 활동의 ESG 요소 포함",
    "생물다양성 영향",
    "생태학적 영향",
    "석탄재 관리",
    "소매 및 유통 과정에서의 에너지 관리",
    "수명만료 제품 관리",
    "수명만료 제품관리",
    "수자원 관리",
    "시스템 위험 관리",
    "시스템 위험관리",
    "식품 안전",
    "신규 개발의 지역사회 영향",
    "신용 분석에 ESG 요소 포함",
    "에너지 가격적정성",
    "에너지 관리",
    "연비 및 사용단계 배출량",
    "연료 효율성 및 사용단계 배출량",
    "연료 효율성을 위한 설계",
    "운전자 근무 조건",
    "원료 공급망의 환경적∙사회적 영향",
    "원료 조달",
    "유전자변형 생물체",
    "유해물질 관리",
    "유해폐기물 관리",
    "윤리 마케팅",
    "이해충돌 관리",
    "의약품 안전성",
    "의약품 접근성",
    "의약품의 위조 방지",
    "의약품 접근성 및 안전성",
    "의약품 접근성과 가격 책정",
    "의약품 품질 및 접근성",
    "의약품 품질·접근성",
    "의약품 품질·접근성 및 가격",
    "의약품 품질·접근성·안전성",
    "의약품 품질·접근성·효과성",
    "이해 상충",
    "임상시험 참여자의 안전",
    "자원 효율성을 위한 설계",
    "자재 조달",
    "자재 효율성",
    "자재 효율성 및 재활용",
    "재제조 설계 및 서비스",
    "저널리스트의 무결성 및 스폰서십 식별",
    "전 종업원(workforce) 보건 및 안전",
    "전 종업원(workforce)다양성 및 포용성",
    "전 종업원(workforce)보건 및 안전",
    "전문가적 진실성",
    "정량적 목표 설정",
    "제품 라벨링 및 마케팅",
    "제품 수명주기 관리",
    "제품 수명주기(Lifecycle)의 환경적 영향",
    "제품 설계 및 수명주기 관리",
    "제품 안전",
    "제품 환경·보건·안전 성과",
    "제품 조달,포장재 및 마케팅",
    "제품 효율",
    "제품 보안",
    "정보 보호 및 사이버 보안",
    "정책 환경의 변화 대응",
    "종업원 다양성 및 포용성",
    "종업원 인센티브 및 위험 감수",
    "종업원 보건 및 안전",
    "종업원(employee) 보건 및 안전",
    "종업원(employee)보건 및 안전",
    "종업원 채용·개발·유지",
    "지역사회 관계",
    "지식재산권 보호 및 경쟁적 행위",
    "지적재산 보호 및 미디어 저작권 침해",
    "진단 정확도 및 접근성",
    "창의적 콘텐츠 보호",
    "책임감 있는 행동을 장려하기 위한 약관",
    "초과근무 및 근무시간",
    "친환경 제품 설계",
    "최종 사용 효율",
    "최종 사용 효율 및 수요",
    "투명하고 효율적인 자본시장 촉진",
    "투명한 정보 및 고객들을 위한 공정한 자문",
    "팜유 공급망의 환경적·사회적 영향",
    "폐기물 관리",
    "폐기물 및 유해물질 관리",
    "표준화된 보고서 작성 기준",
    "포장재 수명주기 관리",
    "프라이버시 및 개인 정보 보호",
    "프로젝트 개발의 환경적 영향",
    "하드웨어 기반시설의 환경 발자국",
    "화학물질 안전과 환경 책임주의",
    "환경 위험 노출",
    "환경 성과 측정",
    "환경 위험 노출 및 평가",
    "환경 위험 관리",
    "환경·사회적 영향"
]

# 1. 텍스트 로딩
def load_text_pages(text_dir: Path):
    pages = {}
    for txt_file in sorted(text_dir.glob("page*.txt")):
        try:
            page_num = int(txt_file.stem.replace("page", ""))
            pages[page_num] = txt_file.read_text(encoding="utf-8").strip()
        except:
            continue
    return pages

# 2. 문장 단위 청크화
def split_by_sentences(text, max_chars=500, overlap=100):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) > max_chars:
            chunks.append(current.strip())
            current = current[-overlap:] + " " + sentence
        else:
            current += " " + sentence
    if current:
        chunks.append(current.strip())
    return chunks

# 3. 키워드 기준 topic 분류
def guess_topic(text, keywords):
    for k in keywords:
        if k in text:
            return k
    return "기타"

# 4. 전체 실행
def main():
    root_dir = Path(__file__).resolve().parent.parent / "extracted" / "sasb"
    output_file = Path(__file__).resolve().parent.parent / "sasb_chunks.xlsx"

    records = []

    for industry_path in sorted(root_dir.iterdir()):
        if not industry_path.is_dir():
            continue

        title = industry_path.name
        text_dir = industry_path / "text"
        table_dir = industry_path / "tables_gpt"

        page_texts = load_text_pages(text_dir)
        all_text = "\n".join(page_texts.values())

        tables = []
        if table_dir.exists():
            for html_file in sorted(table_dir.glob("*.html")):
                tables.append(str(html_file))

        topic = guess_topic(all_text, criteria_keywords)
        chunks = split_by_sentences(all_text)

        for i, chunk in enumerate(chunks):
            records.append({
                "chunk_id": f"{title}_{i+1:02}",
                "title": title,
                "topic": topic,
                "text": chunk,
                "tables": tables,
                "pages": list(page_texts.keys())
            })

    df = pd.DataFrame(records)
    df.to_excel(output_file, index=False)
    print(f"✅ 완료: {output_file} (총 {len(df)}개 청크)")

if __name__ == "__main__":
    main()
