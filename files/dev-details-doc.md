# 开发细节手册

# 后端部分
# Python
关注classmethod实例方法和静态（类）方法staticmethod(tool)
在try catch的catch部分，遇到local variable 'response' referenced before assignment
，需要再次try catch

# LLM部分
- 变量
    问题 question 
    内容 content=input_text=text
    上下文（可选） context

- 基本参数设置 top-k 等，导致召回不正常，见
https://blog.csdn.net/u012856866/article/details/140308083

- 调用超时或不够时间
    对于大段文本，如果本地超时时间太短requests.post(timeout=60)，LLM还没返回

- LLM返回的异常码：
    Google
        错误的Key 4xx 403 账号权限
        地区禁止  
        服务端繁忙 5xx

# 前端部分
## API调试
文章详情
http://localhost:5000/chat/api/articles/87

# 部署手册

## 环境准备

### 系统要求
- Ubuntu Server LTS
- Python 3.8+
- Nginx
- Supervisor

### 系统包安装
```bash
# 更新系统
sudo apt update
sudo apt upgrade

# 安装必要的系统包
sudo apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools nginx supervisor
```

## 项目部署

### 1. 基础设置
```bash
# 创建项目目录
mkdir -p /var/www/newsreader
cd /var/www/newsreader

# 从代码仓库克隆代码
git clone [仓库地址] .

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装项目依赖
pip install -r requirements.txt
pip install gunicorn  # 生产环境WSGI服务器
```

### 2. Supervisor配置
创建配置文件：`/etc/supervisor/conf.d/newsreader.conf`

```ini
[program:newsreader]
directory=/var/www/newsreader
# worker数量： 使用了 -w 5，建议使用 2 * CPU核心数 + 1
command=/var/www/newsreader/venv/bin/gunicorn -w 5 -b 0.0.0.0:5000 src.app:app
command=/var/www/newsreader/venv/bin/gunicorn --workers 5 --bind 0.0.0.0:5000 --timeout 30 --worker-class sync --log-level info  src.app:app
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/newsreader/gunicorn.err.log
stdout_logfile=/var/log/newsreader/gun corn.out.log

[supervisord]
logfile=/var/log/supervisor/supervisord.log
```

### 3. Nginx配置
创建配置文件：`/etc/nginx/sites-available/newsreader`

```nginx
server {
    listen 80;
    server_name your_domain.com;  # 替换成实际域名

    # 静态文件处理
    location /static {
        alias /var/www/newsreader/src/webapp/static;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4. 服务启动
```bash
# 创建日志目录
sudo mkdir -p /var/log/newsreader

# 设置权限
sudo chown -R www-data:www-data /var/www/newsreader
sudo chown -R www-data:www-data /var/log/newsreader

# 启用Nginx配置
sudo ln -s /etc/nginx/sites-available/newsreader /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx

# 启动Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start newsreader
```

### 5. SSL配置（可选）
```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your_domain.com
```

## 维护指南

### 1. 服务管理命令
```bash
# 重启应用
sudo supervisorctl restart newsreader

# 重启Nginx
sudo systemctl restart nginx

# 查看应用状态
sudo supervisorctl status newsreader
```

### 2. 日志查看
```bash
# 应用日志
tail -f /var/log/newsreader/gunicorn.err.log
tail -f /var/log/newsreader/gunicorn.out.log

# Nginx日志
tail -f /var/log/nginx/error.log
```

### 3. 环境变量
- 复制`.env.example`为`.env`
- 修改生产环境的配置参数
- 确保敏感信息安全性

### 4. 注意事项
1. 确保服务器防火墙开放80（HTTP）和443（HTTPS）端口
2. 定期备份数据和配置文件
3. 设置日志轮转防止日志文件过大
4. 定期更新系统和依赖包
5. 建议配置服务器监控（如Prometheus + Grafana）

## 故障排查

### 1. 应用无法启动
- 检查supervisor日志
- 确认gunicorn是否正确安装
- 验证项目路径和权限

### 2. 静态文件404
- 检查Nginx配置中的static路径
- 确认文件权限
- 验证文件是否存在

### 3. 502错误
- 检查gunicorn是否运行
- 确认端口配置
- 查看error日志
