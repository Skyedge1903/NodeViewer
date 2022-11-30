# NodeViewer

## Get the latest version

[Download the latest version](https://github.com/Skyedge1903/NodeViewer/archive/refs/heads/main.zip)
and then Unzip the file in the destination of your choice.

## Compile you own version

Run the following command in the root directory of the project:
```console
python -m py_compile ticker.py
```

## Linux Installation

First install python 3.10.0 or higher :
```console
sudo apt-get install python3.10
```

Installation of libraries (with Linux Shell) :

```console
pip install pyserial
pip install requests
```

Then you can run the following command (replace with your directories) to run the program :
```console
python3 ~/NodeViewer/__pycache__/ticker.cpython-310.pyc
```

[Launch the script at startup](https://help.ubuntu.com/stable/ubuntu-help/startup-applications.html.en)
for ubuntu.

## Windows Installation

First install [python 3.10.0](https://apps.microsoft.com/store/detail/python-310/9PJPW5LDXLZ5?hl=en-us&gl=us)
or higher on the Windows Store !

Installation of libraries (with Powershell) :

```console
pip install pyserial
pip install requests
```

Then [follow this tutorial to access the start-up folder](https://support.microsoft.com/en-us/windows/add-an-app-to-run-automatically-at-startup-in-windows-10-150da165-dcd9-7230-517b-cf3c295d89dd)
for Windows. Then create a file name `launch.bat` (replace with your directories in code) in start-up folder with contain :

```batch
if not DEFINED IS_MINIMIZED set IS_MINIMIZED=1 && start "" /min "%~dpnx0" %* && exit
	@echo off
	@CD /D "%~dp0"
	color 0a
	cd ..
	cls
	python3 C:\Users\%username%\NodeViewer\__pycache__\ticker.cpython-310.pyc
exit
```
