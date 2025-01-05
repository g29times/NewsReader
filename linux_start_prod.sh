exec bash
source .venv/bin/activate
nohup python src/app.py >newsreader.log 2>&1 &
