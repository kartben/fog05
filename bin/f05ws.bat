@echo off
set PYFILE=%~f0
set PYFILE=%PYFILE:~0,-3%
"python.exe" "%PYFILE%" %*