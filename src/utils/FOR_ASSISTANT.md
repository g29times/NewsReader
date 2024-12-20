# 调用工具示例
## 知晓时间
DOC https://www.timeapi.io/swagger/index.html
curl -X 'GET' \
  'https://www.timeapi.io/api/time/current/zone?timeZone=Asia%2FShanghai' \
  -H 'accept: application/json'

## 网页内容爬虫
python -c "print('Hello, World!')"
- 1 调用JINA API获取网页内容，并保存到本地 src\utils\jina_read_from_url_response_demo.txt
windows环境下务必使用 PowerShell 的 Start-Process 命令在后台运行 Python 脚本，否则对话会卡住
例如：
powershell -Command Start-Process python -ArgumentList '-c "from src.utils.file_input_handler import FileInputHandler; FileInputHandler.jina_read_from_url(\"https://blog.csdn.net/qq_63585949/article/details/136128693\", mode=\"write\")"' -NoNewWindow
- 2 查看本地文件
隔几秒查看一次，因为JINA的处理需要时间

## 通过Git查看本地未提交文件的历史变化
1 每次改动 都使用 git stash 保存修改的文件
git stash push -m "message=[TIME] Cascade" -- <FILE RELATIVE PATH>
2 使用 git stash apply 恢复工作区
3 使用git diff来对比stash和工作区的内容

例子：
1 修改src\utils\jina_read_from_url_response_demo.txt的内容
    内容替换为：“修改后：ADD”
2 git stash jina_read_from_url_response_demo.txt 文件
    'git stash push -m "message=[2024-12-20T12:48:09] test" -- src/utils/jina_read_from_url_response_demo.txt'
    成功stash的响应：
    Saved working directory and index state On master: message=[2024-12-20T12:48:09] test
3 git stash apply
    
4 git diff