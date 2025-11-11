# 使用说明 - JSON答题卡模式

## 📋 JSON格式规范

### 输入格式（查询）

```json
{
  "query": "这里填写提问内容",
  "question_id": "B001"  
}
```

**字段说明**：
- `query`（必填）：要提问的内容
- `question_id`（可选）：题号，用于难度判断。如果不提供，系统会自动分配

### 输出格式（答题卡）

```json
{
  "query": "这里填写提问内容",
  "result": [
    {
      "position": 1,
      "content": "这里填写第1条召回结果的正文内容",
      "source": "文件名.txt",
      "page": 页码
    },
    {
      "position": 2,
      "content": "这里填写第2条召回结果的正文内容",
      "source": "文件名.txt",
      "page": 页码
    }
  ],
  "answer": "这里填写基于召回内容生成的回答",
  "metadata": {
    "difficulty": "basic/intermediate/advanced",
    "strategy": "使用的策略名称",
    "time_used": 2.5,
    "sources": ["【文件名, P页码】", "【文件名, P页码】"]
  }
}
```

**字段说明**：
- `query`：原始问题
- `result`：召回的文档列表
  - `position`：位置序号（从1开始）
  - `content`：文档正文内容
  - `source`：来源文件名
  - `page`：页码
- `answer`：生成的最终答案（包含来源标注）
- `metadata`：元数据信息
  - `difficulty`：难度等级
  - `strategy`：使用的RAG策略
  - `time_used`：处理耗时（秒）
  - `sources`：所有引用来源的列表

## 🚀 使用方法

### 方法1：命令行处理单个文件

```powershell
# 基本用法
python json_handler.py input.json output.json

# 示例
python json_handler.py example_query.json my_answer.json
```

### 方法2：创建示例文件

```powershell
# 创建示例查询文件
python json_handler.py --create-sample my_query.json
```

### 方法3：Python编程接口

```python
from json_handler import AnswerCard

# 初始化（会自动加载Agent）
card_handler = AnswerCard()

# 方式A：直接处理字典
query_dict = {
    "query": "什么是CBTC系统？",
    "question_id": "B001"
}
answer_card = card_handler.process_query(query_dict)

# 方式B：处理文件
card_handler.process_query_file("input.json", "output.json")

# 方式C：批量处理
queries = [
    {"query": "问题1", "question_id": "Q1"},
    {"query": "问题2", "question_id": "Q2"}
]
results = card_handler.process_batch_queries(queries)

# 保存结果
card_handler.save_answer_card(answer_card, "output.json")
```

### 方法4：集成到主程序

```powershell
python main.py
# 选择 "2. JSON答题卡模式"
```

## 📝 完整示例

### 步骤1：创建查询文件 `query.json`

```json
{
  "query": "请详细说明CBTC系统的工作原理和主要组成部分。",
  "question_id": "I001"
}
```

### 步骤2：运行处理

```powershell
python json_handler.py query.json answer.json
```

### 步骤3：查看结果 `answer.json`

```json
{
  "query": "请详细说明CBTC系统的工作原理和主要组成部分。",
  "result": [
    {
      "position": 1,
      "content": "CBTC系统主要由车载子系统、地面子系统和通信子系统三部分组成...",
      "source": "CBTC技术规范.txt",
      "page": 15
    },
    {
      "position": 2,
      "content": "车载子系统负责列车的定位、速度控制和与地面的通信...",
      "source": "CBTC技术规范.txt",
      "page": 16
    }
  ],
  "answer": "CBTC系统主要由三大子系统组成：\n\n1. 车载子系统：负责列车的精确定位、速度控制和与地面系统的实时通信...\n\n2. 地面子系统：包括区域控制器、联锁系统等，负责列车运行的监控和调度...\n\n3. 通信子系统：采用无线通信技术，实现车地之间的双向数据传输...\n\n【CBTC技术规范.txt, P15】【CBTC技术规范.txt, P16】",
  "metadata": {
    "difficulty": "intermediate",
    "strategy": "intermediate",
    "time_used": 3.2,
    "sources": [
      "【CBTC技术规范.txt, P15】",
      "【CBTC技术规范.txt, P16】"
    ]
  }
}
```

## 🎯 难度自动判断

系统会根据 `question_id` 自动判断难度：

| 题号模式 | 难度等级 | RAG策略 | 特点 |
|---------|---------|---------|------|
| B001, B-001, BASIC_001 | 基础 | 精准检索+重排序 | 快速定位单一答案 |
| I001, I-001, 100-200 | 中级 | 单文档综合 | 整合多个段落 |
| A001, A-001, >200 | 高级 | 多文档综合 | 跨文档对比分析 |

**自定义规则**：编辑 `utils/difficulty_judge.py` 中的 `custom_difficulty_judge` 函数

## 📊 输出结果说明

### result字段
- 包含所有召回的文档片段
- 按相关性排序（position从1开始）
- 每个片段都标注了来源文件和页码

### answer字段
- 基于召回内容生成的最终答案
- 答案中会标注来源：`【文件名, P页码】`
- 不同难度的答案风格不同：
  - 基础题：简洁精准
  - 中级题：综合完整
  - 高级题：多角度分析

### metadata字段
- `difficulty`：自动判断的难度等级
- `strategy`：实际使用的RAG策略
- `time_used`：处理耗时（包含检索和生成）
- `sources`：所有引用来源的汇总

## ⚠️ 注意事项

1. **文档准备**：确保 `AI_database/` 目录下有TXT文件
2. **首次使用**：需要先运行索引 `python main.py` → 选择3
3. **API配置**：需要在 `.env` 中配置 `OPENAI_API_KEY`
4. **JSON格式**：输入必须是有效的JSON格式
5. **编码格式**：文件使用UTF-8编码

## 🔧 故障排查

### 问题1：找不到文档
```
错误：未找到相关信息
解决：检查AI_database目录下是否有TXT文件，并确保已索引
```

### 问题2：JSON解析错误
```
错误：JSON解析失败
解决：检查输入JSON格式是否正确，使用在线JSON验证工具
```

### 问题3：API调用失败
```
错误：OpenAI API调用失败
解决：检查.env中的OPENAI_API_KEY是否正确
```

## 💡 最佳实践

1. **批量处理**：多个问题时使用批量接口更高效
2. **保存结果**：重要查询建议保存JSON文件备查
3. **难度指定**：如果明确知道难度，可以在query中指定question_id
4. **定期重索引**：文档更新后记得重新索引

## 📞 获取帮助

- 查看完整文档：`README.md`
- 运行示例程序：`python examples.py`
- 检查环境配置：`python setup.py`
- 查看API文档：`API.md`
