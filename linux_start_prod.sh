source .venv/bin/activate
nohup python3 src/webapp/article.py >newsreader.log 2>&1 &

source .venv/bin/activate
nohup python src/app.py >newsreader.log 2>&1 &