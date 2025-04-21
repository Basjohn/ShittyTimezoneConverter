#!/bin/bash
# MacOS: Run Shitty Timezone Converter from source
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m src.main
