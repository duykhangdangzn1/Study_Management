@echo off
setlocal
REM ============================================================
REM  Dong goi MOT file .exe duy nhat (Windows, Python 3.10+)
REM  Chay: build_windows.bat
REM ============================================================
cd /d "%~dp0"
echo [1/5] Cai dat thu vien...
python -m pip install --disable-pip-version-check -r requirements.txt pyinstaller || goto :err
echo.
echo [2/5] Kiem thu logic diem (tests_core.py)...
python tests_core.py || goto :err
echo.
echo [3/5] Kiem thu AI / phan tich / tu van (tests_ai.py)...
python tests_ai.py || goto :err
echo.
echo [4/5] Kiem thu tu dong hoa (tests_automation.py)...
python tests_automation.py || goto :err
echo.
echo [5/5] Dong goi file exe...
python -m PyInstaller --noconfirm --clean TinHocXayDung.spec || goto :err
echo.
echo ============================================================
echo  XONG! File exe: dist\QuanLyHocPhan_TinHocXayDung_AI.exe
echo ============================================================
pause
exit /b 0

:err
echo.
echo [LOI] Buoc vua roi that bai. Xem thong bao phia tren.
pause
exit /b 1
