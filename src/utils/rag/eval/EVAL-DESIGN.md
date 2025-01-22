# RAG 系统评估设计方案

## 使用指南
1. 使用 retrieve.py 收集RAG召回，并更新eval集（需关闭VPN）
2. 调整context_recall.py 相似度分值 使用 ragas_rag_eval.py 进行评估出分（需开启VPN）
3. 使用 rag_eval_vision.py 进行可视化（无需VPN）

## 零、横向评测设计

### 1. 评测维度

#### 输入维度
1. **文件大小 (File Size)**
   - 定义：文档的总字节大小
   - 取值：1MB, 5MB, 10MB等固定大小
   - 评测目的：验证系统在不同规模文档下的性能表现

2. **切块大小 (Chunk Size)**
   - 定义：每个文本块的token数量
   - 取值：100, 500, 1000等token数
   - 评测目的：找到信息完整性和检索精度的最佳平衡点

3. **上下文策略 (Context)**
   - 定义：是否在切块时保留段落上下文
   - 取值：true/false
   - 评测目的：验证上下文信息对答案质量的影响

4. **TopK**
   - 定义：检索时返回的相关文档数量
   - 取值：3, 5, 10等
   - 评测目的：确定信息冗余和答案质量的最佳平衡点

#### 输出指标
1. **AnswerRelevancy**
   - 评估答案与问题的相关性
   - 取值范围：[0,1]
   - 展示：折线图，横轴为变化维度

2. **ContextPrecision**
   - 评估检索结果的精确度
   - 取值范围：[0,1]
   - 展示：与AnswerRelevancy在同一图表中

3. **Faithfulness**
   - 评估答案的可信度
   - 取值范围：[0,1]
   - 展示：与其他指标在同一图表中

### 2. 数据消融实验

#### 实验设计
1. **固定维度组合**
   ```
   基准配置：
   - File Size: 5MB
   - Chunk Size: 500
   - Context: true
   - TopK: 5
   ```

2. **单维度变化实验**
   - 实验A：变化Chunk Size
     ```
     固定：File Size=5MB, Context=true, TopK=5
     变化：Chunk Size=[100, 300, 500, 700, 1000]
     ```
   - 实验B：变化TopK
     ```
     固定：File Size=5MB, Chunk Size=500, Context=true
     变化：TopK=[3, 5, 7, 10, 15]
     ```
   - 实验C：变化Context
     ```
     固定：File Size=5MB, Chunk Size=500, TopK=5
     变化：Context=[true, false]
     ```

#### 可视化方案
1. **主图表**：折线图
   - X轴：变化维度的取值
   - Y轴：三个指标得分
   - 图例：区分不同指标

2. **补充信息**
   - 固定参数值
   - 最佳组合推荐
   - 异常值分析


## 一、评估维度

### 1. 检索结果排序质量
评估检索系统对文档相关性的排序能力

| 场景 | 描述 | 预期表现 |
|------|------|----------|
| 最优排序 | 相关文档在前，不相关文档在后 | 高分 |
| 随机排序 | 相关文档随机分布 | 中等分数 |
| 最差排序 | 不相关文档在前，相关文档在后 | 低分 |

### 2. 检索结果相关度分布
评估检索系统的精确度和召回率

| 场景 | 描述 | 比例 |
|------|------|------|
| 高质量检索 | 大部分相关 + 少量不相关 | 80% 相关 + 20% 不相关 |
| 中等质量 | 部分相关 + 部分不相关 | 50% 相关 + 50% 不相关 |
| 低质量检索 | 少量相关 + 大部分不相关 | 20% 相关 + 80% 不相关 |

### 3. 答案覆盖情况
评估检索系统的完整性

| 场景 | 描述 | 示例 |
|------|------|------|
| 单文档完整 | 单个文档包含完整答案 | Q: "作者的ID是什么？" <br> Doc: "作者ID：复制忍者卡卡西" |
| 多文档组合 | 需要多个文档组合得到答案 | Q: "作者的联系方式有哪些？" <br> Doc1: "微信公众号：MY聊审计" <br> Doc2: "论坛ID：复制忍者卡卡西" |
| 部分覆盖 | 只能找到部分答案 | Q: "企业会计准则的更新时间？" <br> Doc: "部分准则在2014年更新" (缺少完整更新信息) |

## 二、测试数据生成策略

### 1. 基础数据结构
```json
{
  "id": "test_001",
  "question": "问题文本",
  "answer": "标准答案",
  "golden_chunk": "标准上下文",
  "retrieved": [
    "检索文档1",
    "检索文档2",
    "检索文档3"
  ]
}
```

### 2. 数据生成方法

1. **相关文档生成**：
   - 直接相关：包含完整答案
   - 间接相关：包含部分答案或相关背景
   - 主题相关：同主题但不含答案

