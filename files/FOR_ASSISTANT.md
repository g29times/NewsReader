# 调用工具示例
## 1 知晓时间
DOC https://www.timeapi.io/swagger/index.html
curl -X 'GET' \
  'https://www.timeapi.io/api/time/current/zone?timeZone=Asia%2FShanghai' \
  -H 'accept: application/json'

## 2 内容阅读
### 临时内容存放文件
    temp_article_content.txt 存放PDF等解析出来的内容
    jina_read_from_url_response_demo.txt 存放JINA等API解析出来的网络内容
### 文件
src\utils\file_input_handler.py
    PDF extract_text_from_pdf
    文本文件 read_from_file
    其他文件：待定
    临时内容存放文件（覆盖）：src\utils\temp_article_content.txt
### 网页
python -c "print('Hello, World!')"
- 1 调用JINA API获取网页内容，并保存到本地 src\utils\jina_read_from_url_response_demo.txt
windows环境下务必使用 PowerShell 的 Start-Process 命令在后台运行 Python 脚本，否则对话会卡住
例如：
powershell -Command Start-Process python -ArgumentList '-c "from src.utils.file_input_handler import FileInputHandler; FileInputHandler.jina_read_from_url(\"https://blog.csdn.net/qq_63585949/article/details/136128693\", mode=\"write\")"' -NoNewWindow
- 2 查看本地文件
隔几秒查看一次，因为JINA的处理需要时间

## 3 通过Git查看本地未提交文件的历史变化（仅保存程序代码，不存储日志、临时文件、测试等）
https://www.geeksforgeeks.org/how-to-stash-a-specific-file-or-multiple-files-in-git/
https://geek-docs.com/git/git-questions/113_git_git_diff_against_a_stash.html
1 每次改动 都使用 git stash 保存修改的文件（多个文件用空格分隔）
git stash push -m "[TIME][SHORT DESCRIPTION]" -- <FILE RELATIVE PATH>
2 使用 git stash apply 恢复工作区
3 使用git diff来对比stash和工作区的内容


例子：
1 修改src\utils\jina_read_from_url_response_demo.txt和src\utils\temp_article_content.txt的内容
    内容替换为：“修改后：ADD”
2 暂存文件修改
    `git stash push -m "[2024-12-20T12:48:09][修改文本]" -- src/utils/jina_read_from_url_response_demo.txt src/utils/temp_article_content.txt`
    成功stash的响应：
    Saved working directory and index state On master: message=[2024-12-20T12:48:09] test
3 回到工作区
    `git stash apply`
4 git diff stash
    全部文件 `git diff stash@{0}`
    指定文件 `git diff stash@{0} -- src/utils/jina_read_from_url_response_demo.txt`
