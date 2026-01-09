@echo off
REM 호텔 CMS 컨트롤러 자동 설치 및 실행 스크립트


REM 1. Python 설치 여부 확인 및 자동 설치 (WindowsApps 가짜 python.exe 무시)
setlocal enabledelayedexpansion
set PYTHON_OK=0
for /f "delims=" %%P in ('where python 2^>nul') do (
    echo %%P | findstr /I "WindowsApps" >nul
    if !ERRORLEVEL! == 0 (
        REM WindowsApps의 python.exe는 무시
        set PYTHON_OK=0
    ) else (
        set PYTHON_OK=1
    )
)
if !PYTHON_OK! == 0 (
    echo [안내] Python이 설치되어 있지 않거나, WindowsApps의 가짜 python.exe만 있습니다. 자동으로 설치를 진행합니다.
    set PYTHON_INSTALLER=python-installer.exe
    set PYTHON_URL=https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe
    powershell -Command "Invoke-WebRequest -Uri %PYTHON_URL% -OutFile %PYTHON_INSTALLER%"
    if exist %PYTHON_INSTALLER% (
        echo [진행중] Python 설치 프로그램 실행...
        %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        if %ERRORLEVEL% neq 0 (
            echo [오류] Python 자동 설치에 실패했습니다. 수동 설치를 진행해 주세요.
            pause
            exit /b 1
        )
        del %PYTHON_INSTALLER%
        echo [안내] Python 설치가 완료되었습니다. 새 창을 열어 다시 실행해 주세요.
        pause
        exit /b 0
    ) else (
        echo [오류] Python 설치 파일 다운로드에 실패했습니다. 인터넷 연결을 확인하거나 수동 설치해 주세요.
        pause
        exit /b 1
    )
)
endlocal

REM 2. pip 최신화
python -m pip install --upgrade pip

REM 3. 필수 패키지 설치
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [오류] 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)

REM 4. .env 파일 자동 생성 안내
if not exist .env (
    echo [안내] 환경설정 파일(.env)이 없습니다. 기본 예시 파일을 복사합니다.
    copy .env.example .env >nul
    echo [중요] .env 파일을 열어 CMS 계정 정보를 입력해 주세요.
    notepad .env
    pause
)


REM 5. 기능 선택 메뉴
echo.
echo 실행할 기능을 선택하세요:
echo 1. 객실수 자동조정 (기간별)
echo 2. 요금 자동입력 (RMO 기반)
set /p menu_option=번호 입력 (1 또는 2): 
echo.
if "%menu_option%"=="1" (
    python hotel_cms_controller.py
) else if "%menu_option%"=="2" (
    python hotel_cms_controller.py
) else (
    echo 잘못된 옵션입니다. 프로그램을 종료합니다.
    pause
    exit /b 1
)
