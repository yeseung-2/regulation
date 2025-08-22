import os
import base64
from glob import glob
import re
from dotenv import load_dotenv
from openai import OpenAI

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)
print("🔑 OPENAI API KEY:", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def send_table_to_gpt(table_html: str, image_path: str, page_num: int):
    try:
        with open(image_path, "rb") as img_file:
            image_b64 = base64.b64encode(img_file.read()).decode()

        gpt_prompt = f"""
        다음은 PDF에서 추출한 표입니다. 이 표는 병합 셀(rowspan, colspan)이 반영되지 않은 상태입니다.
        아래 HTML 테이블과 첨부된 페이지 이미지를 참고하여 실제 문서처럼 병합 구조를 반영한 HTML <table>을 생성해주세요.
        또한 표의 시각적 제목도 함께 추출해 <h3>제목</h3> 형태로 표 위에 포함해 주세요.(예: 표 상단 텍스트 중 표와 관련 있는 핵심 제목)
        마크다운이나 텍스트 기반 표는 절대 사용하지 마세요.

        페이지: {page_num}
        <table>
        {table_html}
        </table>
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": gpt_prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }}
                    ]
                }
            ]
        )

        return response.choices[0].message.content
    
    except Exception as e:
        print(f"❌ GPT 호출 실패 (page {page_num}): {e}")
        return ""


def process_all_tables(base_dir: str):
    table_dir = os.path.join(base_dir, "tables")
    image_dir = os.path.join(base_dir, "page_images") 
    output_dir = os.path.join(base_dir, "tables_gpt")
    os.makedirs(output_dir, exist_ok=True)

    table_files = sorted([
    os.path.join(table_dir, f)
    for f in os.listdir(table_dir)
    if f.endswith(".html") and "page" in f and "_table" in f
])

    for table_file in table_files:
        base = os.path.basename(table_file)
        match = re.search(r"page(\d+)_table", base)
        if not match:
            print(f"⚠️ 페이지 번호 추출 실패: {base}")
            continue
        page_num = int(match.group(1))
        # if page_num in [1, 2, 3, 4, 5, 6, 7]:
        #     print(f"⏭️ page{page_num:02}: 중복 페이지로 건너뜀")
        #     continue
        image_path = os.path.join(image_dir, f"page{page_num:02}.png")

        if not os.path.exists(image_path):
            print(f"⚠️ 이미지 없음: {image_path}")
            continue

        with open(table_file, "r", encoding="utf-8") as f:
            table_html = f.read()

        print(f"🔍 GPT 분석 중: {base} + page{page_num:02}.png")
        html_result = send_table_to_gpt(table_html, image_path, page_num)
        print(f"📤 GPT 응답 일부:\n{html_result[:300]}")
        output_path = os.path.join(output_dir, base.replace(".html", "_gpt.html"))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_result)
        print(f"✅ 저장 완료: {output_path}")
        

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❌ 사용법: python table_gpt_formatter.py extracted/esg_templates")
        exit(1)

    base_dir = sys.argv[1]
    process_all_tables(base_dir)
    