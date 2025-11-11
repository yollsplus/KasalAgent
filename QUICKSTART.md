# 快速开始指南

本指南将帮助你在5分钟内启动并运行RAG问答系统。

## 步骤1：准备文档数据

**重要**：系统读取的是TXT文件，不是PDF！

请确保 `AI_database` 目录下有TXT格式的文档文件（与PDF同名的txt文件）。

例如：
```
AI_database/
  标准规范/
    document1.txt
    document2.txt
  技术报告/
    report1.txt
```

## 步骤2：安装依赖 (2分钟)

打开PowerShell，进入项目目录：

```powershell
cd d:\mywork\KascalAgent

# 创建虚拟环境（推荐）
python -m venv venv
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

**注意**：首次安装会下载较大的模型文件（约2-3GB），请确保网络畅通。

## 步骤3：配置环境 (1分钟)

1. 复制环境变量模板：
```powershell
copy .env.example .env
```

2. 编辑 `.env` 文件，填入你的OpenAI API Key：
```env
OPENAI_API_KEY=sk-your-key-here
```

其他配置保持默认即可。

## 步骤4：索引文档 (根据文档数量，可能需要5-30分钟)

首次运行需要建立索引：

```python
from agent import QAAgent

# 初始化Agent
agent = QAAgent()

# 索引所有TXT文档
agent.index_documents()
```

或者运行主程序：

```powershell
python main.py
# 选择模式3: 文档索引管理
```

## 步骤5：开始问答 (立即)

### 方式1：JSON答题卡模式（推荐）

1. 创建查询JSON文件 `query.json`：
```json
{
  "query": "什么是CBTC系统？",
  "question_id": "B001"
}
```

2. 运行处理：
```powershell
python json_handler.py query.json answer.json
```

3. 查看结果 `answer.json`：
```json
{
  "query": "什么是CBTC系统？",
  "result": [
    {
      "position": 1,
      "content": "召回的文档内容...",
      "source": "文件名.txt",
      "page": 1
    }
  ],
  "answer": "CBTC（基于通信的列车控制）系统是...",
  "metadata": {
    "difficulty": "basic",
    "sources": ["【文件名.txt, P1】"]
  }
}
```

### 方式2：交互式命令行

```powershell
python main.py
# 选择模式1: 交互式问答
# 或选择模式2: JSON答题卡模式（图形界面）
```

### 方式3：编程方式

```python
from json_handler import AnswerCard

# 初始化
card_handler = AnswerCard()

# 处理查询
query_json = {
    "query": "什么是CBTC系统？",
    "question_id": "B001"
}

answer_card = card_handler.process_query(query_json)

print(answer_card["answer"])
print(answer_card["result"])  # 召回的文档
```

## 常见问题

### Q1: 模型下载太慢怎么办？

A: 可以设置HuggingFace镜像：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

### Q2: 如何自定义难度判断规则？

A: 编辑 `utils/difficulty_judge.py` 文件中的 `custom_difficulty_judge` 函数。

### Q3: 找不到文档怎么办？

A: 确保PDF文件在 `AI_database` 目录下，运行：

```powershell
python tools.py
# 选择选项 2 统计PDF文件
```

### Q4: 如何清空重建索引？

A: 运行：

```python
agent.index_documents(force_reindex=True)
```

## 性能优化建议

1. **使用GPU**：如果有NVIDIA GPU，安装GPU版本：
   ```powershell
   pip install faiss-gpu
   ```

2. **调整批处理大小**：编辑 `utils/vector_store.py` 中的 `batch_size`

3. **使用本地模型**：下载模型到本地后修改 `.env` 中的模型路径

## 下一步

- 阅读 [README.md](README.md) 了解详细功能
- 查看 [main.py](main.py) 学习更多使用示例
- 使用 [tools.py](tools.py) 进行数据库管理

## 需要帮助？

查看完整文档或提交Issue。
