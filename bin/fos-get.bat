@echo off
set PYFILE=%~f0
set PYFILE=%PYFILE:~0,-6%
"python.exe" "%PYFILE%" %*