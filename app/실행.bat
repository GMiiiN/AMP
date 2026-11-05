@echo off
chcp 65001 >nul
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (
 echo Node.js 22.13 이상을 설치한 후 다시 실행해 주세요.
 pause
 exit /b 1
)
if not exist node_modules (
 call npm ci
 if errorlevel 1 (
  echo 패키지 설치 실패. 위 오류를 확인해 주세요.
  pause
  exit /b 1
 )
)
call npm start
pause
