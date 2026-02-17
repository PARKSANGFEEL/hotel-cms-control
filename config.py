"""
호텔 CMS 컨트롤 프로그램 설정
"""
import os
from dotenv import load_dotenv

load_dotenv()

# CMS 접속 정보
CMS_URL = os.getenv('CMS_URL', 'https://wingscms.com/#/app/zz/zz03_0100')
CMS_COMPANY_ID = os.getenv('CMS_COMPANY_ID', 'GRIDINN')
CMS_USERNAME = os.getenv('CMS_USERNAME', 'gridpsp')
CMS_PASSWORD = os.getenv('CMS_PASSWORD', 'zbfl=726331')

# 방 타입 정의

ROOM_TYPES = {
    'SINGLE': 'Single Room',
    'TWIN': 'Twin Room',
    'DOUBLE': 'Double Room',
    'TRIPLE': 'Triple Room'
}

# 방 타입별 최대 수량
ROOM_MAX_COUNT = {
    'SINGLE': 10,
    'TWIN': 12,
    'DOUBLE': 5,
    'TRIPLE': 6
}

# 브라우저 설정
HEADLESS = False  # True로 설정하면 브라우저 창이 보이지 않음
IMPLICIT_WAIT = 10  # 요소를 찾을 때 대기 시간(초)

# 로그/속도 옵션
VERBOSE_LOGS = False  # True면 상세 디버그 로그 출력
LOG_LEVEL = "summary"  # summary|errors|verbose
SLEEP_SCALE = 0.5  # 1.0 기본, 값이 낮을수록 더 빠름 (0.5 = 안전한 중간 속도)

# 엑셀 안전 모드 설정
# True: 기준가격.xlsx을 읽기 전용으로 사용(로그/하이라이트 등 쓰기 작업 비활성화)
EXCEL_READ_ONLY = True
