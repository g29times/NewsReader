# doc
https://modelcontextprotocol.io/introduction
https://modelcontextprotocol.io/quickstart
https://github.com/modelcontextprotocol/python-sdk

# config
cline_mcp_settings.json
## windows folder
C:\Users\SWIFT\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings
## linux

# open servers
https://github.com/modelcontextprotocol/servers?tab=readme-ov-file

# commands
`npx` and `uv` for node and Python servers respectively.
## uv（Python）
uv venv .venv
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer
### install and config
#### windows
`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
##### set Admin
https://bobbyhadz.com/blog/run-vscode-or-the-vscode-terminal-as-an-administrator
1. manally set
2. check
`net session`
3. * for PowerShell
`Set-ExecutionPolicy Unrestricted -Scope Process`

## npx
npx @modelcontextprotocol/create-server weather-server

# Test
https://r.jina.ai/
https://www.guoxuemeng.com/yingyuzuowen/577110.html

# TODO
    node and nv work
    npx not work
    python need test
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    },
    "mcp-installer": {
      "command": "npx",
      "args": [
        "@anaisbetts/mcp-installer"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/username/Desktop",
        "/path/to/other/allowed/dir"
      ]
    },
    连接失败
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },