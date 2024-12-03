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
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run the application
    `python.exe m:/WorkSpace/Dev/NewsReader/src/webapp/article.py`

## Technologies
- Python
- FastAPI/Flask
- SQLAlchemy
- Scrapy/BeautifulSoup
- Celery (for background tasks)
- React/Vue.js (frontend)

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
- The AI News and Papers Collector is a project by [Your Name](https://github.com/YourUsername).

## License
This project is licensed under the [MIT License](LICENSE).

## Library Usage
https://blog.csdn.net/Stromboli/article/details/143220261
https://blog.csdn.net/pearl8899/article/details/113877334
查看过时的库：使用 pip list --outdated 检查哪些库已经过时。
更新特定库：选择需要更新的库，使用 pip install --upgrade <库名> 进行更新。
pip install -r requirements.txt

pip install pipreqs
pipreqs /path/to/your/project
or
pip freeze > requirements.txt

Python Lib Errors
`python -m pip install --upgrade --force-reinstall pip`