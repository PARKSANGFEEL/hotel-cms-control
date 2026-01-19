# -*- coding: utf-8 -*-
"""
기준가격 파일 복구/변환 도구
- 손상된 기준가격.xlsx가 있을 경우, 기준가격.csv를 기준으로 새 기준가격.xlsx를 생성합니다.
- CSV 인코딩(utf-8/cp949)을 자동으로 시도합니다.

사용법 (Windows PowerShell or cmd):
    py repair_base_price.py

생성 파일:
    기준가격.xlsx (동일 폴더)

CSV 형식 요구사항:
- 첫 번째 행: 헤더(첫 열은 날짜, 이후 열은 방 타입명)
- 이후 행: 각 날짜별 방 타입 가격 (숫자)
"""
import os
import pandas as pd

def load_csv_flexible(csv_path: str) -> pd.DataFrame:
    last_err = None
    for enc in ("utf-8", "cp949"):
        try:
            return pd.read_csv(csv_path, encoding=enc)
        except Exception as e:
            last_err = e
            continue
    raise last_err if last_err else RuntimeError("CSV 로드 실패")


def repair_to_xlsx(base_dir: str = None):
    base_dir = base_dir or os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "기준가격.csv")
    xlsx_path = os.path.join(base_dir, "기준가격.xlsx")

    if not os.path.exists(csv_path):
        print(f"⚠ 기준가격.csv 파일이 없습니다: {csv_path}")
        print("→ Excel에서 '다른 이름으로 저장'으로 CSV를 만들거나, 기존 시트를 CSV로 내보내세요.")
        return 1

    try:
        df = load_csv_flexible(csv_path)
        # 날짜 열을 문자열로 강제 변환 (엑셀에서 날짜로 인식되도록 유지)
        df.iloc[:, 0] = df.iloc[:, 0].astype(str)
        # 엑셀로 저장
        df.to_excel(xlsx_path, index=False, engine='openpyxl')
        print(f"✓ 새 기준가격.xlsx 생성 완료: {xlsx_path}")
        print("→ 호텔 CMS 컨트롤러가 이 파일을 사용해 기준가를 로드합니다.")
        return 0
    except Exception as e:
        print(f"⚠ 변환 실패: {e}")
        return 2


if __name__ == "__main__":
    exit_code = repair_to_xlsx()
    raise SystemExit(exit_code)
