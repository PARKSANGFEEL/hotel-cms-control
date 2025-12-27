"""
호텔 CMS 컨트롤러 사용 예시
"""
from hotel_cms_controller import HotelCMSController
import time

# 예시 1: 간단한 사용
def example_1():
    """기본 사용 예시"""
    controller = HotelCMSController()
    
    try:
        # 브라우저 실행 및 CMS 접속
        controller.setup_driver()
        controller.navigate_to_cms()
        
        print("\n로그인을 완료한 후 Enter를 눌러주세요...")
        input()
        
        # 현재 상태 조회
        current = controller.get_current_availability()
        
        # 수량 변경
        controller.set_room_availability('SINGLE', 10)
        controller.set_room_availability('TWIN', 5)
        
        print("\n완료! 10초 후 종료됩니다...")
        time.sleep(10)
        
    finally:
        controller.close()


# 예시 2: 모든 방 한번에 설정
def example_2():
    """일괄 설정 예시"""
    controller = HotelCMSController()
    
    try:
        controller.setup_driver()
        controller.navigate_to_cms()
        
        print("\n로그인을 완료한 후 Enter를 눌러주세요...")
        input()
        
        # 모든 방 타입 한번에 설정
        settings = {
            'SINGLE': 8,
            'TWIN': 6,
            'DOUBLE': 4,
            'TRIPLE': 2
        }
        
        controller.set_all_rooms(settings)
        
        print("\n완료! 확인 후 Enter를 눌러 종료하세요...")
        input()
        
    finally:
        controller.close()


# 예시 3: 조건부 수량 조절
def example_3():
    """현재 상태를 확인하고 조건에 따라 조절"""
    controller = HotelCMSController()
    
    try:
        controller.setup_driver()
        controller.navigate_to_cms()
        
        print("\n로그인을 완료한 후 Enter를 눌러주세요...")
        input()
        
        # 현재 상태 확인
        current = controller.get_current_availability()
        
        # 조건: Single Room이 3개 미만이면 10개로 설정
        single_count = current.get('SINGLE')
        if single_count and int(single_count) < 3:
            print(f"\nSingle Room이 {single_count}개로 부족합니다. 10개로 설정합니다.")
            controller.set_room_availability('SINGLE', 10)
        else:
            print(f"\nSingle Room은 충분합니다 ({single_count}개)")
        
        print("\n완료! 확인 후 Enter를 눌러 종료하세요...")
        input()
        
    finally:
        controller.close()


if __name__ == "__main__":
    print("실행할 예시를 선택하세요:")
    print("1. 기본 사용")
    print("2. 일괄 설정")
    print("3. 조건부 조절")
    
    choice = input("\n선택 (1-3): ")
    
    if choice == "1":
        example_1()
    elif choice == "2":
        example_2()
    elif choice == "3":
        example_3()
    else:
        print("올바른 선택이 아닙니다.")
