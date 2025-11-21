"""
主程序：读取整个试卷JSON，生成完整答卷JSON
支持通过命令行运行单题或整卷，并可选择强制重新索引
"""
from agent import QAAgent
from json_handler import AnswerCard
import json
import time
from datetime import datetime
import argparse
import sys
import os


def main():
    """主函数：处理整个试卷"""
    print("="*60)
    print("基于难度分级的RAG问答系统")
    print("="*60)
    # 1. 解析命令行参数（支持单题运行）
    parser = argparse.ArgumentParser(description='运行答题脚本，支持单题或整卷')
    parser.add_argument('--qid', '-q', help='运行 questionsheet.json 中的单个 question_id')
    parser.add_argument('--query', '-Q', help='直接传入一个问题文本，作为单题运行')
    parser.add_argument('--index', '-i', action='store_true', help='强制重新索引文档')
    args = parser.parse_args()

    # 2. 设置输入输出文件路径
    input_file = "questionsheet.json"
    output_file = "answersheet.json"  # 合并后的答题卡
    
    print(f"\n试卷文件: {input_file}")
    print(f"答卷文件: {output_file}")
    
    # 3. 读取试卷（若提供 --query 则不一定需要 questionsheet 中的问题）
    print(f"\n正在读取试卷: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            exam_data = json.load(f)
    except Exception as e:
        print(f"错误：无法读取试卷文件 - {e}")
        # 如果用户通过 --query 直接传入问题，则可以继续
        exam_data = {"questions": []}
    
    # 4. 初始化Agent并处理索引逻辑
    agent = QAAgent()

    # 如果传入 --index，则强制重建索引
    if args.index:
        print("\n强制重新索引文档...")
        agent.index_documents(force_reindex=True)
    else:
        # 如果用户传入了单题参数（--qid或--query），跳过交互式索引提示
        if not args.qid and not args.query:
            print("\n是否需要索引文档？")
            print("注意：如果是首次运行或文档有更新，请选择 'y'")
            response = input("索引文档? (y/n，默认n): ").strip().lower()
            if response == 'y':
                print("\n开始索引文档...")
                agent.index_documents()
    
    # 5. 初始化答题卡处理器
    card_handler = AnswerCard(agent)
    
    # 5. 处理所有问题
    # 6. 根据命令行选项准备要处理的问题列表
    if args.query:
        # 直接使用传入的文本作为单题
        questions = [{
            "question_id": "SINGLE",
            "category": "未知",
            "query": args.query
        }]
    elif args.qid:
        # 从 questionsheet.json 中查找对应 question_id
        all_qs = exam_data.get("questions", [])
        matched = [q for q in all_qs if q.get('question_id') == args.qid]
        if not matched:
            print(f"错误：在 {input_file} 中未找到 question_id={args.qid}")
            sys.exit(1)
        questions = matched
    else:
        questions = exam_data.get("questions", [])

    total = len(questions)
    
    if total == 0:
        print("\n错误：没有要处理的问题！")
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
            
            # 添加到答案列表（按照示例模板格式）
            retrieved_contexts = [
                item.get("content", "") 
                for item in answer_card.get("result", [])
            ]
            
            answer_entry = {
                "question": query,
                "retrieved_contexts": retrieved_contexts,
                "answer": answer_card.get("answer", "")
            }
            answers.append(answer_entry)
            
            print(f"✓ 完成")
            
        except Exception as e:
            print(f"✗ 错误: {e}")
            # 添加错误答案（按照示例模板格式）
            answers.append({
                "question": query,
                "retrieved_contexts": [],
                "answer": f"错误：{str(e)}"
            })
    
    # 7. 构建完整答卷并保存（包含处理时间信息）
    total_time = time.time() - start_time
    
    # 确定是合并还是覆盖
    # 如果是单题运行，则尝试读取现有文件并合并
    is_partial_run = bool(args.qid or args.query)
    final_items = []
    
    if is_partial_run and os.path.exists(output_file):
        try:
            print(f"\n正在读取现有答卷以进行合并: {output_file}")
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                final_items = existing_data.get("items", [])
        except Exception as e:
            print(f"警告：无法读取现有答卷文件进行合并 - {e}")
            final_items = []
            
    # 合并逻辑
    if is_partial_run and final_items:
        # 创建映射以便快速查找和更新
        # 注意：这里使用问题文本作为键，因为answersheet.json中没有question_id
        existing_map = {item.get('question'): i for i, item in enumerate(final_items)}
        
        for new_item in answers:
            q_text = new_item.get('question')
            if q_text in existing_map:
                # 更新现有条目
                idx = existing_map[q_text]
                final_items[idx] = new_item
                print(f"已更新现有问题答案: {q_text[:30]}...")
            else:
                # 添加新条目
                final_items.append(new_item)
                print(f"已添加新问题答案: {q_text[:30]}...")
    else:
        # 如果是全量运行或没有现有文件，直接使用新答案
        final_items = answers

    answer_sheet = {
        "items": final_items
    }

    # 8. 保存答卷
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(answer_sheet, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print(f"✓ 答卷已保存到: {output_file}")
        if is_partial_run:
            print(f"本次运行耗时: {round(total_time, 2)} 秒")
        else:
            print(f"总用时: {round(total_time, 2)} 秒")
        print("="*60)

    except Exception as e:
        print(f"\n错误：无法保存答卷 - {e}")


if __name__ == "__main__":
    main()

