@echo off
setlocal
set "H3_STUDIO_ROOT=%~dp0"
set "H3_STUDIO_PYTHON="
if exist "%H3_STUDIO_ROOT%..\python_embeded\python.exe" (
    set "H3_STUDIO_PYTHON=%H3_STUDIO_ROOT%..\python_embeded\python.exe"
    goto :launch
)
if exist "%H3_STUDIO_ROOT%.venv\Scripts\python.exe" (
    set "H3_STUDIO_PYTHON=%H3_STUDIO_ROOT%.venv\Scripts\python.exe"
    goto :launch
)
if exist "%H3_STUDIO_ROOT%venv\Scripts\python.exe" (
    set "H3_STUDIO_PYTHON=%H3_STUDIO_ROOT%venv\Scripts\python.exe"
    goto :launch
)
echo MiniMax H3 Studio could not find ComfyUI's Python environment.
echo Place this launcher inside ComfyUI beside main.py.
echo Supported locations: ..\python_embeded, .venv, or venv.
echo To use another environment, activate it and run python h3_studio_start.py.
pause
exit /b 2

:launch
"%H3_STUDIO_PYTHON%" -s "%H3_STUDIO_ROOT%h3_studio_start.py" %*
set "H3_STUDIO_RESULT=%ERRORLEVEL%"
if not "%H3_STUDIO_RESULT%"=="0" pause
exit /b %H3_STUDIO_RESULT%
