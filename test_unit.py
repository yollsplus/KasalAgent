"""
单元测试示例
"""
import unittest
from pathlib import Path
from utils.difficulty_judge import DifficultyJudge, DifficultyLevel
from utils.document_processor import Document, TextChunker


class TestDifficultyJudge(unittest.TestCase):
    """测试难度判断模块"""
    
    def setUp(self):
        self.judge = DifficultyJudge()
    
    def test_basic_questions(self):
        """测试基础题判断"""
        test_cases = [
            "B001",
            "BASIC_001",
            "B-001"
        ]
        for qid in test_cases:
            difficulty = self.judge.judge_difficulty(qid)
            self.assertEqual(difficulty, DifficultyLevel.BASIC)
    
    def test_intermediate_questions(self):
        """测试中级题判断"""
        test_cases = [
            "I001",
            "150"  # 数字范围100-200
        ]
        for qid in test_cases:
            difficulty = self.judge.judge_difficulty(qid)
            self.assertEqual(difficulty, DifficultyLevel.INTERMEDIATE)
    
    def test_advanced_questions(self):
        """测试高级题判断"""
        test_cases = [
            "A001",
            "250"  # 数字大于200
        ]
        for qid in test_cases:
            difficulty = self.judge.judge_difficulty(qid)
            self.assertEqual(difficulty, DifficultyLevel.ADVANCED)


class TestTextChunker(unittest.TestCase):
    """测试文本分块模块"""
    
    def setUp(self):
        self.sample_doc = Document(
            content="这是一段测试文本。" * 100,  # 重复100次
            metadata={"source": "test.pdf", "page": 1}
        )
    
    def test_basic_chunking(self):
        """测试基础分块"""
        chunks = TextChunker.chunk_for_basic(
            [self.sample_doc],
            chunk_size=100,
            overlap=10
        )
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].metadata['chunk_type'], 'basic')
    
    def test_chunk_overlap(self):
        """测试重叠是否正确"""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        doc = Document(content=text, metadata={})
        
        chunks = TextChunker.chunk_for_basic([doc], chunk_size=10, overlap=2)
        
        # 检查重叠
        if len(chunks) > 1:
            self.assertIn(chunks[0].content[-2:], chunks[1].content[:2])
    
    def test_metadata_preservation(self):
        """测试元数据是否保留"""
        chunks = TextChunker.chunk_for_basic([self.sample_doc])
        
        for chunk in chunks:
            self.assertEqual(chunk.metadata['source'], 'test.pdf')
            self.assertEqual(chunk.metadata['page'], 1)


class TestDocumentProcessor(unittest.TestCase):
    """测试文档处理模块"""
    
    def test_clean_text(self):
        """测试文本清洗"""
        from utils.document_processor import DocumentProcessor
        
        processor = DocumentProcessor(Path("."))
        
        # 测试多余空白
        text = "这是  一段   有很多    空白的文本"
        cleaned = processor._clean_text(text)
        self.assertNotIn("  ", cleaned)
        
        # 测试特殊字符
        text = "正常文本\x00\x01\x02"
        cleaned = processor._clean_text(text)
        self.assertEqual(cleaned, "正常文本")
    
    def test_category_extraction(self):
        """测试分类提取"""
        from utils.document_processor import DocumentProcessor
        
        processor = DocumentProcessor(Path("AI_database"))
        
        test_path = Path("AI_database/标准规范/01-安全规范/test.pdf")
        category = processor._extract_category(test_path)
        
        self.assertIn("标准规范", category)
        self.assertIn("01-安全规范", category)


def run_tests():
    """运行所有测试"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
