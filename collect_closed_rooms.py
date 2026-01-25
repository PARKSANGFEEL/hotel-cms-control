# -*- coding: utf-8 -*-
"""
4번 마감객실 정보가져오기 (기간 반복, 기존 hotel_cms_controller.py 스타일)
- 시작일자/마감일자 입력 → 해당 기간 동안 마감객실 정보 수집
- 메뉴 선택 없이 바로 실행, 로그인 방식은 기존과 동일
"""
import os
import sys

import os
import sys
import io
import time
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# config.py에서 값 읽기 (환경변수 우선, 없으면 config.py)
try:
    import config
except ImportError:
    config = None

def get_config_value(env_name, config_attr, default=None):
    v = os.environ.get(env_name)
    if v:
        return v
    if config and hasattr(config, config_attr):
        return getattr(config, config_attr)
    return default

CMS_URL = get_config_value('CMS_URL', 'CMS_URL', 'https://wingscms.com/#/app/cm/cm03_0300')
CMS_COMPANY_ID = get_config_value('CMS_COMPANY_ID', 'CMS_COMPANY_ID', '')
CMS_USERNAME = get_config_value('CMS_USERNAME', 'CMS_USERNAME', '')
CMS_PASSWORD = get_config_value('CMS_PASSWORD', 'CMS_PASSWORD', '')
IMPLICIT_WAIT = int(get_config_value('IMPLICIT_WAIT', 'IMPLICIT_WAIT', 15))
HEADLESS = get_config_value('HEADLESS', 'HEADLESS', False)
if isinstance(HEADLESS, str):
    HEADLESS = HEADLESS.lower() in ("1", "true", "yes")
# 한글 방 타입 → Excel 기준 타입 매핑
KOREAN_TO_ROOM_TYPE = {
    '싱글': 'Single Room',
    '싱글룸': 'Single Room',
    '1인실': 'Single Room',
    '트윈': 'Twin Room',
    '트윈룸': 'Twin Room',
    '이코노미': 'Economy Double Room',
    '이코노미더블': 'Economy Double Room',
    '이코노미 더블': 'Economy Double Room',
    'economic': 'Economy Double Room',
    '더블': 'Double Room',
    '더블룸': 'Double Room',
    '트리플': 'Triple Room',
    '트리플룸': 'Triple Room',
    '3인실': 'Triple Room',
    '3인': 'Triple Room',
    '3p': 'Triple Room',
    '패밀리': 'Family Room',
    '가족': 'Family Room',
    '5인': 'Family 5p',
    '5p': 'Family 5p',
}


def log_highlight_cells(target_date, closed_rooms):
    """마감된 방 정보를 기준가격_하이라이트.json에 기록"""
    try:
        log_path = os.path.join(os.path.dirname(__file__), "기준가격_하이라이트.json")
        highlights = []
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    highlights = json.load(f)
            except Exception:
                pass
        # 중복 방지: 같은 날짜/방타입 이미 있으면 건너뜀
        for room_type in closed_rooms:
            if not any(h for h in highlights if h.get('date') == target_date and h.get('room_type') == room_type):
                highlights.append({'date': target_date, 'room_type': room_type})
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(highlights, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {len(closed_rooms)}개 마감 방 정보를 하이라이트 로그에 기록")
        print(f"    → 나중에 'py apply_highlights.py'로 엑셀에 반영하세요")
    except Exception as e:
        print(f"  ⚠ 하이라이트 로그 기록 실패: {e}")


def setup_driver():
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, IMPLICIT_WAIT)
    return driver, wait


