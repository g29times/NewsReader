# Article 文章模块设计文档

## BUG/TODO/待优化项
1. 文章批量导入功能
2. 文章内容预览
3. 高级搜索功能
4. 文章分类管理
5. 导出功能

### 技术栈
- 数据库：SQLAlchemy (SQLite)
- 向量库：Milvus
- 内容处理：JINA Reader
- AI处理：LLM (Gemini)

## 1. 产品设计

### 1.1 核心功能
1. **文章管理**
   - 添加文章（URL/文件上传）
   - 删除文章
   - 更新文章标签
   - 文章列表展示
   - 文章搜索

2. **内容处理**
   - URL内容抓取 (JINA Reader)
   - 文章内容摘要生成 (LLM)
   - 向量化存储

3. **文章关联**
   - 支持多文章关联
   - 关联内容自动合并

### 1.2. 界面设计

#### 1.2.1 页面布局
```
+----------------------------------+
|  搜索栏 + 语言切换               |
+----------------------------------+
|  URL输入 + 标签 + 添加/向量化按钮 |
+----------------------------------+
|  表格头部（固定）                |
|  - 选择框                       |
|  - 标题                         |
|  - 摘要                         |
|  - 标签                         |
|  - 日期                         |
+----------------------------------+
|  文章列表（可滚动）              |
|  ...                            |
+----------------------------------+
```

#### 1.2.2 交互功能
1. **文章操作**
   - 全选/取消全选
   - 标签编辑
   - 文章删除
   - 批量向量化

2. **展示优化**
   - 摘要长度限制(500字)
   - 关键点悬浮提示
   - 标签编辑弹窗
   - Toast消息提示

3. **多语言支持**
   - 中文/英文切换
   - 界面文本自动适配

## 2. 技术设计

### 2.1 文章模型 (Article)
```python
class Article:
    # 基本信息
    id: Integer         # 主键
    title: String      # 标题(必填,唯一)
    url: String        # 来源URL(可选)
    content: Text      # 原文内容(必填)
    
    # AI生成字段
    summary: Text      # 文章摘要
    key_topics: String # 关键主题
    vector_ids: String # 向量ID列表(逗号分隔)
    
    # 元数据
    source: String     # 来源类型(website/github/paper)
    type: String       # 资源类型(WEB/FILE/NOTE)
    tags: String       # 人工标签
    authors: String    # 作者
    
    # 时间信息
    collection_date: DateTime  # 收集时间
    publication_date: String   # 发布时间(由LLM提取)
    
    # 关联
    user_id: Integer   # 创建用户ID
```

### 2.2 API设计
```
article_routes
├── GET  /article/                # 文章列表页面
├── POST /article/add_article     # 添加文章
├── POST /article/delete/<id>     # 删除文章
├── POST /article/update/<id>     # 更新文章
├── GET  /article/search          # 搜索文章
└── POST /article/batch_vector    # 批量向量化
```

### 2.3 关键流程
1. **添加文章流程**
   1. 获取表单数据
   2. 检查URL重复
   3. 获取文章内容
   4. 处理关联文章
   5. LLM内容处理
   6. 数据入库
   7. 向量存储

2. **文章搜索流程**
   1. 获取搜索关键词
   2. 数据库模糊匹配
   3. 结果排序返回

## 3. 开发进度
1. 文章批量导入功能
2. 文章内容预览
3. 高级搜索功能
4. 文章分类管理
5. 导出功能