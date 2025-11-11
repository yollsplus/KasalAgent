"""
JSON答题卡处理模块：处理输入输出的JSON格式
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from agent import QAAgent
from utils.difficulty_judge import custom_difficulty_judge


class AnswerCard:
    """答题卡处理器"""
    
    def __init__(self, agent: Optional[QAAgent] = None):
        """
        初始化答题卡处理器
        
        Args:
            agent: QAAgent实例，如果不提供则创建新实例
        """
        self.agent = agent or QAAgent()
    
    def process_query(self, query_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个查询JSON，返回完整的答题卡
        
        Args:
            query_json: 输入的查询JSON，格式为 {"query": "问题内容"}
            
        Returns:
            完整的答题卡JSON，包含query、result和answer三部分
        """
        query = query_json.get("query", "")
        
        if not query:
            return {
                "query": "",
                "result": [],
                "answer": "错误：未提供查询内容"
            }
        
        # 使用默认题号（如果需要难度判断，可以在query_json中添加question_id字段）
        question_id = query_json.get("question_id", "Q_AUTO")
        
        # 调用Agent回答问题
        agent_result = self.agent.answer_question(question_id, query)
        
        # 转换为答题卡格式
        answer_card = self._convert_to_answer_card(query, agent_result)
        
        return answer_card
    
    def process_query_file(self, input_path: str, output_path: str):
        """
        处理查询JSON文件，生成答题卡文件
        
        Args:
            input_path: 输入JSON文件路径
            output_path: 输出JSON文件路径
        """
        # 读取输入
        with open(input_path, 'r', encoding='utf-8') as f:
            query_json = json.load(f)
        
        # 处理
        answer_card = self.process_query(query_json)
        
        # 保存输出
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(answer_card, f, ensure_ascii=False, indent=2)
        
        print(f"答题卡已保存到: {output_path}")
    
    def process_batch_queries(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量处理查询
        
        Args:
            queries: 查询列表，每个元素是 {"query": "问题内容", "question_id": "可选"}
            
        Returns:
            答题卡列表
        """
        answer_cards = []
        
        for i, query_json in enumerate(queries, 1):
            print(f"\n处理第 {i}/{len(queries)} 个问题...")
            answer_card = self.process_query(query_json)
            answer_cards.append(answer_card)
        
        return answer_cards
    
    def _convert_to_answer_card(self, query: str, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将Agent结果转换为答题卡格式
        
        Args:
            query: 原始查询
            agent_result: Agent返回的结果
            
        Returns:
            答题卡格式的JSON
        """
        # 构建召回结果列表
        result_list = []
        retrieved_docs = agent_result.get('retrieved_docs', [])
        
        for i, doc in enumerate(retrieved_docs, 1):
            result_list.append({
                "position": i,
                "content": doc.get('content', ''),
                "source": doc.get('metadata', {}).get('source', 'unknown'),
                "page": doc.get('metadata', {}).get('page', '?')
            })
        
        # 构建答题卡
        answer_card = {
            "query": query,
            "result": result_list,
            "answer": agent_result.get('answer', ''),
            "metadata": {
                "difficulty": agent_result.get('difficulty', 'unknown'),
                "strategy": agent_result.get('strategy', 'unknown'),
                "time_used": agent_result.get('time_used', 0),
                "sources": agent_result.get('sources', [])
            }
        }
        
        return answer_card
    
    def load_and_process(self, input_file: str) -> Dict[str, Any]:
        """
        加载JSON文件并处理
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            答题卡JSON
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            query_json = json.load(f)
        
        return self.process_query(query_json)
    
    def save_answer_card(self, answer_card: Dict[str, Any], output_file: str):
        """
        保存答题卡到文件
        
        Args:
            answer_card: 答题卡JSON
            output_file: 输出文件路径
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(answer_card, f, ensure_ascii=False, indent=2)
        
        print(f"答题卡已保存到: {output_file}")


def create_sample_query(output_file: str = "sample_query.json"):
    """
    创建示例查询JSON文件
    
    Args:
        output_file: 输出文件路径
    """
    sample = {
        "query": "什么是CBTC系统？",
        "question_id": "B001"  # 可选字段
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample, f, ensure_ascii=False, indent=2)
    
    print(f"示例查询已创建: {output_file}")


def main():
    """命令行使用示例"""
    import sys
    
    if len(sys.argv) < 3:
        print("用法:")
        print("  python json_handler.py input.json output.json")
        print("  python json_handler.py --create-sample [filename]")
        return
    
    if sys.argv[1] == '--create-sample':
        filename = sys.argv[2] if len(sys.argv) > 2 else "sample_query.json"
        create_sample_query(filename)
        return
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 初始化答题卡处理器
    card_handler = AnswerCard()
    
    # 处理
    card_handler.process_query_file(input_file, output_file)
    
    print("\n处理完成！")


if __name__ == "__main__":
    main()
