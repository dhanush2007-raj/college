@echo off
title SLVGP Hassan Website - Sync Updates to GitHub
echo ================================================================
echo   SLVGP HASSAN SYNC UPDATE ASSISTANT
echo ================================================================
echo.
echo This script will save and push all your latest edits to GitHub.
echo.

:: Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not in your PATH.
    echo Please install Git from https://git-scm.com/ and try again.
    echo.
    pause
    exit /b
)

:: Check if git is initialized
if not exist ".git" (
    echo [ERROR] Git has not been initialized in this folder.
    echo Please run deploy.bat first to configure your repository.
    echo.
    pause
    exit /b
)

:: Stage files
echo Staging updated files...
git add index.html slvgp-hassan-website.html slvgp-hassan-editor.html server.py logo-removebg-preview.png update.bat deploy.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to stage files.
    pause
    exit /b
)

:: Commit
echo.
echo Committing changes...
git commit -m "Update website content via sync script"

:: Push to GitHub
echo.
echo Pushing updates to GitHub Pages...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   SUCCESSFULLY UPDATED LIVE WEBSITE!
    echo ================================================================
    echo.
    echo   Your changes are pushed to GitHub.
    echo   The live site will update in a minute at your GitHub Pages URL!
    echo.
) else (
    echo.
    echo [ERROR] Sync failed.
    echo Please make sure your network is connected and git is configured.
    echo.
)

pause
