# API参考文档

本文档详细说明了系统各个模块的API接口。

## QAAgent

主控制器类，协调整个问答流程。

### 初始化

```python
QAAgent(vector_store_path: Optional[str] = None)
```

**参数**:
- `vector_store_path`: 向量数据库路径，默认使用配置文件中的路径

**示例**:
```python
agent = QAAgent()
# 或指定自定义路径
agent = QAAgent(vector_store_path="./my_vector_db")
```

### index_documents

索引AI_database中的所有文档。

```python
index_documents(force_reindex: bool = False) -> None
```

**参数**:
- `force_reindex`: 是否强制重新索引，默认False

**示例**:
```python
# 首次索引或增量索引
agent.index_documents()

# 强制重建索引
agent.index_documents(force_reindex=True)
```

### answer_question

回答单个问题。

```python
answer_question(
    question_id: str,
    question: str,
    difficulty: Optional[DifficultyLevel] = None
) -> Dict[str, Any]
```

**参数**:
- `question_id`: 题号
- `question`: 问题文本
- `difficulty`: 可选，手动指定难度等级

**返回值**:
```python
{
    "answer": str,              # 答案文本
    "sources": List[str],       # 来源列表
    "question_id": str,         # 题号
    "question": str,            # 问题
    "difficulty": str,          # 难度等级
    "time_used": float,         # 耗时（秒）
    "strategy": str,            # 使用的策略
    "retrieved_docs": List[Dict], # 检索到的文档
    
    # 高级题额外字段
    "sub_questions": List[str],     # 子问题列表（仅高级题）
    "sub_answers": List[Dict]       # 子答案列表（仅高级题）
}
```

**示例**:
```python
# 自动判断难度
result = agent.answer_question("B001", "什么是CBTC？")

# 手动指定难度
from utils.difficulty_judge import DifficultyLevel
result = agent.answer_question(
    "Q001", 
    "你的问题", 
    difficulty=DifficultyLevel.ADVANCED
)

print(result['answer'])
print(result['sources'])
```

### batch_answer

批量回答问题。

```python
batch_answer(questions: List[Tuple[str, str]]) -> List[Dict[str, Any]]
```

**参数**:
- `questions`: 问题列表，每个元素是(question_id, question_text)元组

**返回值**: 答案列表，每个元素与`answer_question`返回值相同

**示例**:
```python
questions = [
    ("B001", "什么是CBTC？"),
    ("I001", "描述CBTC的特点。"),
    ("A001", "比较CBTC和ERTMS。")
]

results = agent.batch_answer(questions)

for result in results:
    print(f"{result['question_id']}: {result['answer']}")
```

---

## DifficultyJudge

难度判断器。

### judge_difficulty

根据题号判断难度。

```python
judge_difficulty(question_id: str) -> DifficultyLevel
```

**参数**:
- `question_id`: 题号

**返回值**: `DifficultyLevel` 枚举值

**示例**:
```python
from utils.difficulty_judge import DifficultyJudge

judge = DifficultyJudge()
difficulty = judge.judge_difficulty("B001")
print(difficulty)  # DifficultyLevel.BASIC
```

### add_custom_rule

添加自定义判断规则。

```python
add_custom_rule(pattern: str, difficulty: DifficultyLevel) -> None
```

**参数**:
- `pattern`: 正则表达式模式
- `difficulty`: 对应的难度等级

**示例**:
```python
judge.add_custom_rule(r'^EASY_\d+$', DifficultyLevel.BASIC)
judge.add_custom_rule(r'^HARD_\d+$', DifficultyLevel.ADVANCED)
```

### custom_difficulty_judge

用户自定义判断函数（需要修改源码）。

```python
custom_difficulty_judge(question_id: str) -> DifficultyLevel
```

**在源码中修改**:
```python
# utils/difficulty_judge.py

def custom_difficulty_judge(question_id: str) -> DifficultyLevel:
    # 你的自定义逻辑
    if question_id.startswith('SIMPLE_'):
        return DifficultyLevel.BASIC
    # ...
```

---

## VectorStore

向量数据库管理。

### search

搜索相关文档。

```python
search(
    query: str,
    collection_type: str = "basic",
    top_k: int = 5,
    filter_dict: Optional[Dict] = None
) -> List[Dict[str, Any]]
```

**参数**:
- `query`: 查询文本
- `collection_type`: 集合类型，"basic"/"intermediate"/"advanced"
- `top_k`: 返回前k个结果
- `filter_dict`: 元数据过滤条件

**返回值**:
```python
[
    {
        "content": str,      # 文档内容
        "metadata": Dict,    # 元数据
        "distance": float    # 距离分数
    },
    ...
]
```

**示例**:
```python
from utils.vector_store import VectorStore

vs = VectorStore()

# 基本搜索
results = vs.search("CBTC是什么", collection_type="basic", top_k=5)

# 带过滤的搜索
results = vs.search(
    "CBTC",
    collection_type="advanced",
    top_k=10,
    filter_dict={"category": "标准规范"}
)

for result in results:
    print(result['metadata']['source'])
    print(result['content'][:100])
```

### add_documents

添加文档到向量数据库。

```python
add_documents(
    documents: List[Document],
    collection_type: str = "basic"
) -> None
```

**参数**:
- `documents`: 文档列表
- `collection_type`: 目标集合

**示例**:
```python
from utils.document_processor import Document

docs = [
    Document(
        content="文档内容",
        metadata={"source": "test.pdf", "page": 1}
    )
]

vs.add_documents(docs, collection_type="basic")
```

### get_collection_stats

获取集合统计信息。

