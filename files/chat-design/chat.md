# Chat 页面设计文档

## 路由设计
- 页面路由: `/chat`
- API 路由: 
  - `/api/chat/send` - 发送消息
  - `/api/chat/history` - 获取聊天历史
  - `/api/articles/search` - 搜索文章（用于左侧列表）
  - `/api/articles/<article_id>` - 获取文章详情

## 页面布局
三栏布局设计：
1. 左侧文章列表 (300px)
   - [x] 基础列表显示（仅标题）
   - [ ] 文章搜索功能
   - [X] 文章展开/折叠详情
   - [ ] 文章分页加载

2. 中间聊天区域 (自适应)
   - [x] 消息显示区域
   - [x] 消息输入框
   - [x] 发送按钮
   - [ ] 消息历史记录
   - [ ] 消息状态显示
   - [ ] 工具栏功能实现：
     - [ ] 文件上传
     - [ ] 语音输入
     - [ ] 图片上传

3. 右侧笔记区域 (300px)
   - [ ] 笔记编辑器
   - [ ] 笔记保存功能
   - [ ] 笔记分类
   - [ ] 笔记搜索

## 功能清单

### 第一阶段（基础功能）
1. [x] 添加基础路由 `/chat`
2. [x] 实现文章列表获取和显示
3. [ ] 实现基础聊天功能
4. [ ] 添加消息历史记录
5. [ ] 实现文章搜索
6. [x] 实现获取文章详情的 API 路由 `/api/articles/<article_id>`

### 第二阶段（增强功能）
1. [x] 实现文章详情展开/折叠
2. [ ] 添加文章分页
3. [ ] 实现笔记功能
4. [ ] 添加文件上传
5. [ ] 添加语音输入

### 第三阶段（高级功能）
1. [ ] 实现多轮对话
2. [ ] 添加上下文管理
3. [ ] 实现会话保存
4. [ ] 添加导出功能
5. [ ] 实现协同编辑

## 技术栈
- 前端：HTML, CSS, JavaScript, Bootstrap
- 后端：Python, Flask
- 数据库：SQLite
- AI：Gemini API

## 开发顺序
1. 基础路由设置
2. 文章列表功能
3. 基础聊天功能
4. 消息历史
5. 笔记功能
6. 对话记忆
7. 人格设定
8. 主动对话