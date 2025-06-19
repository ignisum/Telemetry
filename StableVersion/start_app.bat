@echo off
setlocal enabledelayedexpansion

taskkill /f /im "ServerApp.exe" >nul 2>&1
taskkill /f /im "ClientApp.exe" >nul 2>&1

set "BAT_DIR=%~dp0"
set "APP_DIR=%BAT_DIR%App\"

cd /d "%APP_DIR%"

echo Текущая директория: %cd%

set "SERVER_PATH=ServerApp.exe"
set "CLIENT_PATH=ClientApp.exe"
set "ENV_FILE=.env"

if not exist "%SERVER_PATH%" (
    echo Ошибка: Файл сервера не найден: %APP_DIR%%SERVER_PATH%
    dir "%APP_DIR%"
    pause
    exit /b 1
)

if not exist "%CLIENT_PATH%" (
    echo Ошибка: Файл клиента не найден: %APP_DIR%%CLIENT_PATH%
    dir "%APP_DIR%"
    pause
    exit /b 1
)

if not exist "%ENV_FILE%" (
    echo Ошибка: .env файл не найден: %APP_DIR%%ENV_FILE%
    dir "%APP_DIR%"
    pause
    exit /b 1
)

echo Запуск сервера...
start "" /B "%APP_DIR%ServerApp.exe"

echo Ожидаем запуск сервера ...
timeout /t 2 /nobreak >nul

echo Запуск клиента...
start "" "%APP_DIR%ClientApp.exe"

echo Ожидание завершения клиента...
:wait_loop
tasklist | find /i "ClientApp.exe" >nul
if %errorlevel% == 0 (
    timeout /t 1 >nul
    goto wait_loop
)

echo Остановка сервера...
taskkill /f /im "ServerApp.exe" >nul 2>&1

echo Все процессы завершены
pause