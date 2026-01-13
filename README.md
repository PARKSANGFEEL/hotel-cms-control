# 호텔 CMS 컨트롤 프로그램

호텔 예약 시스템 CMS를 자동으로 제어하여 방 타입별 예약 가능 수량을 조절하는 프로그램입니다.

## 기능

- ✅ Single Room, Twin Room, Double Room, Triple Room의 예약 가능 수량 조절
- ✅ 현재 예약 가능 수량 조회
- ✅ 일괄 수량 설정

## 설치 방법

### 1. Python 설치
Python 3.8 이상이 필요합니다.

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 설정 (선택사항)
`.env.example` 파일을 `.env`로 복사하고 필요한 정보를 입력합니다:
```bash
copy .env.example .env
```

## 사용 방법

### 기본 실행
```bash
python hotel_cms_controller.py
```

### 프로그램 사용 순서
1. 프로그램 실행 시 자동으로 Chrome 브라우저가 열립니다
2. CMS 페이지로 자동 접속됩니다
3. 수동으로 로그인합니다 (자동 로그인 기능 추가 가능)
4. 콘솔에서 Enter를 눌러 계속 진행합니다
5. 현재 예약 가능 수량이 조회됩니다
6. 수량 변경을 원하면 'y'를 입력합니다
7. 설정된 수량이 자동으로 입력됩니다

## 코드 사용 예시

```python
from hotel_cms_controller import HotelCMSController

# 컨트롤러 생성
controller = HotelCMSController()
controller.setup_driver()
controller.navigate_to_cms()

# 수동 로그인 후 진행...

# 개별 방 설정
controller.set_room_availability('SINGLE', 10)  # Single Room 10개 설정
controller.set_room_availability('TWIN', 5)     # Twin Room 5개 설정

# 한번에 모든 방 설정
room_settings = {
    'SINGLE': 8,
    'TWIN': 6,
    'DOUBLE': 4,
    'TRIPLE': 2
}
controller.set_all_rooms(room_settings)

# 현재 상태 조회
current_status = controller.get_current_availability()

# 브라우저 종료
controller.close()
```

## 주의사항

⚠️ **중요**: 이 프로그램은 실제 CMS의 HTML 구조에 맞게 커스터마이징이 필요합니다.

`hotel_cms_controller.py` 파일에서 다음 부분들을 실제 CMS 구조에 맞게 수정해야 합니다:

1. **로그인 요소** (line 58-65)
   - 사용자명/비밀번호 입력 필드 ID
   - 로그인 버튼 ID

2. **방 타입 요소** (line 101-111)
   - 방 타입을 표시하는 테이블 구조
   - 입력 필드의 위치 및 타입

3. **저장 버튼** (line 146-152)
   - 저장 버튼의 위치 및 텍스트

## Chrome 개발자 도구로 요소 찾기

1. CMS 페이지에서 F12를 눌러 개발자 도구 열기
2. Elements 탭에서 Ctrl+F로 요소 검색
3. 요소를 찾아 ID, Class, XPath 확인
4. 코드에서 해당 선택자 수정

## 파일 구조

```
hotel-cmscontrol/
├── hotel_cms_controller.py   # 메인 프로그램
├── config.py                 # 설정 파일
├── requirements.txt          # 필요한 패키지 목록
├── repair_base_price.py      # 손상 엑셀 복구 스크립트
├── apply_highlights.py       # 하이라이트 배치 적용 스크립트
├── verify_loader.py          # 기준가 로더 검증 스크립트
├── .env.example              # 환경 변수 예시
└── README.md                 # 이 파일
```

## 요금 자동입력 및 하이라이트 안전 처리

### 하이라이트 JSON 배치 방식 (권장)

원본 엑셀이 손상되지 않도록, 마감된 방 정보는 JSON 로그에 누적 후 별도 명령으로 한 번에 적용합니다.

**워크플로우:**

1. **프로그램 실행** (기준가 읽기만)
   ```powershell
   py hotel_cms_controller.py
   ```
   - Option 2 선택 → 요금 자동입력 실행
   - 마감된 방 정보 → `기준가격_하이라이트.json` 기록
   - 원본 엑셀 (`기준가격.xlsx`)은 **읽기만**, 쓰기 없음

2. **하이라이트 배치 적용** (실행 후 또는 여러 회 누적 후)
   ```powershell
   py apply_highlights.py
   ```
   - `기준가격_하이라이트.json` 읽음
   - 기준가격.xlsx에 진한 노란색(FFFF00) 하이라이트 추가
   - 완료 후: JSON 백업 생성, 원본 JSON 삭제

**장점:**
- 프로그램 실행 중 멈춰도 엑셀 손상 없음
- 하이라이트 정보는 JSON에 안전하게 누적
- 최종 배치 단계에서만 엑셀 쓰기 (위험 최소화)

## 문제 해결

### ChromeDriver 오류
- 자동으로 설치되므로 별도 설치 불필요
- 오류 발생 시 Chrome 브라우저를 최신 버전으로 업데이트

### 요소를 찾을 수 없음
- CMS 페이지의 실제 HTML 구조 확인 필요
- XPath 또는 선택자를 수정해야 함

### 로그인 실패
- 수동 로그인을 사용하거나
- `.env` 파일에 올바른 계정 정보 입력

### 기준가격 엑셀 손상 복구
엑셀 파일이 손상되어 `기준가격.xlsx`를 읽지 못하는 경우 다음 절차로 복구하세요:

- Excel에서 `기준가격.xlsx`를 열고, 메뉴에서 "다른 이름으로 저장" → 파일 형식을 `Excel 통합 문서 (*.xlsx)`로 선택해 새 파일로 저장합니다.
- 매크로 포함 형식(`.xlsm`)이나 오래된 형식(`.xls`)은 피하세요.
- 위 방법으로도 열리지 않으면 CSV로 대체하세요:
   1) Excel에서 시트를 `기준가격.csv`로 저장
   2) 아래 명령으로 새 `기준가격.xlsx`를 생성

```powershell
py repair_base_price.py
```

- 생성된 새 `기준가격.xlsx`는 컨트롤러가 자동으로 사용합니다.
- 컨트롤러는 손상 징후가 있을 때 `기준가격.csv`가 있으면 자동으로 대체 로드합니다(UTF-8/CP949 모두 시도).

## 향후 개선 사항

- [ ] 날짜별 예약 가능 수량 설정
- [ ] 가격 정책 자동 조절
- [ ] 예약 현황 리포트 생성
- [ ] API 연동 (있는 경우)
- [ ] GUI 인터페이스 추가
