"""
示例脚本：演示如何使用QA Agent
"""
from agent import QAAgent
from utils.difficulty_judge import DifficultyLevel
from config import config


def main():
    """主函数"""
    print("="*60)
    print("欢迎使用基于难度分级的RAG问答系统")
    print("="*60)
    
    # 1. 初始化Agent
    agent = QAAgent()
    
    # 2. 索引文档（首次运行需要）
    print("\n是否需要索引文档？")
    print("注意：如果是首次运行或文档有更新，请选择 'y'")
    response = input("索引文档? (y/n): ")
    
    if response.lower() == 'y':
        agent.index_documents()
    
    # 3. 交互式问答
    print("\n" + "="*60)
    print("开始问答（输入 'quit' 退出）")
    print("="*60)
    
    while True:
        print("\n" + "-"*60)
        question_id = input("请输入题号（如 B001, I001, A001）: ").strip()
        
        if question_id.lower() == 'quit':
            break
        
        question = input("请输入问题: ").strip()
        
        if not question:
            print("问题不能为空！")
            continue
        
        # 回答问题
        result = agent.answer_question(question_id, question)
        
        # 可选：保存结果
        save = input("\n是否保存结果到文件？(y/n): ").strip()
        if save.lower() == 'y':
            save_result(result)
    
    print("\n谢谢使用！")


def save_result(result: dict):
    """保存结果到文件"""
    import json
    from datetime import datetime
    
    filename = f"result_{result['question_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到: {filename}")


def demo_batch():
    """演示批量问答"""
    agent = QAAgent()
    
    # 示例问题列表
    questions = [
        ("B001", "什么是CBTC系统？"),
        ("I001", "请总结CBTC系统的主要特点和优势。"),
        ("A001", "比较CBTC系统和ERTMS系统的异同点。")
    ]
    
    results = agent.batch_answer(questions)
    
    # 保存批量结果
    import json
    from datetime import datetime
    
    filename = f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n批量结果已保存到: {filename}")


def demo_single_question():
    """演示单个问题"""
    agent = QAAgent()
    
    # 基础题示例
    print("\n" + "="*60)
    print("示例1: 基础题（精准检索）")
    print("="*60)
    result1 = agent.answer_question(
        question_id="B001",
        question="CBTC系统的定义是什么？"
    )
    
    # 中级题示例
    print("\n" + "="*60)
    print("示例2: 中级题（单文档综合）")
    print("="*60)
    result2 = agent.answer_question(
        question_id="I001",
        question="请详细描述CBTC系统的组成部分和工作原理。"
    )
    
    # 高级题示例
    print("\n" + "="*60)
    print("示例3: 高级题（多文档综合）")
    print("="*60)
    result3 = agent.answer_question(
        question_id="A001",
        question="比较不同国家的列车控制系统标准，分析它们的优缺点。"
    )


if __name__ == "__main__":
    # 运行交互式问答
    main()
    
    # 或者运行演示
    # demo_single_question()
    # demo_batch()
