import os
from pathlib import Path

def ensure_symlink():
    target = Path("extracted/esg_templates/images")  # 원본 이미지 폴더
    link_path = Path("static/images")  # 우리가 연결해줄 위치 (/static/images)

    if not link_path.exists():
        print(f"🔗 static/images → {target} symlink 생성")
        link_path.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(target.resolve(), link_path)
    else:
        print("✅ static/images symlink 이미 존재")
