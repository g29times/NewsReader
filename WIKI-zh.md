## Usage
### Lib
#### 安装
1 通过requirements0.txt 创建venv并安装pipreqs
2 用pipreqs扫描有效依赖 pipreqs
3 安装依赖 pip install -r requirements.txt
#### 依赖管理
`pip install pipreqs`
`pipreqs --ignore .venv --force`
https://cloud.tencent.com/developer/article/2464574
https://segmentfault.com/a/1190000020886718
`pipreqs --ignore .venv` # 解决uft-8问题
https://stackoverflow.com/questions/62496083/pipreqs-has-the-unicode-error-under-a-virtualenv

https://blog.csdn.net/Stromboli/article/details/143220261
https://blog.csdn.net/pearl8899/article/details/113877334
查看过时的库：使用 pip list --outdated 检查哪些库已经过时。
更新特定库：选择需要更新的库，使用 pip install --upgrade <库名> 进行更新。
```
pip install pipreqs
pipreqs --ignore .venv --force
or
pip install -r requirements.txt
pip freeze > requirements.txt
```

### Job
```
*/10 * * * * auto_push.sh
```
### Errors Handle
#### pip
`python -m pip install --upgrade --force-reinstall pip`
