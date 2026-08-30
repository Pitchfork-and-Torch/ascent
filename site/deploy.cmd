@echo off
setlocal
cd /d "%~dp0"

echo Generating OG card + architecture infographic + Starlink map + series...
py -3 scripts\make_og.py
if errorlevel 1 exit /b 1
py -3 scripts\make_infographic.py
if errorlevel 1 exit /b 1
py -3 scripts\make_infographic_starlink.py
if errorlevel 1 exit /b 1
py -3 scripts\make_infographic_series.py
if errorlevel 1 exit /b 1

echo Deploying ASCENT site (Pages)...
call npx.cmd --yes wrangler pages deploy public --project-name=ascent-jonbailey --commit-dirty=true
if errorlevel 1 exit /b 1

echo.
echo Deploy complete.
echo Site:    https://ascent.jonbailey.xyz/
echo Preview: https://ascent-jonbailey.pages.dev/
echo NOTE: After major feature ships, bump VERSION in make_infographic*.py and ?v= cache-bust before deploy.
endlocal
