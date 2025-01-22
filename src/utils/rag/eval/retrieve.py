import requests
import json
from typing import List, Dict, Union

def retrieve_docs(query: str, user_id: str, doc_ids: List[str], rn: int = 5) -> List[str]:
    """
    调用检索接口获取相关文档
    
    Args:
        query: 查询问题
        doc_ids: 文档ID列表
        rn: 返回的文档数量，默认5个
    
    Returns:
        List[str]: 检索到的文档内容列表
    """
    url = "http://ifootoo.com:8094/search"
    
    payload = json.dumps({
        "user_id": user_id,
        "queries": query,
        "doc_ids": doc_ids,
        "rn": rn
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()  # 检查响应状态
        
        # 解析响应
        result = response.json()
        if not result.get('data'):
            return []
            
        # 提取所有文档的content
        contents = []
        for answer in result['data'][0]:
            if answer.get('content'):
                contents.append(answer['content'])
        print("Retrieved documents:", len(contents))
        return contents
        
    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return []

def update_evaluation_set(eval_file: str, user_id: str, doc_ids: List[str], topk: int=5, output_file: str = None) -> None:
    """
    更新评估集的retrieved属性
    
    Args:
        eval_file: 评估集JSON文件路径
        output_file: 输出文件路径，默认覆盖原文件
    """
    try:
        # 读取评估集
        with open(eval_file, 'r', encoding='utf-8') as f:
            eval_data = json.load(f)
            
        # 遍历每个评估项
        for item in eval_data:
            # 获取检索结果
            retrieved_docs = retrieve_docs(
                query=item['question'],
                user_id=user_id,
                doc_ids=item.get('doc_ids', doc_ids),  # 默认使用文档ID 2
                rn=topk
            )
            
            # 更新retrieved属性
            if retrieved_docs:
                item['retrieved'] = retrieved_docs
        
        # 保存更新后的评估集
        output_path = output_file or eval_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully updated evaluation set: {output_path}")
        
    except Exception as e:
        print(f"Error updating evaluation set: {str(e)}")

if __name__ == "__main__":
# 说明：提问，并返回rag召回的文档，支持将返回数据填充到评估集中
# 入参：user_id 固定，doc_ids - 文档id， queries - 问题，rn - topk
# 返回格式：见 src\utils\rag\data\retrive_response.json

    # 示例用法
    # 1. 直接获取检索结果
    # docs = retrieve_docs("这份企业会计准则资料的作者在中国会计视野论坛的ID是什么？", ["2"])
    
    # 2. 更新评估集
    update_evaluation_set("src/utils/rag/data/rag_instruct_benchmark_20.jsonl", "5008", ["44"], 5)
