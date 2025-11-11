"""
主Agent控制器：协调整个问答流程
"""
from typing import Dict, Any, Optional
import time
from pathlib import Path

from utils.document_processor import DocumentProcessor, TextChunker
from utils.vector_store import VectorStore
from utils.difficulty_judge import DifficultyJudge, DifficultyLevel, custom_difficulty_judge
from rag_strategies import RAGStrategyFactory
from config import config


class QAAgent:
    """问答Agent主控制器"""
    
    def __init__(self, vector_store_path: Optional[str] = None):
        """
        初始化QA Agent
        
        Args:
            vector_store_path: 向量数据库路径
        """
        print("正在初始化QA Agent...")
        
        # 初始化组件
        self.vector_store = VectorStore(vector_store_path)
        self.difficulty_judge = DifficultyJudge()
        
        print("QA Agent初始化完成！")
    
    def index_documents(self, force_reindex: bool = False):
        """
        索引AI_database中的所有文档
        
        Args:
            force_reindex: 是否强制重新索引
        """
        print("\n" + "="*50)
        print("开始文档索引流程")
        print("="*50)
        
        # 检查是否已有索引
        if not force_reindex:
            stats = self._check_existing_index()
            if stats['total_docs'] > 0:
                print(f"\n发现已有索引（共{stats['total_docs']}个文档）")
                response = input("是否要重新索引？(y/n): ")
                if response.lower() != 'y':
                    print("使用现有索引")
                    return
        
        # 清空现有索引
        print("\n清空现有索引...")
        self.vector_store.clear_all()
        
        # 处理TXT文档
        print("\n步骤1: 处理TXT文档")
        processor = DocumentProcessor(config.AI_DATABASE_PATH)
        documents = processor.process_all_txts()
        
        if not documents:
            print("警告：未找到任何文档！")
            return
        
        # 为三种难度分别分块
        print("\n步骤2: 为不同难度进行分块")
        
        print("  - 基础题分块（小块，精准检索）...")
        basic_chunks = TextChunker.chunk_for_basic(
            documents, 
            config.BASIC_CHUNK_SIZE,
            config.BASIC_CHUNK_OVERLAP
        )
        
        print("  - 中级题分块（中块，保持结构）...")
        intermediate_chunks = TextChunker.chunk_for_intermediate(
            documents,
            config.INTERMEDIATE_CHUNK_SIZE,
            config.INTERMEDIATE_CHUNK_OVERLAP
        )
        
        print("  - 高级题分块（大块，多文档）...")
        advanced_chunks = TextChunker.chunk_for_advanced(
            documents,
            config.ADVANCED_CHUNK_SIZE,
            config.ADVANCED_CHUNK_OVERLAP
        )
        
        # 添加到向量数据库
        print("\n步骤3: 建立向量索引")
        
        print(f"  - 索引基础题文档（{len(basic_chunks)}个块）...")
        self.vector_store.add_documents(basic_chunks, "basic")
        
        print(f"  - 索引中级题文档（{len(intermediate_chunks)}个块）...")
        self.vector_store.add_documents(intermediate_chunks, "intermediate")
        
        print(f"  - 索引高级题文档（{len(advanced_chunks)}个块）...")
        self.vector_store.add_documents(advanced_chunks, "advanced")
        
        # 输出统计信息
        print("\n" + "="*50)
        print("索引完成！")
        print("="*50)
        self._print_index_stats()
    
    def answer_question(self, question_id: str, question: str, 
                       difficulty: Optional[DifficultyLevel] = None) -> Dict[str, Any]:
        """
        回答问题
        
        Args:
            question_id: 题号
            question: 问题文本
            difficulty: 难度等级（如果不提供则自动判断）
            
        Returns:
            答案结果字典
        """
        start_time = time.time()
        
        print("\n" + "="*50)
        print(f"问题ID: {question_id}")
        print(f"问题: {question}")
        print("="*50)
        
        # 1. 判断难度
        if difficulty is None:
            difficulty = custom_difficulty_judge(question_id)
        
        difficulty_desc = self.difficulty_judge.get_difficulty_description(difficulty)
        print(f"\n难度判断: {difficulty_desc}")
        
        # 2. 选择对应的RAG策略
        strategy = RAGStrategyFactory.create_strategy(difficulty, self.vector_store)
        print(f"使用策略: {strategy.__class__.__name__}")
        
        # 3. 执行检索和回答
        print("\n正在检索相关文档...")
        result = strategy.retrieve_and_answer(question)
        
        # 4. 添加元信息
        result['question_id'] = question_id
        result['question'] = question
        result['difficulty'] = difficulty.value
        result['time_used'] = time.time() - start_time
        
        # 5. 输出结果
        self._print_answer(result)
        
        return result
    
    def batch_answer(self, questions: list) -> list:
        """
        批量回答问题
        
        Args:
            questions: 问题列表，每个元素是(question_id, question_text)元组
            
        Returns:
            答案列表
        """
        results = []
        
        print(f"\n开始批量问答，共{len(questions)}个问题")
        
        for i, (qid, qtext) in enumerate(questions, 1):
            print(f"\n处理第{i}/{len(questions)}个问题...")
            result = self.answer_question(qid, qtext)
            results.append(result)
        
        return results
    
    def _check_existing_index(self) -> Dict[str, int]:
        """检查现有索引"""
        stats = {
            'basic': self.vector_store.get_collection_stats('basic')['document_count'],
            'intermediate': self.vector_store.get_collection_stats('intermediate')['document_count'],
            'advanced': self.vector_store.get_collection_stats('advanced')['document_count']
        }
        stats['total_docs'] = sum(stats.values())
        return stats
    
    def _print_index_stats(self):
        """打印索引统计信息"""
        stats = self._check_existing_index()
        print(f"\n基础题索引: {stats['basic']} 个文档块")
        print(f"中级题索引: {stats['intermediate']} 个文档块")
        print(f"高级题索引: {stats['advanced']} 个文档块")
        print(f"总计: {stats['total_docs']} 个文档块")
    
    def _print_answer(self, result: Dict[str, Any]):
        """打印答案"""
        print("\n" + "="*50)
        print("回答结果")
        print("="*50)
        print(f"\n{result['answer']}")
        print(f"\n引用来源:")
        for source in result['sources']:
            print(f"  - {source}")
        print(f"\n耗时: {result['time_used']:.2f}秒")
        
        # 如果是高级题，显示子问题
        if 'sub_questions' in result and result['sub_questions']:
            print(f"\n子问题分解:")
            for i, sq in enumerate(result['sub_questions'], 1):
                print(f"  {i}. {sq}")
