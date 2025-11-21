"""
转换旧的 answersheet.json 格式到新的示例模板格式
"""
import json


def convert_answersheet():
    """读取旧格式的 answersheet.json 并转换为新格式"""
    
    # 读取旧格式文件
    with open("answersheet.json", "r", encoding="utf-8") as f:
        old_data = json.load(f)
    
    # 构建新格式
    new_data = {
        "items": []
    }
    
    # 转换每个答案条目
    for answer in old_data.get("answers", []):
        # 提取召回内容的文本
        retrieved_contexts = answer.get("retrieved_contexts", [])
        
        # 如果 retrieved_contexts 是字符串列表，则直接使用
        # 否则尝试从 "result" 字段提取内容
        if not retrieved_contexts:
            retrieved_contexts = [
                item.get("content", "") 
                for item in answer.get("result", [])
            ]
        
        # 构建新条目
        new_item = {
            "question": answer.get("question", ""),
            "retrieved_contexts": retrieved_contexts,
            "answer": answer.get("answer", "")
        }
        
        new_data["items"].append(new_item)
    
    # 保存新格式文件
    with open("answersheet.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 转换完成！共转换 {len(new_data['items'])} 个问题")
    print(f"✓ 已保存到 answersheet.json")


if __name__ == "__main__":
    convert_answersheet()