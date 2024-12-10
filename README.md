# AI News and Papers Collector

## Overview
A comprehensive system for collecting, organizing, and managing AI news articles and research papers.

## Features
- Web scraping from multiple AI news sources
- PDF paper collection and metadata extraction
- Searchable database of collected content
- User-friendly web interface

## Setup
1. Clone the repository
2. Set up environment variables
    ```
    # 1 setup safety password
    touch .env
    # 2 setup project env
    sudo apt install python3.12-venv -y
    python3 -m venv .venv
    # 3 use venv
    source .venv/bin/activate
    ```
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application `python src/webapp/article.py python3 src/webapp/article.py`

## Technologies
- Python
- FastAPI/Flask
- SQLAlchemy
- Scrapy/BeautifulSoup
- Celery (for background tasks)
- NextJs (frontend)

## Planned Sources
- arXiv
- Google Scholar
- AI News Websites
- Research Lab Blogs

## Future Enhancements
- AI-powered content summarization
- Automated paper recommendation
- Integration with reference management tools

## Acknowledgments
- The AI News and Papers Collector is a project by [NEO LEE](https://github.com/g29times).

## License
This project is licensed under the [Apache License](LICENSE).

## Usage
### Lib
#### 安装
1 通过requirements0.txt 创建venv并安装pipreqs
2 用pipreqs扫描有效依赖 pipreqs
3 安装依赖 pip install -r requirements.txt
#### 归集管理
pip install pipreqs
https://cloud.tencent.com/developer/article/2464574
https://segmentfault.com/a/1190000020886718
pipreqs --ignore .venv
https://stackoverflow.com/questions/62496083/pipreqs-has-the-unicode-error-under-a-virtualenv

https://blog.csdn.net/Stromboli/article/details/143220261
https://blog.csdn.net/pearl8899/article/details/113877334
查看过时的库：使用 pip list --outdated 检查哪些库已经过时。
更新特定库：选择需要更新的库，使用 pip install --upgrade <库名> 进行更新。
```
pip install -r requirements.txt
pip freeze > requirements.txt
or
pip install pipreqs
pipreqs /path/to/your/project
```

### Job
```
*/10 * * * * auto_push.sh
```
### Python Lib Errors
`python -m pip install --upgrade --force-reinstall pip`
