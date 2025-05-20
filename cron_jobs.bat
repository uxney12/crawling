@echo off

echo ACTIVATE venv...
call E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\venv\Scripts\activate
IF %ERRORLEVEL% NEQ 0 (echo ERROR venv! & pause & exit /b)

echo RUNNING crawling.py...
python E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\crawling.py
IF %ERRORLEVEL% NEQ 0 (echo ERROR crawling.py! & pause & exit /b)

echo RUNNING preprocessing.py...
python E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\preprocessing.py
IF %ERRORLEVEL% NEQ 0 (echo ERROR preprocessing.py! & pause & exit /b)

echo RUNNING upload_csv.py...
python E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\upload_csv.py
IF %ERRORLEVEL% NEQ 0 (echo ERROR upload_csv.py! & pause & exit /b)

cd /d E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\the_SHEA

echo RUNNING import_csv.py...
python manage.py import_csv
IF %ERRORLEVEL% NEQ 0 (echo ERROR import_csv! & pause & exit /b)

echo RUNNING export_google_sheets.py...
python manage.py export_google_sheets
IF %ERRORLEVEL% NEQ 0 (echo ERROR export_google_sheets! & pause & exit /b)

cd /d E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM

echo RUNNING refresh_data_source.py...
python E:\INTERN\PORTFOLIO\AUTOMATION\SYSTEM\refresh_data_source.py
IF %ERRORLEVEL% NEQ 0 (echo ERROR refresh_data_source.py! & pause & exit /b)

echo DEACTIVATE venv...
deactivate
IF %ERRORLEVEL% NEQ 0 echo ERROR venv!

echo DONE!!!!!!!!!!!!
pause




