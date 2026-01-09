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
import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.styles import PatternFill




class HotelCMSController:
    """호텔 CMS를 제어하는 클래스"""

    def highlight_closed_rooms_in_excel(self, target_date, closed_rooms):
        """마감된 방 타입을 엑셀 파일에서 노란색으로 하이라이트"""
        try:
            excel_path = os.path.join(os.path.dirname(__file__), "기준가격.xlsx")
            if not os.path.exists(excel_path):
                print(f"  ⚠ 하이라이트 대상 파일 없음: {excel_path}")
                return
            
            # openpyxl로 엑셀 파일 열기
            wb = load_workbook(excel_path)
            ws = wb.active
            
            # 첫 번째 열에서 대상 날짜 행 찾기
            target_row = None
            for row_idx, cell in enumerate(ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=1), 1):
                try:
                    cell_date = pd.Timestamp(cell[0].value).strftime("%Y-%m-%d")
                    if cell_date == target_date:
                        target_row = row_idx
                        break
                except Exception:
                    continue
            
            if target_row is None:
                print(f"  ⚠ 엑셀에서 {target_date} 행을 찾지 못했습니다.")
                return
            
            # 노란색 하이라이트 설정
            yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            
            # 마감된 방에 해당하는 셀에 하이라이트 적용
            for col_idx, cell in enumerate(ws.iter_rows(min_row=target_row, max_row=target_row, min_col=1, max_col=ws.max_column), 1):
                room_type = ws.cell(row=1, column=col_idx).value
                if room_type in closed_rooms:
                    cell[0].fill = yellow_fill
                    print(f"    → '{room_type}' 셀을 노란색으로 하이라이트함")
            
            # 파일 저장
            wb.save(excel_path)
            print(f"  ✓ {len(closed_rooms)}개 마감 방에 대해 엑셀 파일 업데이트 완료")
        except Exception as e:
            print(f"  ⚠ 엑셀 하이라이트 작업 실패: {e}")

    def load_base_prices_from_excel(self, target_date=None):
        """엑셀 파일에서 특정 날짜의 기준가 로드 (방 타입별 기준가)"""
        try:
            excel_path = os.path.join(os.path.dirname(__file__), "기준가격.xlsx")
            if not os.path.exists(excel_path):
                print(f"  ⚠ 기준가격.xlsx 파일을 찾지 못했습니다: {excel_path}")
                return {}
            
            # 기준값이 될 날짜 (기본: 오늘)
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            df = pd.read_excel(excel_path, sheet_name=0)
            
            # 첫 번째 열이 날짜 열이므로 날짜 형식으로 변환
            date_col = df.iloc[:, 0]
            
            # 일치하는 날짜 찾기
            matching_row = None
            for idx, date_val in enumerate(date_col):
                try:
                    # 날짜 값을 문자열로 변환해서 비교
                    date_str = pd.Timestamp(date_val).strftime("%Y-%m-%d")
                    if date_str == target_date:
                        matching_row = df.iloc[idx]
                        break
                except Exception:
                    continue
            
            if matching_row is None:
                print(f"  ⚠ 엑셀에서 {target_date}에 해당하는 행을 찾지 못했습니다. 첫 번째 행을 사용합니다.")
                matching_row = df.iloc[0]
            
            # 방 타입과 기준가 매핑
            base_prices = {}
            for col_idx in range(1, len(df.columns)):
                room_type = df.columns[col_idx]
                try:
                    price = int(float(matching_row.iloc[col_idx]))
                    base_prices[room_type] = price
                except (ValueError, TypeError):
                    continue
            
            print(f"  ✓ {target_date}의 기준가 {len(base_prices)}개 로드: {base_prices}")
            return base_prices
        except Exception as e:
            print(f"  ⚠ 기준가 로드 실패: {e}")
            return {}

    def auto_set_rates_by_rmo(self, start_date=None):
        """요금관리 메뉴에서 기준가를 기반으로 OTA별 요금 자동입력 (아고다=기준가, 나머지=기준가+5,000)"""
        try:
            # 날짜 설정
            if not start_date:
                start_date = datetime.now().strftime("%Y-%m-%d")
            
            # 해당 날짜의 기준가 로드
            base_prices = self.load_base_prices_from_excel(start_date)
            if not base_prices:
                print("  ⚠ 기준가를 로드하지 못했습니다. 계속 진행합니다.")
            
            # 마감된 방을 추적할 리스트
            closed_rooms_list = []

            print("\n📋 요금관리 메뉴로 이동 중...")
            rate_url = "https://wingscms.com/#/app/cm/cm03_0200"
            self.driver.get(rate_url)
            time.sleep(3)
            
            # 시작일 input 찾기 및 값 입력
            try:
                date_input = self.wait.until(EC.presence_of_element_located((By.ID, "startDatePicker")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_input)
                date_input.click()
                time.sleep(0.2)
                # 안전하게 초기화 후 값 세팅
                self.driver.execute_script("arguments[0].value = '';", date_input)
                self.driver.execute_script("arguments[0].focus();", date_input)
                date_input.clear()
                date_input.send_keys(start_date)
                # input/change 이벤트 트리거
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles:true}));", date_input)
                self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", date_input)
                date_input.send_keys(Keys.ENTER)
                print(f"  ✓ 시작일 입력: {start_date}")
            except Exception as e:
                print(f"  ⚠ 시작일 입력 실패: {e}")

            time.sleep(1)

            # 전체 객실 선택 (드롭다운 방식) — 드롭다운 열기 + selectall 클릭
            try:
                print("  → 전체 객실 선택 중...")
                # 드롭다운 열기
                try:
                    dropdown_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@id,'searchRoomType') and contains(@id,'button')]")))
                except Exception:
                    dropdown_btn = None
                
                if dropdown_btn:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_btn)
                    time.sleep(0.5)
                    dropdown_btn.click()
                    time.sleep(0.8)  # 드롭다운 메뉴 열릴 때까지 대기
                    print("  ✓ 드롭다운 열음")

                # selectall 요소 찾기
                sel_candidates = [
                    "[data-testid='selectall']",
                    "input[data-testid='selectall-checkbox']",
                    "span[data-testid='select-all-text']",
                    "#searchRoomType-option-selectall",
                ]
                select_all_el = None
                for sel in sel_candidates:
                    try:
                        select_all_el = self.driver.find_element(By.CSS_SELECTOR, sel)
                        if select_all_el:
                            break
                    except Exception:
                        continue

                if select_all_el:
                    try:
                        aria_sel = select_all_el.get_attribute("aria-selected")
                        data_sel = select_all_el.get_attribute("data-selected")
                        if aria_sel == "true" or (data_sel and data_sel != ""):
                            print("  ✓ 전체 객실 선택 (이미 선택됨)")
                        else:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_all_el)
                            time.sleep(0.3)
                            try:
                                select_all_el.click()
                            except Exception:
                                self.driver.execute_script("arguments[0].click();", select_all_el)
                            print("  ✓ 전체 객실 선택 (클릭함)")
                            time.sleep(0.5)
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", select_all_el)
                            print("  ✓ 전체 객실 선택 (JS 강제)")
                            time.sleep(0.5)
                        except Exception as e2:
                            print(f"  ⚠ 전체 객실 선택 실패: {e2}")
                else:
                    print("  ⚠ 전체 객실 selectall 요소를 찾지 못했습니다.")
            except Exception as e:
                print(f"  ⚠ 전체 객실 선택 실패: {e}")

            time.sleep(1)

            # 조회 버튼 클릭
            try:
                # 조회 버튼 찾기 (여러 방법으로 시도)
                search_btn = None
                try:
                    search_btn = self.driver.find_element(By.ID, "searchBtn")
                except Exception:
                    try:
                        search_btn = self.driver.find_element(By.XPATH, "//button[@id='searchBtn']")
                    except Exception:
                        try:
                            search_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'btn-primary') and .//i[contains(@class, 'search')]]")
                        except Exception:
                            pass
                
                if not search_btn:
                    print("  ⚠ 조회 버튼을 찾지 못했습니다.")
                else:
                    # 버튼이 클릭 가능할 때까지 대기
                    self.wait.until(EC.element_to_be_clickable((By.ID, "searchBtn")))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
                    time.sleep(0.5)
                    
                    # 클릭 시도 (일반 클릭 → JS 클릭)
                    try:
                        search_btn.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", search_btn)
                    
                    print("  ✓ 조회 버튼 클릭")
                    print("  ⏳ 페이지 로드 대기 중...")
                    # 페이지가 제대로 로드될 때까지 충분히 기다림
                    time.sleep(5)
                    # 추가로 RMO 버튼이 나타날 때까지 대기
                self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//span[contains(.,'RMO')]")))
                print("  ✓ 페이지 로드 완료")
            except Exception as e:
                print(f"  ⚠ 조회 버튼 클릭 또는 페이지 로드 실패: {e}")

            # 각 객실별 RMO 버튼 클릭 및 요금 입력 (하위 child 행에 반영)
            rmo_buttons = self.driver.find_elements(By.XPATH, "//span[contains(.,'RMO')]")
            print(f"  ✓ RMO 버튼 {len(rmo_buttons)}개 발견")
            for rmo_btn in rmo_buttons:
                try:
                    # RMO 버튼이 속한 행의 parent_id 먼저 파악
                    parent_tr = rmo_btn.find_element(By.XPATH, "ancestor::tr")
                    parent_id = None
                    try:
                        parent_td = parent_tr.find_element(By.XPATH, ".//td[@id]")
                        parent_id = parent_td.get_attribute("id")
                    except Exception:
                        pass

                    if not parent_id:
                        print("    ⚠ parent_id를 찾지 못해 건너뜁니다.")
                        continue

                    # 판매 상태 확인 (같은 방 타입의 판매 상태 행 찾기)
                    try:
                        # parent_tr의 바로 다음 행에서 data-field='CLOSE_YN' 찾기
                        status_row = parent_tr.find_element(By.XPATH, "following-sibling::tr[@data-field='CLOSE_YN'][1]")
                        status_text = status_row.text.strip()
                        
                        # "마감" 또는 "Close" 같은 텍스트 확인
                        if '마감' in status_text or 'close' in status_text.lower():
                            parent_label = parent_tr.text.strip()
                            # 방 타입명만 추출 (OTA 정보 제거)
                            room_type_for_excel = parent_label.split('-')[0].strip() if '-' in parent_label else parent_label
                            closed_rooms_list.append(room_type_for_excel)
                            print(f"    ⊘ '{parent_label}': 마감 상태 - 스킵")
                            continue
                    except Exception:
                        # 판매 상태 행을 찾지 못하면 계속 진행
                        pass

                    print(f"    → RMO 버튼 활성화 중 (parent_id: {parent_id})...")
                    
                    # RMO 버튼을 스크롤해서 보이게 하고 클릭
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", rmo_btn)
                    time.sleep(0.3)
                    
                    # RMO 버튼 클릭 (여러 방법으로 시도)
                    try:
                        rmo_btn.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", rmo_btn)
                    
                    time.sleep(0.5)
                    
                    # RMO 버튼 클릭 후 입력란 활성화 확인 (최대 3초 대기)
                    rmo_input_row = None
                    for attempt in range(6):  # 0.5초 × 6 = 최대 3초
                        try:
                            rmo_input_row = parent_tr.find_element(By.XPATH, "following-sibling::tr[@data-field='RM_RA'][1]")
                            # 입력란이 실제로 활성화되었는지 확인 (disabled 속성 확인)
                            rmo_inputs_check = rmo_input_row.find_elements(By.CSS_SELECTOR, "input[type='text']:not([disabled])")
                            if rmo_inputs_check:
                                print(f"    ✓ RMO 입력란 활성화 확인됨")
                                break
                        except Exception:
                            pass
                        if attempt < 5:
                            time.sleep(0.5)
                        rmo_input_row = None

                    if not rmo_input_row:
                        print("    ⚠ RMO 입력 행을 찾지 못해 건너뜁니다.")
                        continue

                    rmo_inputs = rmo_input_row.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    if not rmo_inputs:
                        print("    ⚠ RMO 입력란 없음, 건너뜀")
                        continue
                    
                    # RMO 행의 기준가를 엑셀에서 찾기
                    parent_label = parent_tr.text.strip()
                    base_price = None
                    
                    # 엑셀에서 해당 방 타입의 기준가 찾기 (정확한 매칭)
                    for room_type, price in base_prices.items():
                        # 방 타입명이 parent_label에 포함되어 있는지 확인
                        if room_type in parent_label:
                            base_price = price
                            print(f"    → 엑셀 기준가 매칭: '{room_type}' = {price:,}원")
                            break
                    
                    # 엑셀에서 못 찾으면 RMO 입력값 사용 (첫 번째 컬럼)
                    if base_price is None:
                        try:
                            val = (rmo_inputs[0].get_attribute('value') or '').replace(',', '').strip()
                            if val.isdigit():
                                base_price = int(val)
                                print(f"    → RMO 입력값 사용: {base_price:,}원")
                        except Exception:
                            pass
                    
                    if base_price is None:
                        print(f"    ⚠ '{parent_label}'에 대한 기준가를 찾지 못해 건너뜁니다.")
                        continue

                    # 하위 child tr들 찾기 (같은 parent_id) — parent_id는 이미 확인됨
                    try:
                        child_trs = self.driver.find_elements(By.XPATH, f"//tr[contains(@class,'child-{parent_id}') and @data-field='RM_RA']")
                    except Exception:
                        child_trs = []

                    if not child_trs:
                        print(f"    ⚠ 하위 요금 행(child-{parent_id})을 찾지 못했습니다.")
                        continue
                    else:
                        print(f"    → child-{parent_id} 행 {len(child_trs)}개 대상 (기준가: {base_price:,}원)")

                    # OTA 매핑: 기준가를 기반으로 계산 (아고다=기준가, 나머지=기준가+5,000~10,000원 랜덤)
                    def calc_new_val(label, base_price):
                        if base_price is None:
                            return None
                        label = label.lower()
                        if 'agoda' in label or '아고다' in label:
                            return base_price
                        # 그 외 모든 OTA: 기준가 + 5,000~10,000원 범위의 랜덤 값 (천원 단위)
                        random_addon = random.randint(5, 10) * 1000  # 5000, 6000, 7000, ..., 10000
                        return base_price + random_addon

                    for child_tr in child_trs:
                        try:
                            label = child_tr.text.strip()
                            inputs = child_tr.find_elements(By.CSS_SELECTOR, "input[type='text']")
                            if not inputs:
                                continue
                            
                            # 스크롤해서 해당 행이 화면에 보이도록
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", child_tr)
                            time.sleep(0.3)
                            
                            # 모든 input에 동일한 기준가 기반 OTA 가격 적용
                            new_val = calc_new_val(label, base_price)
                            if new_val is None:
                                continue
                            
                            for idx, inp in enumerate(inputs):
                                try:
                                    # 요소가 실제로 상호작용 가능한지 확인
                                    self.driver.execute_script("arguments[0].removeAttribute('readonly');", inp)
                                    # 요소가 display:none이면 스킵
                                    display = self.driver.execute_script("return window.getComputedStyle(arguments[0]).display;", inp)
                                    if display == 'none':
                                        continue
                                    

                                    # 포커스를 먼저 설정
                                    self.driver.execute_script("arguments[0].focus();", inp)
                                    time.sleep(0.1)
                                    inp.clear()
                                    inp.send_keys(f"{new_val:,}")
                                except Exception as e_input:
                                    # 개별 입력 실패는 무시하고 계속 진행
                                    pass
                            
                            display_status = self.driver.execute_script("return window.getComputedStyle(arguments[0]).display;", child_tr)
                            if display_status != 'none':
                                print(f"    → {label}: 입력 완료" if label else "    → (공백 행): 입력 완료")
                        except Exception as e_child:
                            pass  # 개별 child 행 실패는 조용히 무시

                    time.sleep(0.5)
                except Exception as e:
                    print(f"    ⚠ RMO 처리 중 오류: {e}")

            # 저장 버튼 클릭 (테스트 버전: 저장 생략)
            # try:
            #     save_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'저장')]")))
            #     save_btn.click()
            #     print("  ✓ 저장 버튼 클릭")
            #     time.sleep(2)
            # except Exception as e:
            #     print(f"  ⚠ 저장 버튼 클릭 실패: {e}")

            print("✓ 요금 자동입력 완료 (테스트 버전: 저장 미수행)")
            
            # 마감된 방이 있으면 엑셀 파일 업데이트
            if closed_rooms_list:
                print(f"\n📊 마감된 방 {len(closed_rooms_list)}개에 대해 엑셀 파일 업데이트 중...")
                self.highlight_closed_rooms_in_excel(start_date, closed_rooms_list)
        except Exception as e:
            print(f"❌ 요금 자동입력 전체 실패: {e}")
            import traceback
            traceback.print_exc()

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
            if remaining <= 4:
                print(f"[정책결과] => None (트윈룸 잔여 4 이하, 모두 오픈)")
                return None
            if remaining >= 3 and booked >= 6:
                print(f"[정책결과] => {booked + 2} (트윈룸 잔여 3이상 & 예약 6이상, 예약+2)")
                return booked + 2
            if remaining >= 3 and booked < 6:
                print(f"[정책결과] => {booked + 4} (트윈룸 잔여 3이상 & 예약 6미만, 예약+4)")
                return booked + 4

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
        # 시작일 미입력 시 오늘+3일로 자동 설정
        if not start_date_str or start_date_str.strip() == "":
            start_date = datetime.now() + timedelta(days=3)
            start_date_str = start_date.strftime("%Y-%m-%d")
            print(f"시작일 미입력: 오늘+3일({start_date_str})로 자동 설정합니다.")
        else:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        # 종료일 미입력 시 오늘+11개월로 자동 설정
        if not end_date_str or end_date_str.strip() == "":
            end_date = datetime.now() + timedelta(days=30*11)
            print(f"종료일 미입력: 오늘+11개월({end_date.strftime('%Y-%m-%d')})로 자동 설정합니다.")
        else:
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


    print("\n실행할 기능을 선택하세요:")
    print("1. 객실수 자동조정 (기간별)")
    print("2. 요금 자동입력 (RMO 기반)")
    option = input("번호 입력 (1 또는 2): ").strip()

    # 기능별 입력값 미리 받기
    if option == "1":
        print("\n[객실수 자동조정] 기간을 입력하세요.")
        start_date_str = input("시작일 (YYYY-MM-DD): ")
        end_date_str = input("종료일 (YYYY-MM-DD): ")
    elif option == "2":
        print("\n[요금 자동입력] 기간을 입력하세요.")
        start_date_str = input("시작일 (YYYY-MM-DD, 엔터시 오늘): ")
        end_date_str = input("종료일 (YYYY-MM-DD, 엔터시 시작일+14일): ")
    else:
        start_date_str = None
        end_date_str = None

    controller = HotelCMSController()

    try:
        controller.setup_driver()
        controller.navigate_to_cms()
        login_success = controller.login()
        if not login_success:
            print("\n수동으로 로그인을 완료한 후 Enter를 눌러주세요...")
            input()

        if option == "1":
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
        elif option == "2":
            # 미입력시 오늘 날짜로 자동
            if not start_date_str or start_date_str.strip() == "":
                start_date_str = datetime.now().strftime("%Y-%m-%d")
                print(f"시작일 미입력: 오늘({start_date_str})로 자동 설정합니다.")
            # 종료일 미입력시 시작일+14일로 자동 (테스트용 요금 자동입력)
            if not end_date_str or end_date_str.strip() == "":
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = start_dt + timedelta(days=14)
                end_date_str = end_date.strftime("%Y-%m-%d")
                print(f"종료일 미입력: 시작일+14일({end_date_str})로 자동 설정합니다.")
            else:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            # 날짜 범위 반복 (요금 자동입력)
            current_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            while current_date <= end_date:
                controller.auto_set_rates_by_rmo(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
            print("\n" + "="*60)
            print("✅ 요금 자동입력 완료!")
            print("="*60)
        else:
            print("잘못된 옵션입니다. 프로그램을 종료합니다.")

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
