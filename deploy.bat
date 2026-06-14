@echo off
title SLVGP Hassan Website - Secure First Deploy to GitHub
echo ================================================================
echo   SLVGP HASSAN SECURE DEPLOYMENT ASSISTANT (GITHUB PAGES)
echo ================================================================
echo.
echo This script performs the FIRST-TIME setup and initial push of
echo your website to GitHub. Run this only once. Use update.bat
echo for all future updates.
echo.

:: ----------------------------------------------------------------
:: SECURITY: Locate Git from a hardcoded known path only.
:: Prevents PATH environment variable manipulation / hijacking.
:: ----------------------------------------------------------------
set GIT_EXE="C:\Program Files\Git\cmd\git.exe"
if not exist %GIT_EXE% set GIT_EXE="C:\Program Files\Git\bin\git.exe"
if not exist %GIT_EXE% set GIT_EXE="C:\Program Files (x86)\Git\bin\git.exe"

if not exist %GIT_EXE% (
    echo [ERROR] Git not found at any known installation path.
    echo Install Git from https://git-scm.com/ and try again.
    echo.
    pause
    exit /b 1
)
echo [OK] Git found at: %GIT_EXE%
echo.

:: ----------------------------------------------------------------
:: Initialize Git if not already done.
:: ----------------------------------------------------------------
if not exist ".git" (
    echo Initializing Git repository...
    %GIT_EXE% init
    %GIT_EXE% branch -M main
    echo [OK] Repository initialized.
) else (
    echo [OK] Git repository already initialized.
)
echo.

:: ----------------------------------------------------------------
:: Stage only the known, specific website files.
:: No wildcards — each file is individually approved.
:: ----------------------------------------------------------------
echo Staging verified files only...
%GIT_EXE% add index.html
%GIT_EXE% add slvgp-hassan-website.html
%GIT_EXE% add logo-removebg-preview.png
%GIT_EXE% add server.py
%GIT_EXE% add update.bat
%GIT_EXE% add deploy.bat

if %errorlevel% neq 0 (
    echo [ERROR] Failed to stage files. Check file permissions.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: Commit with a clear, timestamped label.
:: ----------------------------------------------------------------
set TIMESTAMP=%date% %time%
echo.
echo Committing initial deploy at: %TIMESTAMP%
%GIT_EXE% commit -m "Initial deploy: %TIMESTAMP%"
echo.

:: ----------------------------------------------------------------
:: SECURITY: Validate the repository URL before use.
:: Must start with https://github.com/ to prevent
:: the code from being pushed to an unknown server.
:: ----------------------------------------------------------------
:ask_repo
set /p repo="Enter your GitHub Repository URL (https://github.com/username/repo.git): "

if "%repo%"=="" (
    echo [ERROR] URL cannot be empty. Please try again.
    goto ask_repo
)

:: Check that the URL starts with https://github.com/
echo %repo% | findstr /i "^https://github.com/" >nul
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Invalid URL. URL must start with https://github.com/
    echo This check prevents your code from being sent to unknown servers.
    echo.
    goto ask_repo
)

echo.
echo [OK] Repository URL validated: %repo%
echo.

:: ----------------------------------------------------------------
:: Set the remote origin safely.
:: ----------------------------------------------------------------
%GIT_EXE% remote remove origin >nul 2>nul
%GIT_EXE% remote add origin %repo%

echo.
echo Pushing to GitHub (initial deploy, no --force)...
%GIT_EXE% push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   SUCCESSFULLY DEPLOYED TO GITHUB!
    echo ================================================================
    echo.
    echo   Next steps to go LIVE on GitHub Pages:
    echo   1. Open your repo at: %repo%
    echo   2. Go to: Settings ^> Pages
    echo   3. Under "Build and deployment", set:
    echo      - Source: Deploy from a branch
    echo      - Branch: main ( /root )
    echo   4. Click "Save".
    echo.
    echo   Your site will be live at:
    echo   https://[your-username].github.io/[your-repo-name]/
    echo.
    echo   For future updates, run: update.bat
    echo.
) else (
    echo.
    echo [ERROR] Push failed.
    echo   - Make sure the GitHub repository exists and is EMPTY.
    echo   - Make sure you are logged in: run 'git config --global credential.helper manager'
    echo   - Check your internet connection.
    echo.
)

pause
