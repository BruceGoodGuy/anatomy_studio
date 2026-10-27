@echo off
setlocal
REM ===================================================================
REM  Anatomy Studio (Windows)
REM  OpenSim 4.6 chi co ban cai cho Python 3.11, 3.12, 3.13 (64-bit).
REM  File nay tu tim dung Python, tu tao lai moi truong neu bi hong.
REM ===================================================================
cd /d "%~dp0"
set "VPY=.venv\Scripts\python.exe"
set "CHECK=import sys, opensim, numpy, scipy, trimesh, fastapi, uvicorn"

REM --- 1. Moi truong da co va dung duoc -> chay luon -------------------
if exist "%VPY%" (
  "%VPY%" -c "%CHECK%" >nul 2>&1 && goto run
  echo Moi truong .venv bi thieu thu vien - se tao lai.
  rmdir /s /q .venv
)

REM --- 2. Tim Python 3.11 - 3.13 --------------------------------------
set "PY="
for %%V in (3.12 3.13 3.11) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if (3,11) <= sys.version_info[:2] <= (3,13) and sys.maxsize > 2**32 else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY goto nopython

echo Dung Python:
%PY% --version

REM --- 3. Tao moi truong va cai thu vien ------------------------------
echo Dang tao moi truong va cai thu vien, lan dau mat vai phut...
%PY% -m venv .venv || goto installfail
"%VPY%" -m pip install --upgrade pip || goto installfail
"%VPY%" -m pip install -r requirements.txt || goto installfail
"%VPY%" -c "%CHECK%" || goto installfail
echo Cai dat xong.

:run
"%VPY%" studio.py
pause
exit /b 0

:nopython
echo.
echo  KHONG TIM THAY PYTHON 3.11 - 3.13 (64-bit).
echo  OpenSim 4.6 chua co ban cho Python 3.14 tro len hoac 3.10 tro xuong.
echo.
echo  Cach sua: cai them Python 3.12 (khong can go ban dang co):
echo    - Mo https://www.python.org/downloads/windows/
echo      chon "Python 3.12.x" - "Windows installer (64-bit)"
echo    - hoac chay lenh:  winget install Python.Python.3.12
echo  Sau do bam dup lai run_studio.bat.
echo.
pause
exit /b 1

:installfail
echo.
echo  CAI THU VIEN THAT BAI - xem dong bao loi ngay phia tren.
echo  Da xoa .venv de lan sau cai lai tu dau.
echo  Neu loi lien quan mang/proxy: thu lai khi co mang on dinh.
echo.
if exist .venv rmdir /s /q .venv
pause
exit /b 1
