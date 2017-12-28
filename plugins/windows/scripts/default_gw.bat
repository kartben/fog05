set "ip="
for /f "tokens=1-2 delims=:" %%a in ('ipconfig^|find "Default"') do if not defined ip set ip=%%boute