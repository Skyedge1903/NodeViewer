# NodeViewer

## Get the latest version

[Download the latest version](https://github.com/Skyedge1903/NodeViewer/archive/refs/heads/main.zip)
and then Unzip the file in the destination of your choice.

## Compile you own version

Run the following command in the root directory of the project:
```bash
python -m py_compile ticker.py
```

## Linux Installation

First install python 3.10.0 or higher :
```bash
sudo apt-get install python3.10
```

Installation of libraries :

```bash
pip install pyserial
pip install requests
```

Then you can run the following command (replace with your directories) to run the program :
```bash
python3 ~/NodeViewer/__pycache__/ticker.cpython-310.pyc
```

[Launch the script at startup](https://help.ubuntu.com/stable/ubuntu-help/startup-applications.html.en)
for ubuntu.

## Windows Installation
