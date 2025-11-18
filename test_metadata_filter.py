"""
测试元数据过滤功能
"""
from agent import QAAgent
import json


def test_b002():
    """测试问题B002"""
    print("="*60)
    print("测试问题 B002 - 元数据过滤功能")
    print("="*60)
    
    question = "根据欧洲铁路局 2025-2027 年单一规划文件，机构注册系统迁移到知识图谱（knowledge graph）方法的目标进度在 2025 年底应达到多少百分比？"
    
    print(f"\n问题: {question}")
    print("\n注意：测试前需要重新索引文档以包含新的元数据字段")
    print("      运行: python main.py 并选择 'y' 索引文档")
    
    # 初始化agent（假设已经索引过）
    try:
        agent = QAAgent()
        
        # 处理问题
        result = agent.answer_question(
            question_id="B002",
            question=question
        )
        
        print("\n" + "="*60)
        print("检索结果")
        print("="*60)
        
        for i, doc in enumerate(result.get('retrieved_docs', []), 1):
            metadata = doc['metadata']
            source = metadata.get('source', '未知')
            year_range = metadata.get('year_range_text', '无')
            keywords = metadata.get('keywords', [])
            
            print(f"\n{i}. 【{source}】")
            print(f"   年份范围: {year_range}")
            print(f"   关键词: {keywords}")
            print(f"   内容预览: {doc['content'][:100]}...")
        
        print("\n" + "="*60)
        print("回答")
        print("="*60)
        print(result.get('answer', ''))
        
        print("\n" + "="*60)
        print("来源")
        print("="*60)
        for source in result.get('sources', []):
            print(f"  {source}")
        
    except Exception as e:
        print(f"\n错误: {e}")
        print("\n可能原因：")
        print("1. 向量库未包含新的元数据字段")
        print("2. 解决方法：运行 python main.py，选择 'y' 重新索引文档")


if __name__ == "__main__":
    test_b002()
