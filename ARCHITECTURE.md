# 项目架构文档

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户接口层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ main.py  │  │ tools.py │  │ setup.py │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Agent控制层                             │
│                   ┌──────────────┐                          │
│                   │   agent.py   │                          │
│                   │   QAAgent    │                          │
│                   └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      策略层                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             rag_strategies.py                         │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │  │
│  │  │  Basic   │ │Intermediate││ Advanced │            │  │
│  │  │ Strategy │ │  Strategy  ││ Strategy │            │  │
│  │  └──────────┘ └──────────┘ └──────────┘            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      工具层                                  │
│  ┌────────────────┐  ┌────────────────┐                   │
│  │document_       │  │ vector_store   │                   │
│  │processor.py    │  │     .py        │                   │
│  │                │  │                │                   │
│  │- PDF转文本     │  │- Embedding     │                   │
│  │- 文本分块      │  │- ChromaDB      │                   │
│  │- 元数据提取    │  │- 检索          │                   │
│  └────────────────┘  │- Reranking     │                   │
│                      └────────────────┘                   │
│  ┌────────────────┐                                       │
│  │difficulty_     │                                       │
│  │judge.py        │                                       │
│  │                │                                       │
│  │- 难度判断      │                                       │
│  │- 自定义规则    │                                       │
│  └────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
│  ┌──────────────┐  ┌──────────────┐                       │
│  │ AI_database/ │  │ vector_db/   │                       │
│  │              │  │              │                       │
│  │ - PDF文档    │  │ - ChromaDB   │                       │
│  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      外部服务                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │ OpenAI   │  │  BGE     │  │   BGE    │                │
│  │   LLM    │  │Embedding │  │ Reranker │                │
│  └──────────┘  └──────────┘  └──────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## 数据流

### 1. 文档索引流程

```
PDF文档 
  ↓
DocumentProcessor.process_all_pdfs()
  ↓
提取文本 + 元数据（文件名、页码、分类）
  ↓
TextChunker (三种分块策略)
  ├─ Basic: 512 token, overlap 50
  ├─ Intermediate: 1024 token, overlap 100
  └─ Advanced: 1024 token, overlap 150
  ↓
EmbeddingModel.embed_documents()
  ↓
VectorStore.add_documents()
  ├─ basic_collection
  ├─ intermediate_collection
  └─ advanced_collection
  ↓
ChromaDB持久化存储
```

### 2. 问答流程

```
用户问题 (question_id + question)
  ↓
DifficultyJudge.judge_difficulty()
  ↓
选择难度等级 (Basic/Intermediate/Advanced)
  ↓
RAGStrategyFactory.create_strategy()
  ↓
执行对应策略
  ↓
┌──────────────┬──────────────┬──────────────┐
│  Basic       │ Intermediate │  Advanced    │
│  Strategy    │  Strategy    │  Strategy    │
├──────────────┼──────────────┼──────────────┤
│1. 向量检索   │1. 宽泛检索   │1. 分解问题   │
│   Top 5      │   Top 10     │   (LLM)      │
│              │              │              │
│2. Reranker   │2. 按源分组   │2. 多轮检索   │
│   选Top 1    │   选主文档   │   (子问题)   │
│              │              │              │
│3. LLM生成    │3. 综合生成   │3. 子答案生成 │
│   答案       │   答案       │              │
│              │              │4. 最终综合   │
└──────────────┴──────────────┴──────────────┘
  ↓
格式化答案 + 来源标注
  ↓
返回结果
```

## 核心组件说明

### 1. QAAgent (agent.py)

**职责**：主控制器，协调整个问答流程

**关键方法**：
- `index_documents()`: 索引所有PDF文档
- `answer_question()`: 回答单个问题
- `batch_answer()`: 批量回答

### 2. RAG策略 (rag_strategies.py)

#### BasicRAGStrategy
- **场景**: 精确查找单一答案
- **特点**: 小块 + 重排序
- **适用**: "什么是X"、"定义Y"

#### IntermediateRAGStrategy
- **场景**: 综合同一文档多个部分
- **特点**: 递归分块 + 同源检索
- **适用**: "描述X的特点"、"总结Y"

#### AdvancedRAGStrategy
- **场景**: 跨文档对比分析
- **特点**: 问题分解 + 多轮检索
- **适用**: "比较X和Y"、"分析Z的差异"

### 3. 文档处理 (document_processor.py)

**DocumentProcessor**:
- PDF文本提取（PyMuPDF）
- 元数据提取（文件名、页码、分类）
- 文本清洗

**TextChunker**:
- 三种分块策略
- 滑动窗口分割
- 章节结构识别

### 4. 向量存储 (vector_store.py)

**VectorStore**:
- ChromaDB管理
- 三个独立集合
- 向量检索
- 元数据过滤

**EmbeddingModel**:
- BGE嵌入模型
- 批量处理

**Reranker**:
- BGE重排序
- 精准选择

### 5. 难度判断 (difficulty_judge.py)

**DifficultyJudge**:
- 基于题号的规则判断
- 可自定义规则
- 支持正则匹配

## 关键配置参数

### 分块参数

| 难度 | Chunk Size | Overlap | 说明 |
|------|-----------|---------|------|
| Basic | 512 | 50 | 小块，精准定位 |
| Intermediate | 1024 | 100 | 中块，保持上下文 |
| Advanced | 1024 | 150 | 大块，支持多文档 |

### 检索参数

| 难度 | Top K | Rerank | 说明 |
|------|-------|--------|------|
| Basic | 5 | 是(→1) | 精准检索 |
| Intermediate | 10 | 否 | 宽泛检索 |
| Advanced | 15 | 否 | 多文档检索 |

## 性能优化

### 1. 索引优化
- 批量处理（batch_size=100）
- 并行嵌入
- 增量索引

### 2. 检索优化
- 向量索引（HNSW）
- 元数据过滤
- 缓存机制

### 3. 生成优化
- 温度参数调整
- Prompt优化
- 流式输出

## 扩展点

### 1. 新增RAG策略
```python
class CustomRAGStrategy(RAGStrategy):
    def retrieve_and_answer(self, question: str):
        # 实现自定义逻辑
        pass
```

### 2. 自定义分块
```python
class CustomChunker:
    @staticmethod
    def chunk_custom(documents):
        # 实现自定义分块
        pass
```

### 3. 新增模型
```python
# 替换嵌入模型
config.EMBEDDING_MODEL = "your-model"

# 替换LLM
config.LLM_MODEL = "your-llm"
```

## 错误处理

### 1. 检索失败
```python
if not search_results:
    return {
        "answer": "未找到相关信息",
        "sources": [],
        "retrieved_docs": []
    }
```

### 2. LLM调用失败
```python
try:
    response = self._call_llm(prompt)
except Exception as e:
    return f"生成答案时出错: {e}"
```

### 3. 文档处理失败
```python
try:
    doc = pymupdf.open(pdf_path)
except Exception as e:
    print(f"处理PDF失败: {e}")
    continue
```

## 日志和监控

### 关键指标
- 索引文档数量
- 检索耗时
- 生成耗时
- 引用准确性

### 日志级别
- INFO: 正常流程
- WARNING: 可能的问题
- ERROR: 错误情况

## 安全性

### 1. API Key保护
- 使用环境变量
- 不提交到版本控制

### 2. 输入验证
- 问题长度限制
- 特殊字符过滤

### 3. 输出过滤
- 敏感信息检测
- 来源验证