def login(driver, wait):
    """CMS 로그인 (수동 로그인 지원)"""
    driver.get(CMS_URL)
    time.sleep(2)
    try:
        # 이미 로그인된 경우
        if "#/app" in driver.current_url:
            print("✓ 이미 로그인되어 있습니다.")
            return True
        # 로그인 폼이 보이면 자동 로그인 시도
        try:
            driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            print("  → 로그인 폼 발견, 로그인 진행...")
        except:
            print("✓ 로그인 폼이 없습니다 (이미 로그인된 상태)")
            return True
        # 입력값 없으면 수동 로그인 안내
        if not CMS_COMPANY_ID or not CMS_USERNAME or not CMS_PASSWORD:
            print("⚠ 환경변수에 로그인 정보가 없습니다. 수동으로 로그인 후 Enter...")
            input()
            return True
        # 자동 로그인
        company_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='컴퍼니'], input[placeholder*='ID']")))
        company_field.clear()
        company_field.send_keys(CMS_COMPANY_ID)
        username_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        if len(username_fields) >= 2:
            username_fields[1].clear()
            username_fields[1].send_keys(CMS_USERNAME)
        else:
            username_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='사용자'], input[placeholder*='이메일']")
            username_field.clear()
            username_field.send_keys(CMS_USERNAME)
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.clear()
        password_field.send_keys(CMS_PASSWORD)
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]")
        login_button.click()
        print("  ✓ 로그인 버튼 클릭")
        time.sleep(3)
        print("✓ 로그인 완료")
        return True
    except Exception as e:
        print(f"⚠ 자동 로그인 실패: {e}")
        print("수동으로 로그인 후 Enter...")
        input()
        return True


def select_all_rooms(driver, wait):
    """Single, Twin, Double, Triple Room만 선택"""
    print("\n🏨 호텔 객실 선택 중...")
    dropdown_button = wait.until(EC.element_to_be_clickable((By.ID, "hotelRoomSearch__button__button")))
    dropdown_button.click()
    time.sleep(1.5)
    all_options = driver.find_elements(By.XPATH, "//div[@role='option' and contains(@id, 'hotelRoomSearch-option-')]")
    for option in all_options:
        is_selected = option.get_attribute("aria-selected")
        data_selected = option.get_attribute("data-selected")
        if is_selected == "true" or (data_selected and data_selected != ""):
            option.click()
            time.sleep(0.1)
    time.sleep(1)
    target_rooms = ["Single Room", "Twin Room", "Double Room", "Triple Room"]
    for room_name in target_rooms:
        for option in all_options:
            if room_name in option.text:
                is_selected = option.get_attribute("aria-selected")
                data_selected = option.get_attribute("data-selected")
                if is_selected != "true" and (not data_selected or data_selected == ""):
                    option.click()
                    time.sleep(0.1)
    time.sleep(1)
    search_button = wait.until(EC.element_to_be_clickable((By.ID, "searchBtn")))
    search_button.click()
    print("  ✓ 조회 버튼 클릭 - 방 목록 로딩 중...")
    time.sleep(3)
    print("✅ 객실 목록이 표시되었습니다!")


def get_closed_rooms(driver, wait, target_date):
    """마감(판매불가) 객실명 추출"""
    print(f"\n📅 {target_date} 마감객실 정보 수집 중...")
    closed_rooms = set()
    try:
        # 테이블에서 '마감' 또는 '판매불가' 텍스트가 있는 행의 방 타입 추출
        rows = driver.find_elements(By.XPATH, "//tr")
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if not cells or len(cells) < 2:
                    continue
                room_name = cells[0].text.strip()
                status_text = row.text
                if "마감" in status_text or "판매불가" in status_text:
                    # 한글명 → Excel 기준명 매핑
                    mapped = KOREAN_TO_ROOM_TYPE.get(room_name, room_name)
                    closed_rooms.add(mapped)
            except Exception:
                continue
        print(f"  → 마감/판매불가 객실: {list(closed_rooms)}")
    except Exception as e:
        print(f"  ⚠ 마감객실 추출 실패: {e}")
    return list(closed_rooms)



