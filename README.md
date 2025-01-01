# AI News and Papers Collector

## Overview
A LLM based notenook for collecting and analizing your articles, collections, notes and everything, help you to better understand the world and improve your thinking.

## Website
http://www.haowu.space/

## Features
- Base
    - Instant web content collecting from any open sources
    - PDF, HTML, Text... local file collection and metadata extraction
    - Searchable database of collected content
- Advanced
    - MCP powered integration function scaling
    - LLM/RAG/Agent powered idea generation and notes taking
    - Voice and even Podcast to summarize

## Setup
1. Clone the repository
2. Set up environment variables  
    2.1 setup safety env(password etc.)
        ```
        cd [projectRoot]
        vi .env-demo or scp .env remote:~/NewsReader/
        ```
    rename it to '.env' after setting  
    2.2 setup python(>=3.10) & venv
        ```
        sudo apt update
        sudo apt install python3.12-venv -y
        sudo ln -s /usr/bin/python3 /usr/bin/python
        python -m venv .venv
        ```
    2.3 use venv
        ```
        [linux/mac] source .venv/bin/activate
        [windows](using cmd, not powershell) 1. cd .venv/Scripts; 2. activate
        ```
3. Install dependencies(only first time): 
    `pip install -r requirements.txt`
4. Run the application
    [linux/mac]`.venv/bin/python src/app.py`
    [windows]`.venv/Scripts/python src/app.py`

## Technologies
- Python
- FastAPI/Flask
- SQLite
- Celery (for background tasks)
- NextJs (frontend)
- LLM
    - LlamaIndex
    - MCP

## Future Enhancements
- AI-powered content summarization
- Automated paper recommendation
- Integration with reference management tools

## Copyright
- The 'NewsReader' is a project launched and designed by [NEO@github](https://github.com/g29times).

## License
This project is licensed under the [Apache License](LICENSE).