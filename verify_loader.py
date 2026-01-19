# -*- coding: utf-8 -*-
"""
기준가격 로더/헤더 확인 스크립트
- 기준가격.xlsx를 읽어 헤더(컬럼)와 첫 행의 날짜를 출력
- 컨트롤러의 로더 함수로 기준가 맵을 로드해 샘플 출력
"""
import os
import pandas as pd
from hotel_cms_controller import HotelCMSController

BASE_DIR = os.path.dirname(__file__)
XLSX = os.path.join(BASE_DIR, "기준가격.xlsx")

print("[1] 파일 존재:", XLSX, os.path.exists(XLSX))

# Pandas로 직접 헤더 확인
try:
    df = pd.read_excel(XLSX, sheet_name=0, engine='openpyxl')
    print("[2] 헤더:", list(df.columns))
    if len(df) > 0:
        try:
            first_date = pd.Timestamp(df.iloc[0, 0]).strftime("%Y-%m-%d")
        except Exception:
            first_date = str(df.iloc[0, 0])
        print("[3] 첫 행 날짜:", first_date)
except Exception as e:
    print("[2] Pandas 읽기 실패:", e)

# 컨트롤러 로더로 기준가 확인
try:
    ctrl = HotelCMSController()
    bp = ctrl.load_base_prices_from_excel(None)
    print("[4] 로더 결과 샘플:", bp)
except Exception as e:
    print("[4] 컨트롤러 로더 실패:", e)
