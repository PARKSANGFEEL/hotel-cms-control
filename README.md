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
├── hotel_cms_controller.py  # 메인 프로그램
├── config.py                # 설정 파일
├── requirements.txt         # 필요한 패키지 목록
├── .env.example            # 환경 변수 예시
└── README.md               # 이 파일
```

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

## 향후 개선 사항

- [ ] 날짜별 예약 가능 수량 설정
- [ ] 가격 정책 자동 조절
- [ ] 예약 현황 리포트 생성
- [ ] API 연동 (있는 경우)
- [ ] GUI 인터페이스 추가
