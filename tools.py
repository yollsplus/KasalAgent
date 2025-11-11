"""
工具脚本：用于数据库管理和测试
"""
import json
from pathlib import Path
from agent import QAAgent
from config import config


def check_database_structure():
    """检查AI_database的目录结构"""
    print("AI_database 目录结构：\n")
    
    def print_tree(directory, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir():
                    extension_prefix = "    " if is_last else "│   "
                    print_tree(item, prefix + extension_prefix, max_depth, current_depth + 1)
        except PermissionError:
            pass
    
    db_path = Path(config.AI_DATABASE_PATH)
    if db_path.exists():
        print(f"{db_path.name}/")
        print_tree(db_path, max_depth=4)
    else:
        print(f"错误：目录不存在 - {db_path}")


def count_txt_files():
    """统计TXT文件数量"""
    db_path = Path(config.AI_DATABASE_PATH)
    txt_files = list(db_path.rglob("*.txt"))
    
    print(f"\nTXT文件统计：")
    print(f"总数：{len(txt_files)}")
    
    # 按目录分类统计
    by_category = {}
    for txt in txt_files:
        parts = txt.parts
        try:
            db_index = parts.index("AI_database")
            if db_index + 1 < len(parts):
                category = parts[db_index + 1]
                by_category[category] = by_category.get(category, 0) + 1
        except ValueError:
            pass
    
    print("\n按类别统计：")
    for category, count in sorted(by_category.items()):
        print(f"  {category}: {count} 个文件")


def check_vector_db():
    """检查向量数据库状态"""
    print("\n向量数据库状态：\n")
    
    agent = QAAgent()
    
    for collection_type in ['basic', 'intermediate', 'advanced']:
        stats = agent.vector_store.get_collection_stats(collection_type)
        print(f"{collection_type.capitalize()} 集合: {stats['document_count']} 个文档块")


def export_sample_documents(n=5):
    """导出样本文档用于检查"""
    from utils.document_processor import DocumentProcessor
    
    processor = DocumentProcessor(config.AI_DATABASE_PATH)
    txt_files = list(config.AI_DATABASE_PATH.rglob("*.txt"))[:n]
    
    print(f"\n导出前{n}个TXT的样本内容：\n")
    
    for txt_file in txt_files:
        print(f"\n{'='*60}")
        print(f"文件：{txt_file.name}")
        print('='*60)
        
        documents = processor.txt_to_documents(txt_file)
        
        if documents:
            # 只显示前500字符
            sample = documents[0].content[:500]
            print(f"\n内容样本：\n{sample}...")
            print(f"\n元数据：{json.dumps(documents[0].metadata, ensure_ascii=False, indent=2)}")
        else:
            print("无法读取文本")


def test_retrieval(query: str):
    """测试检索功能"""
    print(f"\n测试检索：{query}\n")
    
    agent = QAAgent()
    
    for collection_type in ['basic', 'intermediate', 'advanced']:
        print(f"\n{'='*60}")
        print(f"{collection_type.capitalize()} 集合检索结果")
        print('='*60)
        
        results = agent.vector_store.search(
            query=query,
            collection_type=collection_type,
            top_k=3
        )
        
        for i, result in enumerate(results, 1):
            print(f"\n结果 {i}:")
            print(f"来源: {result['metadata'].get('source', 'unknown')}")
            print(f"页码: P{result['metadata'].get('page', '?')}")
            print(f"内容: {result['content'][:200]}...")
            print(f"距离: {result.get('distance', 'N/A')}")


def clear_vector_db():
    """清空向量数据库"""
    response = input("确定要清空向量数据库吗？(yes/no): ")
    if response.lower() == 'yes':
        agent = QAAgent()
        agent.vector_store.clear_all()
        print("向量数据库已清空")
    else:
        print("操作已取消")


def benchmark_strategies():
    """测试三种策略的性能"""
    agent = QAAgent()
    
    test_questions = [
        ("B001", "什么是CBTC？", "basic"),
        ("I001", "描述CBTC系统的组成和功能。", "intermediate"),
        ("A001", "比较CBTC和ERTMS的技术特点。", "advanced")
    ]
    
    results = []
    
    for qid, question, expected_difficulty in test_questions:
        print(f"\n{'='*60}")
        print(f"测试问题 {qid}: {question}")
        print('='*60)
        
        result = agent.answer_question(qid, question)
        results.append({
            'question_id': qid,
            'question': question,
            'expected_difficulty': expected_difficulty,
            'actual_difficulty': result['difficulty'],
            'time_used': result['time_used'],
            'sources_count': len(result['sources'])
        })
    
    # 输出性能报告
    print("\n" + "="*60)
    print("性能测试报告")
    print("="*60)
    
    for r in results:
        print(f"\n{r['question_id']}:")
        print(f"  预期难度: {r['expected_difficulty']}")
        print(f"  实际难度: {r['actual_difficulty']}")
        print(f"  耗时: {r['time_used']:.2f}秒")
        print(f"  引用来源: {r['sources_count']}个")


def main():
    """主菜单"""
    while True:
        print("\n" + "="*60)
        print("数据库管理工具")
        print("="*60)
        print("1. 查看目录结构")
        print("2. 统计TXT文件")
        print("3. 检查向量数据库")
        print("4. 导出样本文档")
        print("5. 测试检索功能")
        print("6. 清空向量数据库")
        print("7. 策略性能测试")
        print("0. 退出")
        print("="*60)
        
        choice = input("\n请选择操作: ").strip()
        
        if choice == '1':
            check_database_structure()
        elif choice == '2':
            count_txt_files()
        elif choice == '3':
            check_vector_db()
        elif choice == '4':
            n = input("导出多少个样本？(默认5): ").strip()
            n = int(n) if n.isdigit() else 5
            export_sample_documents(n)
        elif choice == '5':
            query = input("输入测试查询: ").strip()
            if query:
                test_retrieval(query)
        elif choice == '6':
            clear_vector_db()
        elif choice == '7':
            benchmark_strategies()
        elif choice == '0':
            break
        else:
            print("无效选择！")
    
    print("\n再见！")


if __name__ == "__main__":
    main()
