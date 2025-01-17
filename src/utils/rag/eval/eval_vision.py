# 目标： 构建一个可视化的评估系统，用于综合考量不同 RAG 配置（文件大小、切块大小、是否带上下文、topk）下的性能表现（RAGAS 指标）。
# 输入：

# 文件大小 (File Size): 可以是具体的数值 (例如 1MB, 10MB) 或范围 (例如 1MB-5MB)。
# 切块大小 (Chunk Size): 以 token 数为单位，例如 100, 500, 1000。
# 是否带上下文 (Context): 布尔值，表示切块是否包含上下文信息。
# TopK:  表示给 LLM 的上下文块数量, 例如 5, 10, 20。

# 输出：

# RAGAS 指标 (RAGAS Metrics): 选择三个主流指标，例如 answer_relevancy, context_precision, faithfulness。

# 可视化：

# 四个输入维度，如果用表格，会更加复杂，难以展示多个维度之间的关系。
# 一个输出维度，需要选择合适的方式来展示多个指标。

# 可视化方案

# 1 多图表组合仪表盘 (增强版)： (仍然推荐这个方案，更灵活！✨)

# 核心思想： 将不同的输入维度和输出指标拆分到不同的图表中，然后将这些图表组合成一个仪表盘。
# 具体实现：
# 热力图 (Heatmap)：
# x 轴：切块大小 (Chunk Size)
# y 轴：TopK
# 颜色：RAGAS 指标 (例如 answer_relevancy, context_precision, faithfulness)，每个指标一个热力图。
# 每个图表展示一个文件大小 (File Size) 和是否带上下文 (Context) 的组合。
# 交互式控件：
# 使用下拉菜单或滑块来选择文件大小 (File Size) 和是否带上下文 (Context)，切换显示不同组合下的评估结果。
# 优点：
# 可以清晰地展示切块大小和 TopK 对 RAGAS 指标的影响。
# 可以比较不同文件大小和是否带上下文组合下的性能表现。
# 可以通过交互式控件来探索数据。
# 缺点：
# 需要一定的可视化库支持 (例如 matplotlib, seaborn, plotly)。
# 需要一定的编程能力。

# 2 平行坐标图 (增强版)：

# 核心思想: 将每个输入维度和输出指标都表示为一条平行轴，每条折线表示一个 RAG 配置。
# 具体实现：
# 平行轴: 文件大小 (File Size), 切块大小 (Chunk Size), 是否带上下文 (Context), TopK, RAGAS 指标 (例如 answer_relevancy, context_precision, faithfulness)。
# 每条折线表示一个 RAG 配置的性能表现。
# 优点:
# 可以展示所有维度之间的关系。
# 可以比较不同 RAG 配置的整体性能。
# 缺点:
# 如果数据量太大，图表可能会比较拥挤。
# 用户可能需要一些时间来理解平行坐标图。

# 3 三维散点图 (结合切片)：

# 核心思想： 使用三维散点图展示部分维度，并通过切片的方式展示剩余维度。
# 具体实现：
# x 轴：切块大小 (Chunk Size)
# y 轴：TopK
# z 轴：RAGAS 指标，可以使用多个图表展示不同的指标。
# 颜色：是否带上下文 (Context)
# 使用滑动条或下拉菜单选择文件大小 (File Size)，动态展示不同文件大小下的三维散点图。
# 优点：
# 可以同时展示多个维度之间的关系。
# 可以直观地看到不同 RAG 配置的性能差异。
# 缺点：
# 三维图表可能不够直观，用户可能需要一些时间来理解。
# 需要专业的三维可视化库支持。

# RAGAS 集成建议 (更新版)

