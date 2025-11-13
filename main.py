"""
主程序：读取整个试卷JSON，生成完整答卷JSON
"""
from agent import QAAgent
from json_handler import AnswerCard
import json
import time
from datetime import datetime


def main():
    """主函数：处理整个试卷"""
    print("="*60)
    print("基于难度分级的RAG问答系统")
    print("="*60)
    
    # 1. 设置输入输出文件路径
    input_file = "questionsheet.json"
    output_file = "answersheet.json"
    
    print(f"\n试卷文件: {input_file}")
    print(f"答卷文件: {output_file}")
    
    # 2. 读取试卷
    print(f"\n正在读取试卷: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
    except Exception as e:
        print(f"错误：无法读取试卷文件 - {e}")
        return
    
    # 3. 检查是否需要索引文档
    print("\n是否需要索引文档？")
    print("注意：如果是首次运行或文档有更新，请选择 'y'")
    response = input("索引文档? (y/n，默认n): ").strip().lower()
    
    agent = QAAgent()
    if response == 'y':
        print("\n开始索引文档...")
        agent.index_documents()
    
    # 4. 初始化答题卡处理器
    card_handler = AnswerCard(agent)
    
    # 5. 处理所有问题
    questions = exam_data.get("questions", [])
    total = len(questions)
    
    if total == 0:
        print("\n错误：试卷中没有问题！")
        return
    
    print(f"\n开始答题，共 {total} 道题...")
    print("="*60)
    
    answers = []
    start_time = time.time()
    
    for i, q in enumerate(questions, 1):
        question_id = q.get("question_id", f"Q{i}")
        category = q.get("category", "未知")
        query = q.get("query", "")
        
        print(f"\n[{i}/{total}] {question_id} ({category})")
        print(f"问题: {query[:50]}...")
        
        try:
            # 处理问题
            query_json = {
                "question_id": question_id,
                "query": query
            }
            answer_card = card_handler.process_query(query_json)
            
            # 添加到答案列表
            answer_entry = {
                "question_id": question_id,
                "category": category,
                "query": query,
                "result": answer_card.get("result", []),
                "answer": answer_card.get("answer", "")
            }
            answers.append(answer_entry)
            
            print(f"✓ 完成")
            
        except Exception as e:
            print(f"✗ 错误: {e}")
            # 添加错误答案
            answers.append({
                "question_id": question_id,
                "category": category,
                "query": query,
                "result": [],
                "answer": f"错误：{str(e)}"
            })
    
    # 6. 构建完整答卷
    answer_sheet = {
        "exam_info": exam_data.get("exam_info", {}),
        "answers": answers,
        "processing_info": {
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_questions": total,
            "time_used": round(time.time() - start_time, 2)
        }
    }
    
    # 7. 保存答卷
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(answer_sheet, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*60)
        print(f"✓ 答卷已保存到: {output_file}")
        print(f"总用时: {answer_sheet['processing_info']['time_used']} 秒")
        print("="*60)
        
    except Exception as e:
        print(f"\n错误：无法保存答卷 - {e}")


if __name__ == "__main__":
    main()

