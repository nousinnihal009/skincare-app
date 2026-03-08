@echo off
call "%~dp0venv\Scripts\activate.bat"
echo Python path: %PATH% > "%~dp0run_output.log" 2>&1
python --version >> "%~dp0run_output.log" 2>&1
echo --- >> "%~dp0run_output.log" 2>&1
python "%~dp0test_ml_pipeline_logged.py" >> "%~dp0run_output.log" 2>&1
echo Exit code: %ERRORLEVEL% >> "%~dp0run_output.log" 2>&1