def main():
    # Windows에서 UTF-8 출력 지원
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print("\n4번 마감객실 정보가져오기 (기간 반복)")
    print("="*60)
    start_date_str = input("시작일 (YYYY-MM-DD, 엔터시 오늘): ").strip()
    end_date_str = input("종료일 (YYYY-MM-DD, 엔터시 시작일+14일): ").strip()
    driver, wait = setup_driver()

    # 자동 로그인 (환경변수/설정값이 모두 있을 때만)
    driver.get(CMS_URL)
    time.sleep(2)
    try:
        # 이미 로그인된 경우
        if "#/app" in driver.current_url:
            print("✓ 이미 로그인되어 있습니다.")
        else:
            # 로그인 폼이 보이면 자동 로그인 시도
            try:
                driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                if CMS_COMPANY_ID and CMS_USERNAME and CMS_PASSWORD:
                    print("  → 로그인 폼 발견, 자동 로그인 진행...")
                    company_field = WebDriverWait(driver, IMPLICIT_WAIT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='컴퍼니'], input[placeholder*='ID']"))
                    )
                    company_field.clear()
                    company_field.send_keys(CMS_COMPANY_ID)
                    username_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    if len(username_fields) >= 2:
                        username_fields[1].clear()
                        username_fields[1].send_keys(CMS_USERNAME)
                    else:
                        username_field = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='사용자'], input[placeholder*='이메일']")
                        username_field.clear()
                        username_field.send_keys(CMS_USERNAME)
                    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                    password_field.clear()
                    password_field.send_keys(CMS_PASSWORD)
                    try:
                        keep_login_checkbox = driver.find_element(By.ID, "loginKeepCheckbox")
                        if not keep_login_checkbox.is_selected():
                            driver.execute_script("arguments[0].click();", keep_login_checkbox)
                            print("  ✓ 로그인 유지 체크")
                        else:
                            print("  ✓ 로그인 유지 이미 체크됨")
                    except Exception as e:
                        print(f"  ⚠ 로그인 유지 체크 실패: {e}")
                    time.sleep(0.5)
                    login_button = driver.find_element(By.XPATH, "//button[contains(text(), '로그인')]")
                    login_button.click()
                    print("  ✓ 로그인 버튼 클릭")
                    time.sleep(3)
                    print("✓ 로그인 완료")
                else:
                    print("⚠ 로그인 정보가 없습니다. 수동으로 로그인 후 Enter...")
                    input()
            except Exception:
                print("✓ 로그인 폼이 없습니다 (이미 로그인된 상태)")
    except Exception as e:
        print(f"⚠ 로그인 체크 중 오류: {e}")
    if not start_date_str:
        start_date = datetime.now()
        start_date_str = start_date.strftime("%Y-%m-%d")
    else:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    if not end_date_str:
        end_date = start_date + timedelta(days=14)
        end_date_str = end_date.strftime("%Y-%m-%d")
    else:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    print(f"\n[설정] 시작일: {start_date_str}  종료일: {end_date_str}")

    # ...기존 코드...
    # 인벤토리관리 > 객실별 페이지로 이동 (hotel_cms_controller.py와 동일)
    inventory_url = "https://wingscms.com/#/app/cm/cm03_0300"
    driver.get(inventory_url)
    print(f"  ✓ 인벤토리 관리_객실별 페이지 이동: {inventory_url}")
    time.sleep(3)

    # 날짜 설정 (최초 1회)
    try:
        print(f"\n📅 날짜 설정 중: {start_date_str}")
        date_input = wait.until(EC.presence_of_element_located((By.ID, "startDatePicker")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_input)
        time.sleep(0.3)
        try:
            date_input.click()
        except:
            driver.execute_script("arguments[0].click();", date_input)
        print("  ✓ 달력 열기")
        time.sleep(1)
        # 날짜 직접 입력 (간단화)
        date_input.clear()
        date_input.send_keys(start_date_str)
        date_input.send_keys(Keys.ENTER)
        print(f"  ✓ {start_date_str} 날짜 선택 완료")
        time.sleep(1)
    except Exception as e:
        print(f"⚠ 날짜 설정 실패: {e}")

    # 객실 전체 선택 및 필터 설정 (hotel_cms_controller.py와 동일)
    try:
        print("\n🏨 호텔 객실 전체 선택 중...")
        dropdown_button = wait.until(EC.element_to_be_clickable((By.ID, "hotelRoomSearch__button__button")))
        dropdown_button.click()
        print("  ✓ 객실 선택 드롭다운 열기")
        time.sleep(1.5)
        all_options = driver.find_elements(By.XPATH, "//div[@role='option' and contains(@id, 'hotelRoomSearch-option-')]")
        print(f"  → 전체 옵션 {len(all_options)}개 찾음")
        for option in all_options:
            is_selected = option.get_attribute("aria-selected")
            data_selected = option.get_attribute("data-selected")
            if is_selected != "true" and (not data_selected or data_selected == ""):
                option_text = option.text
                driver.execute_script("arguments[0].click();", option)
                print(f"  ✓ '{option_text}' 선택")
                time.sleep(0.3)
            else:
                option_text = option.text
                print(f"  → '{option_text}' 이미 선택됨")
        time.sleep(1)
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "searchBtn")))
        search_button.click()
        print("  ✓ 조회 버튼 클릭 - 방 목록 로딩 중...")
        time.sleep(3)
        print("✅ 전체 객실 목록이 표시되었습니다!")
        # 필터 설정 (판매가능객실만)
        print("\n🔍 필터 설정 시도 중...")
        # 1단계: 필터 아이콘 클릭
        try:
            filter_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "filter-ico")))
        except:
            filter_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='filter-ico']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", filter_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", filter_button)
        print("  ✓ 필터 패널 열기")
        time.sleep(3)
        # 2단계: 노출정보 드롭다운 클릭
        exposure_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "COMN_CN__button__button")))
        driver.execute_script("arguments[0].click();", exposure_dropdown)
        print("  ✓ 노출정보 드롭다운 열기")
        time.sleep(2)
        all_options = driver.find_elements(By.XPATH, "//div[@role='option' and contains(@id, 'COMN_CN-option-')]")
        print(f"  → 전체 옵션 {len(all_options)}개 찾음")
        for option in all_options:
            is_selected = option.get_attribute("aria-selected")
            data_selected = option.get_attribute("data-selected")
            if is_selected == "true" or (data_selected and data_selected != ""):
                option_text = option.text
                driver.execute_script("arguments[0].click();", option)
                print(f"  → '{option_text}' 체크 해제")
                time.sleep(0.3)
        time.sleep(1)
        # "판매가능객실"만 체크
        sales_room_option = wait.until(EC.presence_of_element_located((By.ID, "COMN_CN-option-0")))
        is_selected = sales_room_option.get_attribute("aria-selected")
        data_selected = sales_room_option.get_attribute("data-selected")
        if is_selected != "true" and (not data_selected or data_selected == ""):
            driver.execute_script("arguments[0].click();", sales_room_option)
            print("  ✓ 판매가능객실 체크")
            time.sleep(2)
        else:
            print("  ✓ 판매가능객실 이미 체크됨")
            time.sleep(1)
        # 4단계: 검색 버튼 클릭
        search_button = None
        try:
            search_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), '검색')]")))
            print("  → 검색 버튼 찾음 (텍스트)")
        except:
            search_button = wait.until(EC.element_to_be_clickable((By.ID, "searchBtn")))
            print("  → 검색 버튼 찾음 (ID)")
        driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", search_button)
        print("  ✓ 필터 검색 버튼 클릭")
        time.sleep(3)
        print("  ✓ 필터 적용 완료")
    except Exception as e:
        print(f"⚠ 객실 선택/필터 자동화 실패: {e}")
        print("수동으로 객실을 선택하고 필터를 적용한 뒤, Enter를 눌러주세요.")
        input()

    # 날짜 루프 제거, 한 번에 전체 날짜/객실별 데이터 읽기
    print("\n🔎 잔여/예약 객실수 및 마감 여부 확인 중... (검증된 방식)")
    try:
        # 날짜 리스트 생성 (15일치)
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        date_list = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(15)]
        rows = driver.find_elements(By.XPATH, "//tr[@data-field='REMANING']")
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 3:
                continue
            room_type = tds[0].text.strip()
            for i, td in enumerate(tds[2:], start=0):
                if i >= len(date_list):
                    continue
                spans = td.find_elements(By.TAG_NAME, "span")
                if len(spans) >= 2:
                    remaining = spans[0].text.strip()
                    booked = spans[1].text.strip()
                    date_key = date_list[i]
                    # 빈 값은 출력하지 않음
                    if remaining == "" and booked == "":
                        continue
                    if remaining == "0":
                        print(f"[마감] {date_key} {room_type} (잔여 0)")
        print("[테스트] 전체 객실/날짜별 마감 판단 완료!")
    except Exception as e:
        print(f"⚠ 데이터 파싱 중 오류: {e}")
        closed_cells = []
        try:
            # 날짜 리스트 생성 (15일치)
            start_dt = datetime.strptime(target_date, "%Y-%m-%d")
            date_list = [(start_dt + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(15)]

            # RMO 버튼 순회 (검증된 방식)
            rmo_buttons = driver.find_elements(By.XPATH, "//span[contains(.,'RMO')]")
            print(f"  ✓ RMO 버튼 {len(rmo_buttons)}개 발견 (객실별)")
            for idx, rmo_btn in enumerate(rmo_buttons):
                try:
                    # RMO 버튼 클릭 (여러 번 시도, JS 클릭 포함)
                    try:
                        rmo_btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", rmo_btn)
                    time.sleep(0.3)

                    parent_tr = rmo_btn.find_element(By.XPATH, "ancestor::tr")
                    # child tr들: 다음 RMO 전까지 data-field='RM_RA'인 tr
                    child_trs = []
                    try:
                        current_sibling = parent_tr.find_element(By.XPATH, "following-sibling::tr[1]")
                        while current_sibling:
                            if current_sibling.get_attribute("data-field") == "RM_RA":
                                child_trs.append(current_sibling)
                            # 다음 RMO 만나면 중단
                            try:
                                current_sibling.find_element(By.XPATH, ".//span[contains(.,'RMO')]")
                                break
                            except:
                                pass
                            current_sibling = current_sibling.find_element(By.XPATH, "following-sibling::tr[1]")
                    except Exception:
                        pass
                    if not child_trs:
                        continue

                    # 방 타입 추출 (첫 child tr의 텍스트에서, 한글명 매핑 포함)
                    room_type = None
                    for child_tr in child_trs:
                        text = child_tr.text.strip()
                        if text and text != '요금':
                            for kor, std in KOREAN_TO_ROOM_TYPE.items():
                                if kor in text:
                                    room_type = std
                                    break
                            if not room_type:
                                room_type = text.split()[0]
                            break
                    if not room_type:
                        continue

                    # 각 child tr에서 input[type=text]를 찾아 날짜별 잔여/예약 추출 (검증된 방식)
                    for child_tr in child_trs:
                        inputs = child_tr.find_elements(By.CSS_SELECTOR, "input[type='text']")
                        if not inputs:
                            continue
                        for i, inp in enumerate(inputs):
                            if i >= len(date_list):
                                continue
                            date_key = date_list[i]
                            try:
                                val = inp.get_attribute("value") or inp.get_attribute("textContent") or inp.get_attribute("innerText")
                                if val is None or val.strip() == '':
                                    continue
                                # 잔여/예약: "3/2" 형태 또는 "3" 형태
                                if "/" in val:
                                    remaining, booked = val.split("/")
                                    remaining = int(remaining.strip())
                                    booked = int(booked.strip())
                                else:
                                    remaining = int(val.strip())
                                    booked = 0
                                print(f"[잔여/예약] {date_key} {room_type} [{i+1}] 잔여:{remaining}, 예약:{booked}")
                                if remaining == 0:
                                    closed_cells.append({'date': date_key, 'room_type': room_type})
                                    print(f"[마감] {date_key} {room_type} (잔여 0)")
                            except Exception:
                                continue
                except Exception:
                    continue
            if not closed_cells:
                print("  → 마감된 셀 없음")
        except Exception as e:
            print(f"  ⚠ 마감 판단 오류: {e}")
        print(f"[테스트] {target_date} 전체 객실/날짜별 잔여/예약/마감 판단 완료!")
        current_date += timedelta(days=15)
        time.sleep(3)

if __name__ == "__main__":
    main()
