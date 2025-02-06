# Notes 笔记 设计文档

## BUG/TODO/待优化项
1. 笔记内容预览功能
2. 笔记分类和标签管理
3. 笔记搜索功能
4. 笔记导出功能
5. 离线存储支持

### 技术栈
- Notion API：笔记存储和管理
- Flask：Web服务
- Python SDK：notion-sdk-py

## 1. 产品设计

### 1.1 核心功能
1. **笔记创建**
   - 支持多种类型笔记（CHAT/ARTICLE/NOTE/BLOG/IDEA/MEMORY）
   - 自动分页处理长文本
   - 关联文章和聊天记录

2. **笔记组织**
   - 按类型分类存储
   - 支持多数据库管理
   - 关联功能（文章/聊天/来源）

3. **内容处理**
   - 长文本自动分块
   - 富文本格式支持
   - 多媒体内容支持

### 1.2 笔记类型
1. **聊天笔记 (CHAT)**
   - 简单内容保存
   - 自动记录对话上下文
   - 支持快速回顾

2. **文章笔记 (ARTICLE)**
   - URL关联
   - 主题标记
   - 摘要生成

3. **普通笔记 (NOTE)**
   - 个人笔记
   - 支持关联文章和聊天
   - 自定义来源标记

## 2. 技术设计

### 2.1 数据结构
```python
class Note:
    # 基本信息
    title: str          # 笔记标题
    content: str        # 笔记内容
    types: list         # 笔记类型[CHAT/ARTICLE/NOTE/BLOG/IDEA/MEMORY]
    
    # 类型特定属性
    ## 文章笔记
    url: str           # 文章链接
    topics: list       # 主题列表
    summary: str       # 文章摘要
    
    ## 普通笔记
    articles: list     # 关联文章ID
    chats: list       # 关联聊天ID
    source: str       # 来源(Personal等)
```

### 2.2 API设计
```
note_routes
├── POST /note/create              # 创建笔记
│   ├── 请求参数
│   │   ├── title: str            # 笔记标题
│   │   ├── content: str          # 笔记内容
│   │   ├── types: list           # 笔记类型
│   │   └── properties: dict      # 类型特定属性
│   └── 响应
│       ├── success: bool         # 是否成功
│       └── data: dict           # 创建的笔记信息
```

### 2.3 关键流程
1. **创建笔记流程**
   1. 接收请求参数
   2. 根据类型选择处理方法
   3. 内容分块（如果需要）
   4. 调用Notion API
   5. 返回结果

2. **长文本处理流程**
   1. 按段落分割文本
   2. 检查段落长度
   3. 必要时进行句子分割
   4. 确保块大小不超过限制
   5. 返回分割后的文本块

### 2.4 存储设计
1. **Notion数据库**
   - CHAT_DATABASE_ID：聊天记录
   - ARTICLE_DATABASE_ID：文章笔记
   - NOTE_DATABASE_ID：普通笔记

2. **环境配置**
   - NOTION_API_KEY：API密钥
   - NOTION_VERSION：API版本

## 3. 开发进度
1. [x] 基础笔记创建功能
2. [x] 长文本自动分页
3. [x] 多类型笔记支持
4. [ ] 笔记搜索功能
5. [ ] 笔记管理界面
