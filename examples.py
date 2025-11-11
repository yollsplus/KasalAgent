"""
完整的使用示例
展示系统的各种功能
"""
import json
from pathlib import Path


def example_1_json_handler():
    """示例1：使用JSON答题卡处理器"""
    print("="*60)
    print("示例1：JSON答题卡处理")
    print("="*60)
    
    from json_handler import AnswerCard
    
    # 初始化
    card_handler = AnswerCard()
    
    # 创建查询
    query = {
        "query": "什么是CBTC系统？",
        "question_id": "B001"
    }
    
    # 处理查询
    answer_card = card_handler.process_query(query)
    
    # 显示结果
    print("\n查询:", answer_card["query"])
    print(f"\n召回了 {len(answer_card['result'])} 个文档片段:")
    for item in answer_card['result'][:3]:  # 只显示前3个
        print(f"\n位置 {item['position']}:")
        print(f"来源: {item['source']}, P{item['page']}")
        print(f"内容: {item['content'][:100]}...")
    
    print(f"\n答案:\n{answer_card['answer']}")
    print(f"\n元数据:")
    print(f"  难度: {answer_card['metadata']['difficulty']}")
    print(f"  策略: {answer_card['metadata']['strategy']}")
    print(f"  耗时: {answer_card['metadata']['time_used']:.2f}秒")


def example_2_three_difficulties():
    """示例2：三种难度的问题"""
    print("\n" + "="*60)
    print("示例2：测试三种难度")
    print("="*60)
    
    from json_handler import AnswerCard
    
    card_handler = AnswerCard()
    
    # 基础题
    print("\n[基础题] 大海捞针 - 精准检索")
    query1 = {
        "query": "CBTC系统的英文全称是什么？",
        "question_id": "B001"
    }
    answer1 = card_handler.process_query(query1)
    print(f"难度: {answer1['metadata']['difficulty']}")
    print(f"策略: {answer1['metadata']['strategy']}")
    print(f"答案: {answer1['answer'][:200]}...")
    
    # 中级题
    print("\n[中级题] 单文档综合")
    query2 = {
        "query": "请详细描述CBTC系统的组成部分和各部分的功能。",
        "question_id": "I001"
    }
    answer2 = card_handler.process_query(query2)
    print(f"难度: {answer2['metadata']['difficulty']}")
    print(f"策略: {answer2['metadata']['strategy']}")
    print(f"召回文档数: {len(answer2['result'])}")
    
    # 高级题
    print("\n[高级题] 多文档综合")
    query3 = {
        "query": "比较CBTC系统和ERTMS系统的技术特点和应用场景。",
        "question_id": "A001"
    }
    answer3 = card_handler.process_query(query3)
    print(f"难度: {answer3['metadata']['difficulty']}")
    print(f"策略: {answer3['metadata']['strategy']}")
    print(f"召回文档数: {len(answer3['result'])}")


def example_3_batch_processing():
    """示例3：批量处理"""
    print("\n" + "="*60)
    print("示例3：批量处理多个问题")
    print("="*60)
    
    from json_handler import AnswerCard
    
    card_handler = AnswerCard()
    
    # 准备多个查询
    queries = [
        {"query": "什么是CBTC？", "question_id": "Q1"},
        {"query": "CBTC的优势是什么？", "question_id": "Q2"},
        {"query": "CBTC如何实现列车定位？", "question_id": "Q3"}
    ]
    
    # 批量处理
    results = card_handler.process_batch_queries(queries)
    
    # 保存结果
    output_file = "batch_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n批量处理完成！")
    print(f"共处理 {len(results)} 个问题")
    print(f"结果已保存到: {output_file}")


def example_4_file_processing():
    """示例4：文件处理"""
    print("\n" + "="*60)
    print("示例4：从文件读取查询并保存结果")
    print("="*60)
    
    from json_handler import AnswerCard, create_sample_query
    
    # 创建示例查询文件
    query_file = "test_query.json"
    create_sample_query(query_file)
    print(f"创建了查询文件: {query_file}")
    
    # 处理文件
    card_handler = AnswerCard()
    answer_file = "test_answer.json"
    card_handler.process_query_file(query_file, answer_file)
    
    print(f"答案已保存到: {answer_file}")
    
    # 读取并显示结果
    with open(answer_file, 'r', encoding='utf-8') as f:
        answer_card = json.load(f)
    
    print(f"\n查询: {answer_card['query']}")
    print(f"答案: {answer_card['answer'][:200]}...")


def example_5_custom_difficulty():
    """示例5：自定义难度判断"""
    print("\n" + "="*60)
    print("示例5：自定义难度判断规则")
    print("="*60)
    
    from utils.difficulty_judge import DifficultyJudge, DifficultyLevel
    
    judge = DifficultyJudge()
    
    # 添加自定义规则
    judge.add_custom_rule(r'^EASY_\d+$', DifficultyLevel.BASIC)
    judge.add_custom_rule(r'^NORMAL_\d+$', DifficultyLevel.INTERMEDIATE)
    judge.add_custom_rule(r'^HARD_\d+$', DifficultyLevel.ADVANCED)
    
    # 测试
    test_ids = ["EASY_001", "NORMAL_002", "HARD_003", "B001"]
    
    for qid in test_ids:
        difficulty = judge.judge_with_custom_rules(qid)
        desc = judge.get_difficulty_description(difficulty)
        print(f"{qid} -> {desc}")


def example_6_direct_agent_usage():
    """示例6：直接使用Agent（非JSON格式）"""
    print("\n" + "="*60)
    print("示例6：直接使用QAAgent")
    print("="*60)
    
    from agent import QAAgent
    
    agent = QAAgent()
    
    # 回答问题
    result = agent.answer_question(
        question_id="B001",
        question="CBTC系统的主要优势是什么？"
    )
    
    print(f"\n问题: {result['question']}")
    print(f"难度: {result['difficulty']}")
    print(f"\n答案:\n{result['answer']}")
    print(f"\n来源:")
    for source in result['sources']:
        print(f"  {source}")


def main():
    """主函数"""
    print("RAG问答系统 - 完整示例")
    print("="*60)
    print()
    print("注意：运行这些示例前，请确保：")
    print("1. 已经安装所有依赖")
    print("2. 已经配置.env文件")
    print("3. 已经索引了文档")
    print("4. AI_database目录下有TXT文件")
    print()
    
    examples = [
        ("JSON答题卡处理", example_1_json_handler),
        ("三种难度测试", example_2_three_difficulties),
        ("批量处理", example_3_batch_processing),
        ("文件处理", example_4_file_processing),
        ("自定义难度规则", example_5_custom_difficulty),
        ("直接使用Agent", example_6_direct_agent_usage)
    ]
    
    while True:
        print("\n" + "="*60)
        print("请选择要运行的示例：")
        for i, (name, _) in enumerate(examples, 1):
            print(f"{i}. {name}")
        print("0. 退出")
        print("="*60)
        
        choice = input("\n请选择 (0-6): ").strip()
        
        if choice == '0':
            break
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, func = examples[idx]
                print(f"\n运行示例: {name}")
                func()
            else:
                print("无效选择！")
        except ValueError:
            print("请输入数字！")
        except Exception as e:
            print(f"\n运行示例时出错: {e}")
            import traceback
            traceback.print_exc()
        
        input("\n按回车继续...")
    
    print("\n示例程序结束！")


if __name__ == "__main__":
    main()
