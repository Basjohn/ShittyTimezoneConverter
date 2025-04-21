#!/bin/bash
# Linux: Build standalone executable with PyInstaller
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --distpath dist/linux_onefile --workpath build/linux_onefile -y --onefile src/main.py --name=shitty-timezone-converter --noconsole
