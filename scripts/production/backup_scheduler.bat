@echo off
REM StockHistory Backup Scheduler
REM This batch file is used for automatic data backup execution

echo ========================================
echo StockHistory Automatic Backup Started
echo Time: %DATE% %TIME%
echo ========================================

REM Set environment variables
set PYTHONPATH=%~dp0src
set BACKUP_SCRIPT=%~dp0src\Common\BackupService.py

REM Check Python environment.
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python environment not found
    echo Please ensure Python is installed and available in PATH
    echo Try running: python --version manually to verify installation
    exit /b 1
)

REM Check if backup script exists
echo Checking backup script: %BACKUP_SCRIPT%
if not exist "%BACKUP_SCRIPT%" (
    echo Error: Backup script not found
    echo Script path: %BACKUP_SCRIPT%
    echo Current directory: %CD%
    dir "%~dp0src\Common\" 2>nul
    exit /b 1
)

REM Execute full backup
echo Starting database backup...
echo Command: python "%BACKUP_SCRIPT%" --type full
python "%BACKUP_SCRIPT%" --type full
set BACKUP_ERRORLEVEL=%ERRORLEVEL%
if %BACKUP_ERRORLEVEL% neq 0 (
    echo Error: Backup execution failed with error code %BACKUP_ERRORLEVEL%
    echo Backup script: %BACKUP_SCRIPT%
    echo Please check the backup service logs for more details
    exit /b %BACKUP_ERRORLEVEL%
)

REM Execute archival (optional)
echo Starting data archival...
set ARCHIVAL_SCRIPT=%~dp0src\Common\ArchivalService.py
echo Command: python "%ARCHIVAL_SCRIPT%" --compress-logs
python "%ARCHIVAL_SCRIPT%" --compress-logs
set ARCHIVAL_ERRORLEVEL=%ERRORLEVEL%
if %ARCHIVAL_ERRORLEVEL% neq 0 (
    echo Warning: Data archival failed with error code %ARCHIVAL_ERRORLEVEL%
    echo This is not critical, backup was successful
    echo Archival script: %ARCHIVAL_SCRIPT%
)

echo ========================================
echo Backup completed
echo Time: %DATE% %TIME%
echo ========================================

REM Send notification (optional)
REM Email notification or message push can be added here

exit /b 0