# 数据准备：
# 你需要准备不同大小的文档，并根据不同的切块大小和是否带上下文进行切块。
# 为每个切块生成对应的上下文信息 (如果需要)。
# 将所有切块及其对应的上下文信息存储在一个数据集中。
# RAG 评估：
# 使用不同的 RAG 配置 (文件大小、切块大小、是否带上下文、TopK) 从数据集中检索相关文档。
# 使用 ragas.evaluate 函数评估 RAG 系统的性能，并获取 RAGAS 指标。
# 数据分析和可视化：
# 将评估结果存储在一个数据结构中，例如 Pandas DataFrame。
# 使用上述可视化方案将评估结果可视化。

# 代码示例 (Python + Pandas + Plotly) (更新版)
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from ragas import evaluate
from datasets import Dataset
import numpy as np
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    faithfulness,
)

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def generate_dummy_data(real_data=None):
    """生成虚拟数据，并用真实数据替换指定组合"""
    data = []
    file_sizes = [100000, 500000, 1000000] # 100k, 500k, 1M
    chunk_sizes = [100, 500, 1000]
    with_contexts = [True, False]
    topk_values = [5, 10, 20]

    for file_size in file_sizes:
        for with_context in with_contexts:
            for chunk_size in chunk_sizes:
                for topk in topk_values:
                    # 模拟RAG系统评估逻辑
                    answer_relevancy_score = np.random.uniform(0.6, 1.0)
                    context_precision_score = np.random.uniform(0.5, 1.0)
                    faithfulness_score = np.random.uniform(0.7, 1.0)
                    
                    data.append({
                        'file_size': file_size,
                        'chunk_size': chunk_size,
                        'with_context': with_context,
                        'topk': topk,
                        'answer_relevancy': answer_relevancy_score,
                        'context_precision': context_precision_score,
                        'faithfulness': faithfulness_score,
                    })
    return pd.DataFrame(data)


def create_dashboard(df):
    """创建可视化仪表盘"""
    unique_file_sizes = df['file_size'].unique()
    unique_contexts = df['with_context'].unique()
    metrics = ['answer_relevancy', 'context_precision', 'faithfulness']
    chunk_sizes = [100, 500, 1000]
    topk_values = [5, 10, 20]

    num_rows = len(unique_file_sizes) * len(unique_contexts)
    num_cols = len(metrics)

    fig = make_subplots(rows=num_rows, cols=num_cols, subplot_titles=[
        f"File Size: {size}, Context: {context} - {metric}"
        for size in unique_file_sizes
        for context in unique_contexts
        for metric in metrics
    ])

    row_index = 1
    for file_size in unique_file_sizes:
        for context in unique_contexts:
            df_subset = df[(df['file_size'] == file_size) & (df['with_context'] == context)]
            for col_index, metric in enumerate(metrics):
               # 现在，我们直接使用 'topk' 作为 index, 'chunk_size' 作为 columns
                heatmap_data = df_subset.pivot_table(index='topk', columns='chunk_size', values=metric, aggfunc='mean')
                fig.add_trace(go.Heatmap(
                    z=heatmap_data.values,
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    colorscale='Viridis',
                    showscale=False,
                    hovertemplate='Chunk Size: %{x}<br>TopK: %{y}<br>Score: %{z}<extra></extra>'
                ), row=row_index, col=col_index + 1)
                
                fig.update_xaxes(
                    tickvals=chunk_sizes,
                    ticktext=chunk_sizes,
                    row=row_index,
                    col=col_index + 1)
                
                fig.update_yaxes(
                    tickvals=topk_values,
                    ticktext=topk_values,
                    row=row_index,
                    col=col_index + 1)

            row_index += 1

    # 添加一个共享的 colorbar
    fig.add_trace(go.Heatmap(
        z=[[0, 1]],
        colorscale='Viridis',
        showscale=True,
    ), row=1, col=1)

    fig.update_layout(title='RAG Evaluation Dashboard', showlegend=False, coloraxis_showscale=True,
    coloraxis_colorbar=dict(
        x=1.1,
        xanchor="left"
    ))
    fig.show()



if __name__ == '__main__':
    # 示例用法
    df = generate_dummy_data()
    create_dashboard(df)