2. **干扰文档生成**：
   - 同领域不同主题
   - 完全不相关主题
   - 包含关键词但语义不相关

3. **组合策略**：
   - 高质量组合：2个直接相关 + 1个间接相关
   - 中等质量：1个直接相关 + 1个间接相关 + 1个干扰
   - 低质量：1个间接相关 + 2个干扰

## 三、评估指标使用建议

1. **ContextPrecision**：
   - 用于评估检索结果的相关性
   - 重点关注排序质量
   - 分数低于0.8需要优化检索策略

2. **ContextRecall**：
   - 评估是否找到所有相关的上下文内容
   - 特别关注多文档组合场景
   - 分数低于0.7说明召回不足

3. **Faithfulness**：
   - 评估生成答案与上下文的一致性
   - 重点关注答案是否有幻觉
   - 分数低于0.9需要改进

4. **AnswerRelevancy**：
   - 评估答案与问题的相关性
   - 关注答案是否切中要点
   - 分数低于0.8需要优化


## 四、持续优化建议

1. **定期更新测试集**：
   - 根据实际应用场景补充新case
   - 保持测试数据的多样性
   - 关注特殊场景和边界情况

2. **动态调整评估标准**：
   - 根据用户反馈调整指标权重
   - 针对性能瓶颈优化评估方案
   - 持续收集失败案例


## 五、指标解释

### 1. 核心评估三元组

```
问题 ─── answer_relevancy ─── 答案 ─── faithfulness ─── 上下文 ─── context_precision/recall ─── 问题
```
### 2. 输入详解
- user_input: 即用户提的问题
- response: LLM的回答
- reference ground: truth 参考答案
- retrieved_contexts: 召回文本段
- reference_contexts: golden chunk 参考文档

### 3. 指标详解

1. **AnswerRelevancy (答案相关性)**
```
MetricType.SINGLE_TURN: {"user_input", "response"}
```
   - 含义：衡量生成答案和查询之间的相关性
   - 评估重点：答案是否准确回答了用户的问题
   - 使用场景：不需要参考答案，适合大规模评估

2. **Faithfulness (可信度)**
```
MetricType.SINGLE_TURN: {"user_input", "response", "retrieved_contexts"}
```
   - 含义：确保答案是基于给定上下文生成的，避免幻觉
   - 评估重点：答案中的每个事实陈述是否都能在上下文中找到支持
   - 使用场景：检测模型是否产生了虚构信息

3. **ContextPrecision (上下文精度)**
``` ContextUtilization/LLMContextPrecisionWithoutReference
MetricType.SINGLE_TURN: {"user_input", "response", "retrieved_contexts"}
```
``` ContextPrecision/LLMContextPrecisionWithReference
MetricType.SINGLE_TURN: {"user_input", "retrieved_contexts", "reference"}
```
   - 含义：衡量检索到的上下文中有多少是真正相关的，以及相关内容的排序质量
   - 评估重点：
     - 检索结果的相关性
     - 相关文档的排序质量
   - 评分机制：使用平均精度（Average Precision）计算
   ```python
   # 对于每个位置i的文档：
   # 1. 计算当前位置的精度：sum(相关文档[:i+1]) / (i+1)
   # 2. 如果当前文档相关，将精度计入总分
   # 3. 最后除以相关文档总数得到AP
   score = sum((前i个文档中相关文档数/i) * 是否相关[i]) / 相关文档总数
   ```

4. **ContextRecall (上下文召回率)**
```
MetricType.SINGLE_TURN: {"user_input","retrieved_contexts","reference"}
```
   - 含义：衡量检索系统是否找到了所有相关的上下文内容
   - 评估重点：是否遗漏了重要信息
   - 特点：
      - 将所有召回文档合并后整体评估
      - 让LLM判断合并文档是否包含了回答问题（参考标准答案）所需的全部信息

5. FactualCorrectness 事实正确性
```
MetricType.SINGLE_TURN: {"response", "reference"}
```

6. NonLLMContextRecall
```
MetricType.SINGLE_TURN: {
      "retrieved_contexts",
      "reference_contexts",
}
```
7. NonLLMContextPrecisionWithReference
```
MetricType.SINGLE_TURN: {
      "retrieved_contexts",
      "reference_contexts",
}
```

### 4. 评分特点

1. **无需参考答案的指标**
   - AnswerRelevancy
   - Faithfulness
   - LLMContextPrecisionWithoutReference (不需要 reference 的上下文精度)
   
2. **需要参考答案的指标**
   - ContextRecall (需要 reference)
   - ContextPrecision 
   - FactualCorrectness (需要 reference)

3. **评分机制特点**
   - 采用[0,1]区间的标准化分数
   - ContextPrecision特别关注排序质量，靠前的相关文档贡献更高分数
   - 大多数指标支持批量评估，可以获得整体性能统计
