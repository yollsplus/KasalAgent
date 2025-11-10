# 快速开始指南

本指南将帮助你在5分钟内启动并运行RAG问答系统。

## 步骤1：安装依赖 (2分钟)

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

## 步骤2：配置环境 (1分钟)

1. 复制环境变量模板：
```powershell
copy .env.example .env
```

2. 编辑 `.env` 文件，填入你的OpenAI API Key：
```env
OPENAI_API_KEY=sk-your-key-here
```

其他配置保持默认即可。

## 步骤3：索引文档 (根据文档数量，可能需要5-30分钟)

首次运行需要建立索引：

```python
from agent import QAAgent

# 初始化Agent
agent = QAAgent()

# 索引所有PDF文档
agent.index_documents()
```

或者运行工具脚本：

```powershell
python tools.py
# 选择选项 3 检查数据库状态
```

## 步骤4：开始问答 (立即)

### 方式1：交互式命令行

```powershell
python main.py
```

按提示输入题号和问题即可。

### 方式2：编程方式

```python
from agent import QAAgent

agent = QAAgent()

# 基础题示例
result = agent.answer_question(
    question_id="B001",
    question="什么是CBTC系统？"
)

print(result['answer'])
print(result['sources'])
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
