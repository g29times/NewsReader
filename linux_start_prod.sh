pkill -9 -f "python src/app.py"
nohup .venv/bin/python src/app.py >newsreader.log 2>&1 &
echo ps -ef | grep python
