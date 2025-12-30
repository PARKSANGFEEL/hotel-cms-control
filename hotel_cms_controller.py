"""
호텔 CMS 제어 프로그램
방 타입별 예약 가능 수량 조절 기능
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
import config
from datetime import datetime, timedelta




class HotelCMSController:
    """호텔 CMS를 제어하는 클래스"""

    def __init__(self):
        """브라우저 초기화"""
        self.driver = None
        self.wait = None
        self.change_history = []  # (date, room_type, index, old_value, new_value)

    def search_rooms_by_date(self):
        """조회 버튼을 눌러 해당 날짜의 내역을 조회"""
        try:
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "searchBtn"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
            time.sleep(0.5)
            search_button.click()
            print("  ✓ 조회 버튼 클릭 - 방 목록 로딩 중...")
            time.sleep(3)
            return True
        except Exception as e:
            print(f"  ⚠ 조회 버튼 클릭 실패: {e}")
            return False

    def setup_driver(self):
        """크롬 드라이버 설정 및 초기화"""
        chrome_options = Options()
        
        if config.HEADLESS:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')
        
        # Selenium 4의 자동 드라이버 관리 사용
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, config.IMPLICIT_WAIT)
        
        print("✓ 브라우저 초기화 완료")
        
    def login(self, company_id=None, username=None, password=None):
        """CMS 로그인"""
        company_id = company_id or config.CMS_COMPANY_ID
        username = username or config.CMS_USERNAME
        password = password or config.CMS_PASSWORD
        
        if not username or not password:
            print("⚠ 로그인 정보가 설정되지 않았습니다. 수동으로 로그인해주세요.")
            return False
        
        try:
            print("\n🔐 로그인 확인 중...")
            
            # 먼저 이미 로그인되어 있는지 확인
            time.sleep(2)
            current_url = self.driver.current_url
            
            # URL에 #/app이 있으면 이미 로그인된 상태
            if "#/app" in current_url:
                print("✓ 이미 로그인되어 있습니다 (로그인 유지 상태)")
                return True
            
            # 로그인 폼이 보이는지 확인
            try:
                self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                print("  → 로그인 폼 발견, 로그인 진행...")
            except:
                # 로그인 폼이 없으면 이미 로그인된 것으로 간주
                print("✓ 로그인 폼이 없습니다 (이미 로그인된 상태)")
                return True
            
            # 로그인 필요
            print("\n로그인 중...")
            
            # 컴퍼니 ID 입력
            company_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='컴퍼니'], input[placeholder*='ID']"))
            )
            company_field.clear()
            company_field.send_keys(company_id)
            print(f"  ✓ 컴퍼니 ID 입력: {company_id}")
            
            # 사용자 ID/이메일 입력 - 두 번째 입력 필드
            username_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            if len(username_fields) >= 2:
                username_fields[1].clear()
                username_fields[1].send_keys(username)
            else:
                username_field = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder*='사용자'], input[placeholder*='이메일']")
                username_field.clear()
                username_field.send_keys(username)
            print(f"  ✓ 사용자 ID 입력: {username}")
            
            # 비밀번호 입력
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            print("  ✓ 비밀번호 입력 완료")
            
            # 로그인 유지 체크박스 찾아서 체크
            try:
                keep_login_checkbox = self.driver.find_element(By.ID, "loginKeepCheckbox")
                
                if not keep_login_checkbox.is_selected():
                    self.driver.execute_script("arguments[0].click();", keep_login_checkbox)
                    print("  ✓ 로그인 유지 체크")
                else:
                    print("  ✓ 로그인 유지 이미 체크됨")
            except Exception as e:
                print(f"  ⚠ 로그인 유지 체크 실패: {e}")
            
            time.sleep(0.5)
            
            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]")
            login_button.click()
            print("  ✓ 로그인 버튼 클릭")
            
            # 로그인 완료 대기 (페이지 전환 또는 특정 요소 로드 확인)
            time.sleep(3)
            print("✓ 로그인 완료")
            return True
            
        except Exception as e:
            print(f"⚠ 자동 로그인 실패: {e}")
            print("수동으로 로그인해주세요.")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_cms(self):
        """CMS 페이지로 이동"""
        self.driver.get(config.CMS_URL)
        print(f"✓ CMS 페이지 접속: {config.CMS_URL}")
        time.sleep(3)  # 페이지 로드 대기
    
    def navigate_to_inventory_page(self, date_str=None, do_select_rooms=True):
        """인벤토리 관리_객실별 페이지로 이동"""
        try:
            print("\n📋 인벤토리 관리 페이지로 이동 중...")
            # 직접 URL로 이동
            inventory_url = "https://wingscms.com/#/app/cm/cm03_0300"
            self.driver.get(inventory_url)
            print(f"  ✓ 인벤토리 관리_객실별 페이지 이동: {inventory_url}")
            time.sleep(3)  # 페이지 로드 대기

            # 입력받은 시작일이 없으면 오늘 날짜로 셋팅
            if not date_str or str(date_str).strip() == "":
                date_str = datetime.now().strftime("%Y-%m-%d")
            self.set_date(date_str)
            # 호텔 객실 선택 및 필터 설정은 최초 1회만
            if do_select_rooms:
                self.select_all_rooms()
            return True
        except Exception as e:
            print(f"❌ 페이지 이동 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_date(self, date_str):
        """날짜 설정 (형식: YYYY-MM-DD)"""
        try:
            print(f"\n📅 날짜 설정 중: {date_str}")
            
            # 날짜 입력 필드 찾기 및 클릭
            date_input = self.wait.until(
                EC.element_to_be_clickable((By.ID, "startDatePicker"))
            )
            date_input.click()
            print("  ✓ 달력 열기")
            time.sleep(1)
            

            # 입력받은 날짜 파싱
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            target_year = str(dt.year)
            target_month = dt.strftime("%B")  # 영어 월명
            target_day = str(dt.day)

            # 달력 네비게이션으로 목표 년월로 이동
            max_clicks = 50
            clicks = 0
            print(f"  달력을 {target_year}년 {target_month}로 이동 중...")
            while clicks < max_clicks:
                try:
                    current_month_year = self.driver.find_element(
                        By.CSS_SELECTOR,
                        ".react-datepicker__current-month"
                    ).text
                    print(f"    현재: {current_month_year}")
                    if target_month in current_month_year and target_year in current_month_year:
                        print(f"  ✓ 목표 도달: {current_month_year}")
                        break
                    next_button = self.driver.find_element(
                        By.CSS_SELECTOR,
                        ".react-datepicker__navigation--next"
                    )
                    next_button.click()
                    time.sleep(0.5)
                    clicks += 1
                except Exception as e:
                    print(f"  ⚠ 네비게이션 중 오류: {e}")
                    break

            # 해당 일(day) 클릭
            time.sleep(0.5)
            day_element = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    f"//div[contains(@class, 'react-datepicker__day') and not(contains(@class, 'outside-month')) and text()='{target_day}']"
                ))
            )
            day_element.click()
            print(f"  ✓ {date_str} 날짜 선택 완료")
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print(f"⚠ 날짜 설정 실패: {e}")
            print("수동으로 날짜를 선택해주세요.")
            import traceback
            traceback.print_exc()
            return False
    
    def select_all_rooms(self):
        """Single Room, Twin Room, Triple Room만 선택"""
        try:
            print("\n🏨 호텔 객실 선택 중...")
            
            # 드롭다운 버튼 클릭
            dropdown_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "hotelRoomSearch__button__button"))
            )
            dropdown_button.click()
            print("  ✓ 객실 선택 드롭다운 열기")
            time.sleep(1.5)
            
            # 먼저 모든 옵션 찾기 (전체 체크 해제용)
            all_options = self.driver.find_elements(By.XPATH, "//div[@role='option' and contains(@id, 'hotelRoomSearch-option-')]")
            print(f"  → 전체 옵션 {len(all_options)}개 찾음")
            
            # 모든 옵션 체크 해제
            for option in all_options:
                is_selected = option.get_attribute("aria-selected")
                data_selected = option.get_attribute("data-selected")
                
                # 체크되어 있으면 클릭하여 해제
                if is_selected == "true" or (data_selected and data_selected != ""):
                    option_text = option.text
                    self.driver.execute_script("arguments[0].click();", option)
                    print(f"  → '{option_text}' 체크 해제")
                    time.sleep(0.3)
            
            time.sleep(1)
            
            # Single Room, Twin Room, Double Room, Triple Room 선택
            target_rooms = ["Single Room", "Twin Room", "Double Room", "Triple Room"]
            
            for room_name in target_rooms:
                try:
                    # 옵션 찾기 (텍스트로)
                    room_option = self.driver.find_element(
                        By.XPATH,
                        f"//div[@role='option' and contains(@id, 'hotelRoomSearch-option-') and text()='{room_name}']"
                    )
                    
                    # 체크 상태 확인
                    is_selected = room_option.get_attribute("aria-selected")
                    data_selected = room_option.get_attribute("data-selected")
                    
                    # 체크되어 있지 않으면 클릭
                    if is_selected != "true" and (not data_selected or data_selected == ""):
                        self.driver.execute_script("arguments[0].click();", room_option)
                        print(f"  ✓ {room_name} 선택")
                        time.sleep(0.5)
                    else:
                        print(f"  ✓ {room_name} 이미 선택됨")
                        
                except Exception as e:
                    print(f"  ⚠ {room_name} 선택 실패: {e}")
            
            time.sleep(1)
            
            # 조회 버튼 클릭
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "searchBtn"))
            )
            search_button.click()
            print("  ✓ 조회 버튼 클릭 - 방 목록 로딩 중...")
            time.sleep(3)  # 방 목록이 로드될 때까지 대기
            
            print("✅ Single Room, Twin Room, Triple Room 목록이 표시되었습니다!")
            
            # 필터 설정 (필수)
            self.apply_filter()
            
            return True
            
        except Exception as e:
            print(f"⚠ 객실 선택 자동화 실패: {e}")
            print("수동으로 객실을 선택하고 조회 버튼을 눌러주세요.")
            import traceback
            traceback.print_exc()
            return False
    
    def apply_filter(self):
        """필터에서 판매가능객실만 선택 (재시도 로직 포함)"""
        print("\n🔍 필터 설정 시도 중...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"  ⟳ 재시도 {attempt}/{max_retries-1}...")
                    time.sleep(3)
                
                # 1단계: 필터 아이콘 클릭하여 사이드 패널 열기
                try:
                    filter_button = self.wait.until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "filter-ico"))
                    )
                except:
                    filter_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//span[@class='filter-ico']"))
                    )
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", filter_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", filter_button)
                print("  ✓ 필터 패널 열기")
                time.sleep(3)  # 패널이 완전히 열릴 때까지 대기
                
                # 2단계: 노출정보 드롭다운 클릭
                exposure_dropdown = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "COMN_CN__button__button"))
                )
                self.driver.execute_script("arguments[0].click();", exposure_dropdown)
                print("  ✓ 노출정보 드롭다운 열기")
                time.sleep(2)
                
                # 3단계: 모든 체크박스 해제 후 "판매가능객실"만 체크
                # 먼저 모든 옵션 찾기
                all_options = self.driver.find_elements(By.XPATH, "//div[@role='option' and contains(@id, 'COMN_CN-option-')]")
                print(f"  → 전체 옵션 {len(all_options)}개 찾음")
                
                # 모든 옵션 체크 해제
                for option in all_options:
                    is_selected = option.get_attribute("aria-selected")
                    data_selected = option.get_attribute("data-selected")
                    
                    # 체크되어 있으면 클릭하여 해제
                    if is_selected == "true" or (data_selected and data_selected != ""):
                        option_text = option.text
                        self.driver.execute_script("arguments[0].click();", option)
                        print(f"  → '{option_text}' 체크 해제")
                        time.sleep(0.3)
                
                time.sleep(1)
                
                # "판매가능객실"만 체크
                sales_room_option = self.wait.until(
                    EC.presence_of_element_located((By.ID, "COMN_CN-option-0"))
                )
                
                is_selected = sales_room_option.get_attribute("aria-selected")
                data_selected = sales_room_option.get_attribute("data-selected")
                
                if is_selected != "true" and (not data_selected or data_selected == ""):
                    self.driver.execute_script("arguments[0].click();", sales_room_option)
                    print("  ✓ 판매가능객실 체크")
                    time.sleep(2)
                else:
                    print("  ✓ 판매가능객실 이미 체크됨")
                    time.sleep(1)
                
                # 4단계: 검색 버튼 클릭 (여러 방법 시도)
                search_button = None
                try:
                    # 방법 1: 텍스트로 찾기
                    search_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), '검색')]"))
                    )
                    print("  → 검색 버튼 찾음 (텍스트)")
                except:
                    try:
                        # 방법 2: 아이콘 클래스로 찾기
                        search_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary')]//i[contains(@class, 'pe-7s-search')]"))
                        )
                        # 부모 버튼 요소로 이동
                        search_button = search_button.find_element(By.XPATH, "..")
                        print("  → 검색 버튼 찾음 (아이콘)")
                    except:
                        # 방법 3: w90 클래스로 찾기
                        search_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'w90') and contains(@class, 'btn-primary')]"))
                        )
                        print("  → 검색 버튼 찾음 (클래스)")
                
                # 스크롤하여 버튼이 보이도록
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_button)
                time.sleep(1)
                
                # 여러 방법으로 클릭 시도
                try:
                    search_button.click()
                    print("  ✓ 검색 버튼 클릭 (일반 클릭)")
                except:
                    self.driver.execute_script("arguments[0].click();", search_button)
                    print("  ✓ 검색 버튼 클릭 (JavaScript)")
                
                time.sleep(5)  # 결과 로딩 충분히 대기
                
                print("✅ 필터 적용 완료 - 판매가능객실만 표시됨!")
                return True
                
            except Exception as e:
                print(f"  ✗ 시도 실패: {e}")
                if attempt == max_retries - 1:
                    print(f"\n❌ 필터 적용 {max_retries}회 시도 후 실패")
                    raise Exception(f"필터 적용 실패 - 입력칸이 생성되지 않아 작업을 계속할 수 없습니다: {e}")
                continue
        
        return False
    
    def calculate_available_rooms(self, room_type, remaining, booked, max_count):
        """
        판매가능객실 수량 계산
        
        Args:
            room_type: 'SINGLE', 'TWIN', 'TRIPLE'
            remaining: 잔여 수
            booked: 예약 수
            max_count: 최대 수량
        
        Returns:
            판매가능객실 수량 (None이면 빈칸 = 모두 오픈), 또는 'ALERT:메시지'
        """
        print(f"[정책진단] room_type={room_type}, remaining={remaining}, booked={booked}, max_count={max_count}")

        if room_type in ('SINGLE', 'TWIN', 'DOUBLE'):
            # 더블룸: 예약 3개 이상이면 모두 오픈(빈칸), 아니면 예약+2~3개(랜덤)
            if room_type == 'DOUBLE':
                if booked >= 3:
                    print(f"[정책결과] => None (더블룸 예약 3 이상, 모두 오픈)")
                    return None
                else:
                    val = booked + 2
                    print(f"[정책결과] => {val} (더블룸 예약+2 고정)")
                    return val

        if room_type == 'SINGLE':
            if remaining <= 4:
                print(f"[정책결과] => None (싱글룸 잔여 4 이하, 모두 오픈)")
                return None
            val = booked + 4
            print(f"[정책결과] => {val} (싱글룸 예약+4 고정)")
            return val

        elif room_type == 'TWIN':
            if remaining <= 2:
                print(f"[정책결과] => None (트윈룸 잔여 2 이하, 모두 오픈)")
                return None
            if booked >= 6:
                print(f"[정책결과] => {booked + 2} (예약+2)")
                return booked + 2
            else:
                val = booked + random.randint(2, 3)
                print(f"[정책결과] => {val} (예약+2~3 랜덤)")
                return val

        elif room_type == 'TRIPLE':
            if booked >= 5:
                print(f"[정책결과] => ALERT:트리플룸 예약 {booked}건 - 수동 확인 필요")
                return f"ALERT:트리플룸 예약 {booked}건 - 수동 확인 필요"
            elif booked == 4:
                print(f"[정책결과] => {booked + 1} (예약=4, +1)")
                return booked + 1  # 5
            else:
                print(f"[정책결과] => {booked + 2} (예약<4, +2)")
                return booked + 2

        val = random.randint(2, 3)
        print(f"[정책결과] => {val} (기본값)")
        return val
    
    def set_room_availability_by_date(self):
        from datetime import datetime, timedelta
        run_date = datetime.now().strftime('%Y-%m-%d')
        # 현재 날짜 추출 (달력에서 선택된 값)
        try:
            date_input = self.driver.find_element(By.ID, "startDatePicker")
            current_date = date_input.get_attribute("value")
        except:
            current_date = None
        """날짜별로 각 방 타입의 판매가능객실 설정"""
        try:
            print("\n🏨 판매가능객실 자동 설정 중...")
            time.sleep(3)
            
            results = {}
            
            for room_key, room_name in config.ROOM_TYPES.items():
                max_count = config.ROOM_MAX_COUNT.get(room_key, 10)
                print(f"\n📝 {room_name} 처리 중 (최대: {max_count}개)")
                
                try:
                    # 1. 먼저 룸 타입의 expandable 버튼 찾기 (여러 방법 시도)
                    expandable_span = None
                    try:
                        # 방법 1: class와 텍스트로 찾기
                        expandable_span = self.driver.find_element(
                            By.XPATH,
                            f"//span[contains(@class, 'expandable') and contains(text(), '{room_name}')]"
                        )
                    except:
                        # 방법 2: 아이콘 포함된 span으로 찾기
                        expandable_span = self.driver.find_element(
                            By.XPATH,
                            f"//span[@class='expandable' and contains(., '{room_name}')]"
                        )
                    
                    # 2. expandable 버튼 클릭하여 하위 메뉴 펼치기
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expandable_span)
                    time.sleep(1)
                    
                    # 이미 펼쳐져 있는지 확인 (closes 아이콘이 보이는지)
                    parent_element = expandable_span.find_element(By.XPATH, "./ancestor::td")
                    closes_icon = parent_element.find_elements(By.CSS_SELECTOR, "i.closes")
                    
                    if not closes_icon or not closes_icon[0].is_displayed():
                        # 펼쳐져 있지 않으면 클릭
                        self.driver.execute_script("arguments[0].click();", expandable_span)
                        print(f"  ✓ {room_name} 하위 메뉴 펼침")
                        time.sleep(2)  # 하위 메뉴가 펼쳐질 때까지 대기
                    else:
                        print(f"  ✓ {room_name} 이미 펼쳐져 있음")
                    
                    # 3. 펼쳐진 하위 행들 중 "판매가능객실" 행의 입력 필드만 찾기
                    input_fields = []
                    try:
                        # expandable span이 있는 tr 찾기
                        expandable_tr = expandable_span.find_element(By.XPATH, "./ancestor::tr")
                        
                        # 다음 형제 tr들을 순회하면서 "판매가능객실"이 있는 tr 찾기
                        next_tr = expandable_tr
                        found_sales_row = False
                        
                        for i in range(20):  # 최대 20개 행 확인
                            try:
                                next_tr = next_tr.find_element(By.XPATH, "./following-sibling::tr[1]")
                                
                                # 다음 expandable을 만나면 중단 (다른 룸 타입 시작)
                                if next_tr.find_elements(By.CSS_SELECTOR, "span.expandable"):
                                    print(f"  → 다음 룸 타입 도달, 검색 중단")
                                    break
                                
                                # 이 tr에 "판매가능객실" 텍스트가 있는지 확인
                                tr_text = next_tr.text
                                if "판매가능객실" in tr_text:
                                    # 이 tr의 input 필드들 찾기
                                    row_inputs = next_tr.find_elements(By.CSS_SELECTOR, "input[type='text']")
                                    if row_inputs:
                                        input_fields = row_inputs
                                        found_sales_row = True
                                        print(f"  → {room_name}의 판매가능객실 행 발견: {len(input_fields)}개 입력 필드")
                                        break
                                
                            except:
                                break
                        
                        if not found_sales_row:
                            print(f"  ⚠ {room_name}의 판매가능객실 행을 찾을 수 없음")
                            results[room_name] = False
                            continue
                        
                    except Exception as e:
                        print(f"  ⚠ 판매가능객실 행 찾기 실패: {e}")
                        import traceback
                        traceback.print_exc()
                        results[room_name] = False
                        continue
                    
                    count = 0
                    alert_count = 0
                    skip_count = 0
                    # 잔여/예약 tr 찾기: 판매가능객실 tr의 이전 형제 tr 중 data-field="REMANING"인 tr
                    sales_tr = input_fields[0].find_element(By.XPATH, "./ancestor::tr")
                    remain_tr = sales_tr.find_element(By.XPATH, "./preceding-sibling::tr[@data-field='REMANING'][1]")
                    remain_tds = remain_tr.find_elements(By.TAG_NAME, "td")[2:]  # 앞 2개는 라벨/헤더

                    for idx, input_field in enumerate(input_fields):
                        try:
                            current_value = input_field.get_attribute('value')
                            remain_td = remain_tds[idx]
                            spans = remain_td.find_elements(By.TAG_NAME, "span")
                            remaining = int(spans[0].text.strip())
                            booked = int(spans[1].text.strip())
                            if idx < 3:
                                print(f"    [{idx+1}] 전여:{remaining}, 예약:{booked}")
                            print(f"[잔여/예약 진단] idx={idx+1}, room={room_key}, remaining={remaining}, booked={booked}, current_value={current_value}")
                        except Exception as e:
                            print(f"[잔여/예약 진단] idx={idx+1}, room={room_key}, remain_td 파싱 실패: {e}")
                            remaining = max_count
                            booked = 0
                        
                        try:
                            # 판매가능객실 수량 계산
                            available = self.calculate_available_rooms(
                                room_key, remaining, booked, max_count
                            )

                            # ALERT 메시지 처리
                            if isinstance(available, str) and available.startswith('ALERT:'):
                                alert_msg = available.replace('ALERT:', '')
                                print(f"    [{idx+1}] ⚠️ {alert_msg}")
                                alert_count += 1
                                continue

                            # ★ 빈칸→빈칸이면 완전 생략
                            if (current_value is None or str(current_value).strip() == "") and available is None:
                                skip_count += 1
                                if skip_count <= 3:
                                    print(f"    [{idx+1}] ✓ 건너뛰기: 빈칸→빈칸 (예약:{booked})")
                                count += 1
                                continue

                            # 값이 있고 조건에 맞으면 즉시 건너뛰기 (스크롤/클릭 없이)
                            # 기존 값과 기대값이 다르면 반드시 값을 입력하도록 수정
                            if current_value and str(current_value).strip():
                                try:
                                    existing_val = int(current_value)
                                    if available is not None and existing_val == available:
                                        skip_count += 1
                                        if skip_count <= 3:
                                            print(f"    [{idx+1}] ✓ 건너뛰기: {existing_val} (정책 기대값과 동일)")
                                        count += 1
                                        continue
                                except:
                                    pass

                            # 변경 이력 기록 (변경 발생 시)
                            if str(current_value) != ("" if available is None else str(available)):
                                # index에 따라 실제 날짜 계산
                                try:
                                    base_date = datetime.strptime(current_date, "%Y-%m-%d")
                                    real_date = (base_date + timedelta(days=idx)).strftime("%Y-%m-%d")
                                except Exception as e:
                                    real_date = current_date
                                self.change_history.append({
                                    'run_date': run_date,
                                    'date': real_date,
                                    'room_type': room_name,
                                    'old_value': current_value,
                                    'new_value': available
                                })
                            
                            # 입력 필드가 화면에 보이도록 스크롤
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_field)
                            time.sleep(0.5)
                            
                            # 입력 필드 활성화 및 포커스
                            self.driver.execute_script("arguments[0].removeAttribute('readonly');", input_field)
                            self.driver.execute_script("arguments[0].removeAttribute('disabled');", input_field)
                            input_field.click()
                            time.sleep(0.3)
                            
                            # 입력 필드에 값 설정 (여러 방법 시도)
                            if available is None:
                                # 빈칸 (모두 오픈)
                                try:
                                    input_field.clear()
                                except:
                                    self.driver.execute_script("arguments[0].value = '';", input_field)
                                print(f"    [{idx+1}] 빈칸으로 설정 (모두 오픈)")

                            else:
                                value_str = str(available)
                                success = False
                                for attempt in range(3):
                                    # 방법 1: clear + send_keys
                                    try:
                                        input_field.clear()
                                        time.sleep(0.2)
                                        input_field.send_keys(value_str)
                                        time.sleep(0.2)
                                    except Exception as e1:
                                        print(f"    방법1 실패, 방법2 시도: {e1}")
                                        # 방법 2: JavaScript로 직접 설정
                                        try:
                                            self.driver.execute_script(f"arguments[0].value = '';", input_field)
                                            time.sleep(0.1)
                                            self.driver.execute_script(f"arguments[0].value = '{value_str}';", input_field)
                                        except Exception as e2:
                                            print(f"    방법2도 실패: {e2}")
                                    # 변경 이벤트 트리거
                                    self.driver.execute_script("""
                                        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                                        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                                    """, input_field)
                                    # blur 이벤트로 완료
                                    input_field.send_keys(Keys.TAB)
                                    time.sleep(0.2)
                                    # 입력값 검증
                                    actual_val = input_field.get_attribute('value')
                                    if actual_val == value_str:
                                        print(f"    [{idx+1}] 값 입력 성공: {value_str} (예약:{booked}, 잔여:{remaining})")
                                        success = True
                                        break
                                    else:
                                        print(f"    [{idx+1}] 값 입력 불일치: 기대={value_str}, 실제={actual_val} (재시도 {attempt+1}/3)")
                                if not success:
                                    print(f"    [{idx+1}] ⚠️ 최종 입력 실패: {value_str} (예약:{booked}, 잔여:{remaining})")
                                count += 1
                            
                        except Exception as e:
                            print(f"  ⚠ 입력 필드 {idx+1} 설정 실패: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                    
                    print(f"  ✓ {room_name}: {count}개 처리 완료 (건너뛰기: {skip_count}개)")
                    if alert_count > 0:
                        print(f"  ⚠️ {room_name}: {alert_count}개 알림 - 수동 확인 필요")
                    results[room_name] = True
                    
                except Exception as e:
                    print(f"  ❌ {room_name} 설정 실패: {e}")
                    import traceback
                    traceback.print_exc()
                    results[room_name] = False
            
            # 저장 버튼 클릭
            print("\n💾 저장 중...")
            save_button = self.driver.find_element(
                By.CSS_SELECTOR,
                "#scrollArea > div:nth-child(1) > div.app-main > div.app-main__outer > div > div > div.app-footer.fixFooter.TabsAnimation-appear.TabsAnimation-appear-active > div > div > button.btn-wide.btn-shadow.w140.btn.btn-primary.btn-lg"
            )
            save_button.click()
            time.sleep(2)
            
            # "저장되었습니다" 팝업의 확인 버튼 클릭
            try:
                confirm_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., '확인')]"))
                )
                confirm_button.click()
                print("  ✓ 저장 확인 완료")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠ 확인 버튼 클릭 건너뜀: {e}")
            
            print("✅ 저장 완료!")
            
            return results
            
        except Exception as e:
            print(f"❌ 판매가능객실 설정 실패: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
    def set_room_availability(self, room_type, available_rooms):
        """
        특정 방 타입의 예약 가능 수량 설정
        
        Args:
            room_type (str): 방 타입 ('SINGLE', 'TWIN', 'DOUBLE', 'TRIPLE')
            available_rooms (int): 예약 가능한 방 수량
        """
        try:
            room_name = config.ROOM_TYPES.get(room_type)
            if not room_name:
                print(f"❌ 올바르지 않은 방 타입: {room_type}")
                return False
            
            print(f"\n🔄 {room_name} 예약 가능 수량 설정 중: {available_rooms}개")
            
            # 실제 CMS의 HTML 구조에 맞게 수정 필요
            # 예시: 방 타입별 입력 필드 찾기
            # XPath는 실제 페이지 구조를 확인 후 수정해야 합니다
            
            # 방법 1: 텍스트로 요소 찾기
            room_element = self.wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//td[contains(text(), '{room_name}')]")
                )
            )
            
            # 해당 행에서 입력 필드 찾기
            # 실제 구조에 맞게 수정 필요
            input_field = room_element.find_element(
                By.XPATH, 
                ".//following::input[@type='number' or @type='text'][1]"
            )
            
            # 기존 값 지우고 새 값 입력
            input_field.clear()
            input_field.send_keys(str(available_rooms))
            
            print(f"✓ {room_name} 수량 설정 완료: {available_rooms}개")
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"❌ {room_name} 설정 실패: {e}")
            return False
    
    def set_all_rooms(self, room_settings):
        """
        모든 방 타입의 예약 가능 수량을 한번에 설정
        
        Args:
            room_settings (dict): {'SINGLE': 5, 'TWIN': 3, 'DOUBLE': 4, 'TRIPLE': 2}
        """
        print("\n" + "="*50)
        print("전체 방 예약 가능 수량 설정 시작")
        print("="*50)
        
        results = {}
        for room_type, count in room_settings.items():
            results[room_type] = self.set_room_availability(room_type, count)
        
        # 저장 버튼 클릭 (실제 구조에 맞게 수정)
        try:
            save_button = self.driver.find_element(
                By.XPATH, 
                "//button[contains(text(), '저장') or contains(text(), 'Save')]"
            )
            save_button.click()
            print("\n✓ 변경사항 저장 완료")
            time.sleep(2)
        except Exception as e:
            print(f"\n⚠ 저장 버튼을 찾을 수 없습니다: {e}")
            print("수동으로 저장해주세요.")
        
        # 결과 출력
        print("\n" + "="*50)
        print("설정 결과:")
        for room_type, success in results.items():
            status = "✓ 성공" if success else "❌ 실패"
            print(f"  {config.ROOM_TYPES[room_type]}: {status}")
        print("="*50)
        
        return results
    
    def get_current_availability(self):
        """현재 각 방의 예약 가능 수량 조회"""
        print("\n현재 예약 가능 수량 조회 중...")
        
        current_status = {}
        for room_type, room_name in config.ROOM_TYPES.items():
            try:
                # 실제 구조에 맞게 수정 필요
                room_element = self.driver.find_element(
                    By.XPATH, 
                    f"//td[contains(text(), '{room_name}')]"
                )
                input_field = room_element.find_element(
                    By.XPATH,
                    ".//following::input[@type='number' or @type='text'][1]"
                )
                current_value = input_field.get_attribute('value')
                current_status[room_type] = current_value
                print(f"  {room_name}: {current_value}개")
                
            except Exception as e:
                print(f"  {room_name}: 조회 실패 ({e})")
                current_status[room_type] = None
        
        return current_status
    
    def clear_all_room_availability(self):
        """모든 방 타입의 판매가능객실 입력값을 지우고 저장"""
        try:
            print("\n🧹 모든 판매가능객실 입력값 초기화 중...")
            time.sleep(3)
            
            results = {}
            
            for room_key, room_name in config.ROOM_TYPES.items():
                print(f"\n📝 {room_name} 초기화 중...")
                
                try:
                    # 1. expandable 버튼 찾기
                    expandable_span = None
                    try:
                        expandable_span = self.driver.find_element(
                            By.XPATH,
                            f"//span[contains(@class, 'expandable') and contains(text(), '{room_name}')]"
                        )
                    except:
                        expandable_span = self.driver.find_element(
                            By.XPATH,
                            f"//span[@class='expandable' and contains(., '{room_name}')]"
                        )
                    
                    # 2. 하위 메뉴 펼치기
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", expandable_span)
                    time.sleep(1)
                    
                    parent_element = expandable_span.find_element(By.XPATH, "./ancestor::td")
                    closes_icon = parent_element.find_elements(By.CSS_SELECTOR, "i.closes")
                    
                    if not closes_icon or not closes_icon[0].is_displayed():
                        self.driver.execute_script("arguments[0].click();", expandable_span)
                        print(f"  ✓ {room_name} 하위 메뉴 펼침")
                        time.sleep(2)
                    else:
                        print(f"  ✓ {room_name} 이미 펼쳐져 있음")
                    
                    # 3. 판매가능객실 행의 입력 필드 찾기
                    input_fields = []
                    try:
                        sales_available_row = self.driver.find_element(
                            By.XPATH,
                            f"//span[contains(@class, 'expandable') and contains(text(), '{room_name}')]/ancestor::tr/following-sibling::tr[.//td[contains(text(), '판매가능객실')]]"
                        )
                        
                        input_fields = sales_available_row.find_elements(By.CSS_SELECTOR, "input[type='text']")
                        print(f"  → {len(input_fields)}개 입력 필드 찾음")
                        
                    except Exception as e:
                        print(f"  ⚠ 판매가능객실 행을 찾을 수 없음: {e}")
                        results[room_name] = False
                        continue
                    
                    # 4. 모든 입력값 지우기
                    count = 0
                    for input_field in input_fields:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", input_field)
                            time.sleep(0.1)
                            
                            # 값을 빈 문자열로 설정
                            self.driver.execute_script("arguments[0].value = '';", input_field)
                            self.driver.execute_script("arguments[0].focus(); arguments[0].blur();", input_field)
                            
                            count += 1
                            
                        except Exception as e:
                            continue
                    
                    print(f"  ✓ {room_name}: {count}개 입력값 초기화 완료")
                    results[room_name] = True
                    
                except Exception as e:
                    print(f"  ❌ {room_name} 초기화 실패: {e}")
                    results[room_name] = False
            
            # 저장 버튼 클릭
            print("\n💾 저장 중...")
            save_button = self.driver.find_element(
                By.CSS_SELECTOR,
                "#scrollArea > div:nth-child(1) > div.app-main > div.app-main__outer > div > div > div.app-footer.fixFooter.TabsAnimation-appear.TabsAnimation-appear-active > div > div > button.btn-wide.btn-shadow.w140.btn.btn-primary.btn-lg"
            )
            save_button.click()
            time.sleep(2)
            
            # "저장되었습니다" 팝업의 확인 버튼 클릭
            try:
                confirm_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., '확인')]"))
                )
                confirm_button.click()
                print("  ✓ 저장 확인 완료")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠ 확인 버튼 클릭 건너뜀: {e}")
            
            print("✅ 초기화 및 저장 완료!")
            
            return results
            
        except Exception as e:
            print(f"❌ 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def close(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            print("\n✓ 브라우저 종료")
    
    def run_for_date_range(self):
        """날짜 범위에 대해 자동 실행"""
        start_date = datetime(2026, 11, 1)
        end_date = datetime(2026, 12, 31)
        delta = timedelta(days=15)
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            print(f"\n===== {date_str} ~ 15일치 처리 시작 =====")
            self.set_date(date_str)
            self.set_room_availability_by_date()
            # 15일 뒤로 이동
            current_date += delta
    
    def run_for_date_range_with_input(self, start_date_str, end_date_str):
        """
        시작일(YYYY-MM-DD) 문자열을 받아 15일(시작일~시작일+14일)만 처리
        최초 1회만 객실/필터 설정, 이후에는 날짜만 바꾸고 반드시 조회 버튼을 누름
        """
        # 시작일 미입력 시 오늘 날짜로 대체
        if not start_date_str or start_date_str.strip() == "":
            start_date_str = datetime.now().strftime("%Y-%m-%d")
            print(f"시작일 미입력: 오늘 날짜({start_date_str})로 자동 설정합니다.")

        if not end_date_str or end_date_str.strip() == "":
            # 종료일 미입력 시 시작일로부터 1년 뒤로 설정
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            try:
                end_date = start_date.replace(year=start_date.year + 1)
            except ValueError:
                # 윤년 등으로 2월 29일 예외 처리
                end_date = start_date + timedelta(days=365)
            print(f"종료일 미입력: 시작일로부터 1년 뒤({end_date.strftime('%Y-%m-%d')})로 자동 설정합니다.")
        else:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        current_date = start_date
        # 최초 1회: 객실/필터 설정 포함
        if current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            end_range = current_date + timedelta(days=14)
            print(f"\n===== {date_str} ~ {end_range.strftime('%Y-%m-%d')} 처리 시작 =====")
            self.navigate_to_inventory_page(date_str, do_select_rooms=True)
            self.set_room_availability_by_date()
            current_date += timedelta(days=15)
        # 이후 반복: 날짜만 바꾸고 조회 버튼 누름
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            end_range = current_date + timedelta(days=14)
            print(f"\n===== {date_str} ~ {end_range.strftime('%Y-%m-%d')} 처리 시작 =====")
            self.set_date(date_str)
            self.search_rooms_by_date()
            self.set_room_availability_by_date()
            current_date += timedelta(days=15)


def main():
    """메인 실행 함수"""
    print("\n처리할 기간을 입력하세요.")
    start_date_str = input("시작일 (YYYY-MM-DD): ")
    end_date_str = input("종료일 (YYYY-MM-DD): ")

    controller = HotelCMSController()

    try:
        # 1. 브라우저 초기화
        controller.setup_driver()

        # 2. CMS 페이지 접속
        controller.navigate_to_cms()

        # 3. 자동 로그인
        login_success = controller.login()

        if not login_success:
            # 자동 로그인 실패 시 수동 로그인 대기
            print("\n수동으로 로그인을 완료한 후 Enter를 눌러주세요...")
            input()

        # 4. 최초 1회 인벤토리 관리_객실별 페이지 이동 및 객실 선택/필터 설정은 run_for_date_range_with_input에서 처리

        # 5. 기간 입력받아 15일 단위 자동 처리 (이후 반복에서는 객실 선택/필터 설정 생략)

        controller.run_for_date_range_with_input(start_date_str, end_date_str)

        # 변경 이력 엑셀로 저장
        if controller.change_history:
            import pandas as pd
            df = pd.DataFrame(controller.change_history)
            df.to_excel("change_history.xlsx", index=False)
            print(f"\n변경 이력(change_history.xlsx) 저장 완료! 변경 건수: {len(df)}")
        else:
            print("\n변경된 내역이 없습니다.")

        print("\n" + "="*60)
        print("✅ 기간별 판매가능객실 설정 완료!")
        print("="*60)
        # 테스트 시에만 아래 두 줄을 사용하세요.
        # print("\n확인 후 Enter를 눌러 종료하세요...")
        # input()

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    finally:
        controller.close()


if __name__ == "__main__":
    main()
