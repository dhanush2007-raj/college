@echo off
title SLVGP Hassan Website - Secure Sync Update
echo ================================================================
echo   SLVGP HASSAN SECURE SYNC UPDATE ASSISTANT
echo ================================================================
echo.
echo This script safely stages, verifies, and pushes only the
echo known website files to GitHub. No wildcards. No force push.
echo.

:: ----------------------------------------------------------------
:: SECURITY: Verify Git is installed from a known location.
:: We do NOT use "where git" because PATH can be manipulated.
:: ----------------------------------------------------------------
set GIT_EXE="C:\Program Files\Git\cmd\git.exe"
if not exist %GIT_EXE% set GIT_EXE="C:\Program Files\Git\bin\git.exe"
if not exist %GIT_EXE% set GIT_EXE="C:\Program Files (x86)\Git\bin\git.exe"

if not exist %GIT_EXE% (
    echo [ERROR] Git not found at known locations.
    echo Install Git from https://git-scm.com/ and try again.
    echo.
    pause
    exit /b 1
)

echo [OK] Git found at: %GIT_EXE%
echo.

:: ----------------------------------------------------------------
:: SECURITY: Check Git is initialized.
:: ----------------------------------------------------------------
if not exist ".git" (
    echo [ERROR] Git has not been initialized in this folder.
    echo Please run deploy.bat first to configure your repository.
    echo.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: SECURITY: Only stage specific known files — NO wildcards.
:: This prevents any injected or unknown files from being pushed.
:: ----------------------------------------------------------------
echo Staging only verified website files...
%GIT_EXE% add index.html
%GIT_EXE% add slvgp-hassan-website.html
%GIT_EXE% add slvgp-hassan-editor.html
%GIT_EXE% add server.py
%GIT_EXE% add logo-removebg-preview.png
%GIT_EXE% add update.bat
%GIT_EXE% add deploy.bat

if %errorlevel% neq 0 (
    echo [ERROR] Staging failed. Check your file permissions.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: SECURITY: Commit with unique timestamp so every push is
:: individually traceable in the audit history. No generic labels.
:: ----------------------------------------------------------------
set TIMESTAMP=%date% %time%
echo.
echo Committing with timestamp: %TIMESTAMP%
%GIT_EXE% commit -m "Secure sync update: %TIMESTAMP%"

:: ----------------------------------------------------------------
:: SECURITY: Push WITHOUT --force. This prevents accidental or
:: malicious history rewrites. If there is a conflict, the push
:: will fail and alert you rather than silently destroying history.
:: ----------------------------------------------------------------
echo.
echo Pushing to GitHub (no force — history is protected)...
%GIT_EXE% push origin main

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   SUCCESSFULLY UPDATED LIVE WEBSITE!
    echo ================================================================
    echo.
    echo   Your changes are live on GitHub Pages.
    echo   The website will update within 1-2 minutes.
    echo.
) else (
    echo.
    echo [ERROR] Push failed.
    echo   - Check your internet connection.
    echo   - Ensure your GitHub credentials are configured.
    echo   - If remote has newer commits, run: git pull origin main
    echo     then try this script again.
    echo.
)

pause
