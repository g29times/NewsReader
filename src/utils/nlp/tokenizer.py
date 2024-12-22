from cgitb import text
import jieba

# https://www.cnblogs.com/python-xkj/p/9247265.html
# https://www.shenlanxueyuan.com/course/621/task/23988/show
# https://blog.csdn.net/iceliooo/article/details/142204897
# https://blog.csdn.net/qq_33578950/article/details/130155988

text = "我还给页面增加了基础的增删改查功能。"
tokens = jieba.lcut(text)
print(tokens)

import nltk
nltk.download('punkt')
# nltk.download('punkt_tab')
# nltk.download('popular') # punkt
from nltk.tokenize import word_tokenize
text = "Hello, world!"
tokens = word_tokenize(text)
print(tokens)