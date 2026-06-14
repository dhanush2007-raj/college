@echo off
title SLVGP Hassan Website - Deploy to GitHub
echo ================================================================
echo   SLVGP HASSAN DEPLOYMENT ASSISTANT (GITHUB PAGES)
echo ================================================================
echo.
echo This script will initialize Git, commit your files, and push
echo them to a GitHub repository to host the website for free.
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

:: Initialize git if not already initialized
if not exist ".git" (
    echo Initializing Git repository...
    git init
    git branch -M main
) else (
    echo Git repository already initialized.
)

:: Stage files
echo.
echo Staging website files...
git add index.html slvgp-hassan-website.html slvgp-hassan-editor.html server.py

:: Commit changes
echo.
echo Committing changes...
git commit -m "Publish updated website content"

:: Prompt for repository URL
echo.
set /p repo="Enter your GitHub Repository URL (e.g., https://github.com/username/repo.git): "

if "%repo%"=="" (
    echo [ERROR] Repository URL cannot be empty.
    pause
    exit /b
)

:: Configure origin remote
git remote remove origin >nul 2>nul
git remote add origin %repo%

echo.
echo Pushing website to GitHub main branch...
git push -u origin main --force

if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo   SUCCESSFULLY DEPLOYED TO GITHUB!
    echo ================================================================
    echo.
    echo   Now, enable GitHub Pages to view it live:
    echo   1. Open your repository on github.com
    echo   2. Go to: Settings --^> Pages
    echo   3. Under "Build and deployment", set:
    echo      - Source: Deploy from a branch
    echo      - Branch: main ( /root )
    echo   4. Click "Save".
    echo.
    echo   Your website will be live at:
    echo   https://[your-username].github.io/[your-repo-name]/
    echo.
) else (
    echo.
    echo [ERROR] Push failed. 
    echo Please ensure the repository exists on GitHub, is empty,
    echo and that you have login credentials configured.
    echo.
)

pause