```python
get_collection_stats(collection_type: str) -> Dict[str, Any]
```

**返回值**:
```python
{
    "collection_type": str,
    "document_count": int
}
```

**示例**:
```python
stats = vs.get_collection_stats("basic")
print(f"基础题集合有 {stats['document_count']} 个文档块")
```

---

## DocumentProcessor

文档处理器。

### pdf_to_text

将PDF转换为文本。

```python
pdf_to_text(pdf_path: Path) -> List[Document]
```

**参数**:
- `pdf_path`: PDF文件路径

**返回值**: 文档列表，每个文档对应一页

**示例**:
```python
from utils.document_processor import DocumentProcessor
from pathlib import Path

processor = DocumentProcessor(Path("AI_database"))
documents = processor.pdf_to_text(Path("test.pdf"))

for doc in documents:
    print(f"Page {doc.page_number}: {doc.content[:100]}")
```

### process_all_pdfs

处理所有PDF文件。

```python
process_all_pdfs() -> List[Document]
```

**返回值**: 所有文档的列表

**示例**:
```python
processor = DocumentProcessor(Path("AI_database"))
all_docs = processor.process_all_pdfs()
print(f"共处理 {len(all_docs)} 个文档页面")
```

---

## TextChunker

文本分块器。

### chunk_for_basic

为基础题分块。

```python
@staticmethod
chunk_for_basic(
    documents: List[Document],
    chunk_size: int = 512,
    overlap: int = 50
) -> List[Document]
```

### chunk_for_intermediate

为中级题分块。

```python
@staticmethod
chunk_for_intermediate(
    documents: List[Document],
    chunk_size: int = 1024,
    overlap: int = 100
) -> List[Document]
```

### chunk_for_advanced

为高级题分块。

```python
@staticmethod
chunk_for_advanced(
    documents: List[Document],
    chunk_size: int = 1024,
    overlap: int = 150
) -> List[Document]
```

**示例**:
```python
from utils.document_processor import TextChunker

# 基础题分块
basic_chunks = TextChunker.chunk_for_basic(
    documents,
    chunk_size=512,
    overlap=50
)

# 中级题分块
intermediate_chunks = TextChunker.chunk_for_intermediate(
    documents,
    chunk_size=1024,
    overlap=100
)
```

---

## RAGStrategy

RAG策略基类。

### BasicRAGStrategy

基础题策略。

```python
BasicRAGStrategy(vector_store: VectorStore)
```

**方法**:
- `retrieve_and_answer(question: str) -> Dict[str, Any]`

### IntermediateRAGStrategy

中级题策略。

```python
IntermediateRAGStrategy(vector_store: VectorStore)
```

### AdvancedRAGStrategy

高级题策略。

```python
AdvancedRAGStrategy(vector_store: VectorStore)
```

**示例**:
```python
from rag_strategies import BasicRAGStrategy, RAGStrategyFactory
from utils.difficulty_judge import DifficultyLevel

# 直接使用策略
strategy = BasicRAGStrategy(vector_store)
result = strategy.retrieve_and_answer("什么是CBTC？")

# 使用工厂模式
strategy = RAGStrategyFactory.create_strategy(
    DifficultyLevel.BASIC,
    vector_store
)
result = strategy.retrieve_and_answer("什么是CBTC？")
```

---

## Config

配置类。

### 主要配置项

```python
from config import config

# 路径配置
config.AI_DATABASE_PATH      # AI_database路径
config.VECTOR_DB_PATH         # 向量数据库路径

# API配置
config.OPENAI_API_KEY         # OpenAI API Key
config.OPENAI_BASE_URL        # API Base URL
config.LLM_MODEL              # LLM模型名称

# 模型配置
config.EMBEDDING_MODEL        # 嵌入模型
config.RERANKER_MODEL         # 重排序模型

# 分块配置
config.BASIC_CHUNK_SIZE       # 基础题块大小
config.INTERMEDIATE_CHUNK_SIZE # 中级题块大小
config.ADVANCED_CHUNK_SIZE    # 高级题块大小

# 检索配置
config.BASIC_TOP_K            # 基础题Top K
config.INTERMEDIATE_TOP_K     # 中级题Top K
config.ADVANCED_TOP_K         # 高级题Top K
```

### 验证配置

```python
config.validate()  # 验证配置是否完整
```

---

## 数据结构

### Document

文档数据类。

```python
@dataclass
class Document:
    content: str                    # 文档内容
    metadata: Dict[str, Any]        # 元数据
    page_number: Optional[int] = None  # 页码
```

**元数据字段**:
- `source`: 文件名
- `file_path`: 完整路径
- `page`: 页码
- `category`: 分类
- `chunk_id`: 块ID
- `chunk_type`: 块类型
- `total_chunks`: 总块数

### DifficultyLevel

难度等级枚举。

```python
class DifficultyLevel(Enum):
    BASIC = "basic"           # 基础题
    INTERMEDIATE = "intermediate"  # 中级题
    ADVANCED = "advanced"      # 高级题
```

---

## 错误处理

所有主要函数都有错误处理，会返回有意义的错误消息。

### 常见错误

**配置错误**:
```python
ValueError: 请在.env文件中配置OPENAI_API_KEY
```

**文档不存在**:
```python
ValueError: AI_database目录不存在
```

**检索失败**:
```python
{
    "answer": "未找到相关信息",
    "sources": [],
    "retrieved_docs": []
}
```

---

## 类型提示

所有函数都包含完整的类型提示，可以使用IDE的智能提示功能。

```python
from typing import List, Dict, Any, Optional
from pathlib import Path

def my_function(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    pass
```
