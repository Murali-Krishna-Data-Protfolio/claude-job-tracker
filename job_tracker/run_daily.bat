@echo off
REM Daily Job Tracker — Entry point for Windows Task Scheduler
REM Task Scheduler calls this file every day at 08:30
REM All source code lives centrally in src\ — see src\job_tracker.py

cd /d "%~dp0src"

REM Use system Python (or activate venv if you have one)
REM Uncomment the line below if you use a virtual environment:
REM call "%~dp0venv\Scripts\activate.bat"

python job_tracker.py >> "%~dp0outputs\run_log.txt" 2>&1

echo [%DATE% %TIME%] Run completed >> "%~dp0outputs\run_log.txt"
