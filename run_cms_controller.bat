@echo off
REM 호텔 CMS 컨트롤러 자동 실행 배치파일

REM 가상환경이 있다면 활성화 (없으면 이 부분 생략 가능)
REM call venv\Scripts\activate

REM Python 실행 (실행 중 오류 발생 시 메시지 출력)
python hotel_cms_controller.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [실패] 프로그램 실행 중 오류가 발생했습니다.
    pause
) else (
    echo.
    echo [완료] 프로그램이 정상적으로 종료되었습니다.
    pause
)
