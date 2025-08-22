import os
import argparse
import camelot
import pdfplumber
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import math
import openai
from collections import defaultdict

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                path = os.path.join(output_dir, f"page{i+1:02}.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"📄 텍스트 저장: {path}")

def extract_sorted_text(pdf_path, output_dir, y_tolerance=3):
    os.makedirs(output_dir, exist_ok=True)
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            width, height = page.width, page.height
            # BBox 설정: 좌0 유지, 우36, 상50 제외, 하단 전체 포함
            clipped = page.within_bbox((0, 50, width - 36, height))
            lines = defaultdict(list)

            for char in clipped.chars:
                y_key = round(char['top'] / y_tolerance)
                lines[y_key].append((char['x0'], char['text']))

            sorted_lines = []
            for y in sorted(lines.keys()):
                line = ''.join([t for _, t in sorted(lines[y])])
                sorted_lines.append(line.strip())

            text = '\n'.join(sorted_lines)
            path = os.path.join(output_dir, f"page_{i+1:03}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"✅ 정렬 텍스트 저장: {path}")

# def gpt_format_text(input_dir, output_dir):
#     os.makedirs(output_dir, exist_ok=True)
#     for filename in sorted(os.listdir(input_dir)):
#         if not filename.endswith(".txt"):
#             continue
#         with open(os.path.join(input_dir, filename), "r", encoding="utf-8") as f:
#             raw = f.read()

#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             temperature=0.3,
#             messages=[
#                 {"role": "system", "content": "너는 PDF에서 추출된 텍스트를 구조화하는 어시스턴트야. 표는 무시하고, 제목(h3), 리스트(ul/li), 문단(p) 구조로만 정리해줘."},
#                 {"role": "user", "content": raw[:8000]}
#             ]
#         )

#         result = response.choices[0].message.content.strip()
#         html_path = os.path.join(output_dir, filename.replace(".txt", ".html"))
#         with open(html_path, "w", encoding="utf-8") as f:
#             f.write(result)
#         print(f"🧠 GPT 정제 결과 저장: {html_path}")

def extract_tables(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
    for i, table in enumerate(tables):
        page_num = int(table.page)
        html_path = os.path.join(output_dir, f"page{page_num:02}_table{i+1:02}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(table.df.to_html(index=False))
        print(f"✅ 표 저장: {html_path}")

def extract_page_images(pdf_path, output_dir, batch_size=10, dpi=200):
    os.makedirs(output_dir, exist_ok=True)
    total_pages = len(convert_from_path(pdf_path, dpi=10))
    num_batches = math.ceil(total_pages / batch_size)

    for b in range(num_batches):
        start = b * batch_size + 1
        end = min((b + 1) * batch_size, total_pages)
        print(f"📦 페이지 이미지 배치 처리 중: {start}~{end}페이지")
        images = convert_from_path(pdf_path, dpi=dpi, first_page=start, last_page=end)
        for i, img in enumerate(images):
            page_num = start + i
            path = os.path.join(output_dir, f"page{page_num:02}.png")
            img.save(path, "PNG")
            print(f"🖼️ 페이지 이미지 저장: {path}")

def extract_embedded_images(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            filename = f"page{i+1:02}_img{img_index+1}.{ext}"
            with open(os.path.join(output_dir, filename), "wb") as f:
                f.write(image_bytes)
            print(f"🖼️ 내부 이미지 저장: {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="PDF 파일 경로")
    parser.add_argument("--text", action="store_true", help="pdfplumber 텍스트 추출")
    # parser.add_argument("--gpt-text", action="store_true", help="좌표 정렬 텍스트 + GPT 정제")
    parser.add_argument("--tables", action="store_true", help="표 HTML 저장")
    parser.add_argument("--images", action="store_true", help="내부 삽입 이미지 추출")
    parser.add_argument("--page-images", action="store_true", help="페이지 전체 이미지 저장")
    parser.add_argument("--all", action="store_true", help="전체 추출")
    parser.add_argument("--batch", type=int, default=10, help="페이지 이미지 배치 단위")
    parser.add_argument("--dpi", type=int, default=200, help="페이지 이미지 DPI 설정")
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print("❌ PDF 파일이 존재하지 않습니다.")
        exit()

    base_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    base_dir = f"extracted/{base_name}"

    if args.all or args.text:
        print("📄 텍스트 추출 중...")
        extract_text(args.pdf_path, os.path.join(base_dir, "text"))

    # if args.gpt_text:
    #     print("🧠 GPT 텍스트 정제 중...")
    #     sorted_dir = os.path.join(base_dir, "sorted_text")
    #     formatted_dir = os.path.join(base_dir, "gpt_text")
    #     extract_sorted_text(args.pdf_path, sorted_dir)
    #     gpt_format_text(sorted_dir, formatted_dir)

    if args.all or args.tables:
        print("📊 표 추출 중...")
        extract_tables(args.pdf_path, os.path.join(base_dir, "tables"))

    if args.all or args.images:
        print("🖼️ 내부 삽입 이미지 추출 중...")
        extract_embedded_images(args.pdf_path, os.path.join(base_dir, "images"))

    if args.all or args.page_images:
        print("🖼️ 페이지 전체 이미지 추출 중...")
        extract_page_images(args.pdf_path, os.path.join(base_dir, "page_images"), args.batch, args.dpi)

    print("✅ 완료!")
