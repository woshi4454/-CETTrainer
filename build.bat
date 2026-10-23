@echo off
REM ============================================================
REM  CET 四六级学习助手 —— 打包脚本 (PyInstaller 单文件)
REM
REM  前置：本机装有 E:\Python315 (Python 3.15) 并已 pip install pyinstaller
REM  用法：双击本文件，或在工程目录执行 build.bat
REM ============================================================
setlocal
set PY=E:\Python315\python.exe
set SPEC=build\CETTrainer.spec

if not exist "%PY%" (
    echo [错误] 找不到 Python: %PY%
    echo 请安装 Python 3.15 到 E:\Python315，或自行修改本脚本的 PY 变量。
    pause
    exit /b 1
)

echo [1/3] 生成数据包 cet_pack.json ...
"%PY%" build_pack.py
if errorlevel 1 (
    echo [错误] 数据包生成失败
    pause
    exit /b 1
)

echo [2/3] 调用 PyInstaller 打包 ...
"%PY%" -m PyInstaller --noconfirm --clean ^
    --name CETTrainer ^
    --onefile ^
    --windowed ^
    --icon "cet.ico" ^
    --add-data "cet_pack.json;." ^
    --add-data "cet.ico;." ^
    --add-data "icon_app.png;." ^
    --add-data "icon_app64.png;." ^
    --hidden-import pages ^
    --hidden-import pages.page_vocab ^
    --hidden-import pages.page_wordbook ^
    --hidden-import pages.page_wrong ^
    --hidden-import pages.page_dictation ^
    --hidden-import pages.page_listening ^
    --hidden-import pages.page_reading ^
    --hidden-import pages.page_cloze ^
    --hidden-import pages.page_translate ^
    --hidden-import pages.page_writing ^
    --hidden-import pages.page_phrase ^
    --hidden-import pages.page_grammar ^
    --hidden-import pages.page_mock ^
    --hidden-import pages.page_import ^
    --hidden-import pages.page_stats ^
    --hidden-import data_vocab ^
    --hidden-import data_phrases ^
    --hidden-import data_sentences ^
    --hidden-import data_grammar ^
    --hidden-import data_writing ^
    --hidden-import data_listening ^
    --hidden-import data_extra ^
    --hidden-import data_gaokao ^
    --hidden-import data_cet4_big ^
    --hidden-import data_cet6_big ^
    --hidden-import tts_edge ^
    app.py

if errorlevel 1 (
    echo [错误] PyInstaller 打包失败
    pause
    exit /b 1
)

echo [3/3] 完成。产物位于 dist\CETTrainer.exe
pause
endlocal
