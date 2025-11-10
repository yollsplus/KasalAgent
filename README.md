# 基于难度分级的RAG问答系统

一个智能的文本问答Agent，根据问题难度自动选择不同的RAG（检索增强生成）策略。

## 🌟 核心特性

### 三级难度分类 RAG 架构

1. **基础题（大海捞针）- 精准检索**
   - 小块分割（512 token）
   - 向量检索 + BGE重排序
   - 快速精准定位单一答案

2. **中级题（单文档综合）- 宽泛检索 + 摘要合成**
   - 递归分块，保持文档结构
   - 同源文档多段落检索
   - 综合生成完整答案

3. **高级题（多文档综合）- 多轮检索 + Agent思维**
   - LLM分解复杂问题
   - 跨文档检索与对比
   - 深度分析与综合

## 📁 项目结构

```
KascalAgent/
├── AI_database/              # 文档数据库目录
│   ├── 标准规范/
│   ├── 技术报告/
│   ├── 事故报告/
│   └── 行业报告/
├── utils/                    # 工具模块
│   ├── document_processor.py # PDF处理和文本分块
│   ├── vector_store.py       # 向量数据库和检索
│   └── difficulty_judge.py   # 难度判断
├── rag_strategies.py         # 三种RAG策略实现
├── agent.py                  # 主Agent控制器
├── main.py                   # 使用示例
├── config.py                 # 配置管理
├── requirements.txt          # 依赖包
└── .env.example             # 环境变量模板
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 模型配置
LLM_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
RERANKER_MODEL=BAAI/bge-reranker-large
```

### 3. 运行示例

```bash
python main.py
```

## 📖 使用指南

### 交互式问答

```python
from agent import QAAgent

# 初始化Agent
agent = QAAgent()

# 首次运行需要索引文档
agent.index_documents()

# 回答问题
result = agent.answer_question(
    question_id="B001",
    question="什么是CBTC系统？"
)

print(result['answer'])
print(result['sources'])
```

### 批量问答

```python
questions = [
    ("B001", "什么是CBTC系统？"),
    ("I001", "请总结CBTC系统的主要特点。"),
    ("A001", "比较CBTC和ERTMS系统。")
]

results = agent.batch_answer(questions)
```

### 自定义难度判断规则

编辑 `utils/difficulty_judge.py` 中的 `custom_difficulty_judge` 函数：

```python
def custom_difficulty_judge(question_id: str) -> DifficultyLevel:
    """自定义难度判断逻辑"""
    
    # 示例1：根据前缀
    if question_id.startswith('BASIC_'):
        return DifficultyLevel.BASIC
    
    # 示例2：根据数字范围
    num = int(re.search(r'\d+', question_id).group())
    if num <= 50:
        return DifficultyLevel.BASIC
    elif num <= 100:
        return DifficultyLevel.INTERMEDIATE
    else:
        return DifficultyLevel.ADVANCED
```

## 🎯 RAG策略详解

### 基础题策略 (BasicRAGStrategy)

**适用场景**：需要快速找到精确答案的问题

**流程**：
1. 使用小块分割（512 token，重叠50）
2. 向量检索Top 5个最相关块
3. BGE Reranker重排序，选出Top 1
4. LLM基于最相关块生成答案
5. 强制标注来源【文件名, P页码】

**优势**：精准、快速，适合"大海捞针"场景

### 中级题策略 (IntermediateRAGStrategy)

**适用场景**：需要综合同一文档多个部分的信息

**流程**：
1. 递归分块（1024 token），保持文档结构
2. 宽泛检索Top 10
3. 按源文件分组，选择最相关文档
4. 综合多个段落生成完整答案
5. 标注所有使用的段落来源

**优势**：保持上下文，生成连贯的综合答案

### 高级题策略 (AdvancedRAGStrategy)

**适用场景**：需要跨文档对比、分析的复杂问题

**流程**：
1. LLM分解问题为2-4个子问题
2. 对每个子问题独立检索（可能来自不同文档）
3. 为每个子问题生成初步答案
4. 汇总所有信息，进行深度分析
5. 明确标注不同观点的来源

**优势**：支持复杂推理，多角度分析

## ⚙️ 配置说明

### 分块参数

```python
# 基础题
BASIC_CHUNK_SIZE=512
BASIC_CHUNK_OVERLAP=50

# 中级题
INTERMEDIATE_CHUNK_SIZE=1024
INTERMEDIATE_CHUNK_OVERLAP=100

# 高级题
ADVANCED_CHUNK_SIZE=1024
ADVANCED_CHUNK_OVERLAP=150
```

### 检索参数

```python
# 基础题：检索5个，重排序选1个
BASIC_TOP_K=5

# 中级题：检索10个，综合同源文档
INTERMEDIATE_TOP_K=10

# 高级题：检索15个，支持多文档
ADVANCED_TOP_K=15
```

## 🔧 高级功能

### 强制重新索引

```python
agent.index_documents(force_reindex=True)
```

### 指定难度等级

```python
from utils.difficulty_judge import DifficultyLevel

result = agent.answer_question(
    question_id="Q001",
    question="你的问题",
    difficulty=DifficultyLevel.ADVANCED  # 强制使用高级策略
)
```

### 元数据过滤

在高级检索中可以使用元数据过滤：

```python
# 只检索特定类别的文档
results = vector_store.search(
    query="你的问题",
    collection_type="advanced",
    top_k=10,
    filter_dict={"category": "标准规范 > 01-安全规范"}
)
```

## 📊 答案格式

所有答案都包含以下信息：

```python
{
    "answer": "答案内容...",
    "sources": ["【文件名1, P1】", "【文件名2, P5】"],
    "question_id": "B001",
    "question": "问题内容",
    "difficulty": "basic",
    "time_used": 2.5,
    "strategy": "basic",
    "retrieved_docs": [...],  # 检索到的原始文档
    
    # 高级题额外字段
    "sub_questions": [...],   # 分解的子问题
    "sub_answers": [...]      # 子问题的答案
}
```

## 🛠️ 技术栈

- **LLM**: OpenAI GPT-4
- **Embedding**: BAAI/bge-large-zh-v1.5
- **Reranker**: BAAI/bge-reranker-large
- **Vector DB**: ChromaDB
- **PDF处理**: PyMuPDF
- **框架**: LangChain

## 📝 注意事项

1. **首次运行**：需要下载embedding和reranker模型，可能需要较长时间
2. **API Key**：确保配置有效的OpenAI API Key
3. **文档格式**：目前支持PDF，系统会自动转换为文本
4. **索引时间**：大量文档首次索引可能需要较长时间
5. **来源标注**：所有答案都会强制标注来源，格式为【文件名, P页码】

## 🔍 故障排查

### 1. 找不到文档

```python
# 检查文档路径
print(config.AI_DATABASE_PATH)

# 检查索引状态
stats = agent._check_existing_index()
print(stats)
```

### 2. 模型加载失败

确保网络可以访问HuggingFace，或者手动下载模型到本地后修改路径。

### 3. API调用失败

检查 `.env` 中的 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 配置。

