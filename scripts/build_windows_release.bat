@echo off
set packages=pygame cx_Freeze prompt_toolkit tones
set pythondir=C:\Python27
set python-pip=%pythondir%\Scripts\pip.exe
set python-interpreter=%pythondir%\python.exe
set build-dir=%~dp0build
set setup-script=%~dp0cxfreeze-setup.py
set setup-script-args=build_exe
set python-download-url=https://www.python.org/downloads/release/python-2715/

call :check-python-bin %python-interpreter%
call :check-python-bin %python-pip%

echo(
echo Installing python packages...
echo(

%python-pip% install %packages%

if exist %build-dir%\ (
	echo(
	echo Deleting %build-dir%...
	del /Q %build-dir%\
)

echo(
echo Building windows executable...
echo(

%python-interpreter% %setup-script% %setup-script-args%

echo(
echo Build completed, output should be in %build-dir%
echo(

goto finish-pause

:check-python-bin
	if not exist %~1 (
		echo(
		echo Can't find %~1
		echo Please install Python2.7.x
		echo(
		echo %python-download-url%
		echo(
		goto finish-pause
	)
exit /b

:finish-pause
pause>nul|set/p =Press any key to exit ...
exit
