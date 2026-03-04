@echo off
cd /d "%~dp0"
git add -A
git commit -m "Auto-save %date% %time%"
git push
echo.
echo Сохранено в GitHub!
pause
