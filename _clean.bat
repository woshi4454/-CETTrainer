@echo off
chcp 65001 >nul
title CETTrainer 垃圾清理
setlocal
cd /d "%~dp0"

echo ============================================================
echo  CETTrainer 垃圾清理
echo ============================================================
echo.
echo  [1] 直接清理
echo  [2] 先预览（不真删）
echo  [3] 连源码 build/ __pycache__ 一起清
echo.
set /p CH="请输入 1 / 2 / 3 后回车（直接回车 = 1）: "
if "%CH%"=="" set CH=1

if "%CH%"=="2" (
    "E:\Python315\python.exe" _clean.py --dry
) else if "%CH%"=="3" (
    "E:\Python315\python.exe" _clean.py --all
) else (
    "E:\Python315\python.exe" _clean.py
)

echo.
pause
endlocal
