#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""마감 방 하이라이트 기능 테스트"""

from hotel_cms_controller import test_highlight_closed_rooms

if __name__ == "__main__":
    result = test_highlight_closed_rooms()
    if result:
        print("\n✅ 테스트 성공! 기준가격.xlsx를 열어서 확인해보세요.")
    else:
        print("\n❌ 테스트 실패.")
