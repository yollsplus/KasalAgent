"""
RAG策略模块：实现三种不同难度的检索策略
"""
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import re
import openai
from openai import OpenAI

from utils.vector_store import VectorStore, Reranker
from utils.difficulty_judge import DifficultyLevel
from config import config


class RAGStrategy(ABC):
    """RAG策略基类"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL
        )
        
    @abstractmethod
    def retrieve_and_answer(self, question: str) -> Dict[str, Any]:
        """检索并回答问题"""
        pass
    
    def _call_llm(self, messages: List[Dict[str, str]], 
                  temperature: float = 0.1) -> str:
        """调用LLM"""
        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content


class BasicRAGStrategy(RAGStrategy):
    """
    基础题策略：大海捞针 - 精准检索
    1. 小块分割（512 token）
    2. 向量检索Top K（扩大K值）
    3. 根据元数据过滤（年份、关键词等）
    4. 重排序选出Top 1
    5. 生成答案并引用来源
    """
    
    def __init__(self, vector_store: VectorStore):
        super().__init__(vector_store)
        self.reranker = Reranker()
        
    def retrieve_and_answer(self, question: str) -> Dict[str, Any]:
        """
        执行基础题的检索和回答
        
        Args:
            question: 问题文本
            
        Returns:
            包含答案、来源、检索结果的字典
        """
        # 1. 向量检索Top K（扩大检索范围以增加找到正确文档的概率）
        top_k = config.BASIC_TOP_K * 3  # 扩大到15个
        search_results = self.vector_store.search(
            query=question,
            collection_type="basic",
            top_k=top_k
        )
        
        if not search_results:
            return {
                "answer": "未找到相关信息",
                "sources": [],
                "retrieved_docs": []
            }
        
        # 2. 根据元数据过滤（年份、关键词等）
        filtered_results = self._filter_by_metadata(question, search_results)
        
        # 如果过滤后没有结果，使用原始结果
        if not filtered_results:
            print("⚠️ 元数据过滤后无结果，使用原始检索结果")
            filtered_results = search_results[:config.BASIC_TOP_K]
        
        # 3. 重排序 - 传递元数据，同时考虑内容和元数据匹配
        documents = [result['content'] for result in filtered_results]
        metadatas = [result['metadata'] for result in filtered_results]
        reranked_indices = self.reranker.rerank(question, documents, top_k=1, metadatas=metadatas)
        
        # 4. 选择最相关的文档
        best_result = filtered_results[reranked_indices[0]]
        
        # 4. 构建提示词并生成答案
        prompt = self._build_prompt(question, best_result)
        answer = self._call_llm(prompt)
        
        # 5. 提取引用信息
        sources = self._extract_sources([best_result])
        
        return {
            "answer": answer,
            "sources": sources,
            "retrieved_docs": [best_result],
            "strategy": "basic"
        }
    
    def _build_prompt(self, question: str, document: Dict[str, Any]) -> List[Dict[str, str]]:
        """构建提示词"""
        source_info = document['metadata']
        source_text = f"【{source_info.get('source', '未知文件')}, P{source_info.get('page', '?')}】"
        
        system_prompt = """你是一个专业的问答助手。你的任务是根据提供的文档片段，准确回答用户的问题。

要求：
1. 直接基于文档内容回答，不要添加文档中没有的信息
2. 保持答案简洁、准确
3. 在答案末尾必须注明来源，格式为：【文件名, P页码】
4. 如果文档不包含答案所需信息，请明确说明"""
        
        user_prompt = f"""参考文档：
{source_text}
{document['content']}

问题：{question}

请根据上述文档回答问题，并在答案末尾标注来源。"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[str]:
        """提取来源信息"""
        sources = []
        for doc in documents:
            metadata = doc['metadata']
            source = f"【{metadata.get('source', '未知')}, P{metadata.get('page', '?')}】"
            if source not in sources:
                sources.append(source)
        return sources
    
    def _filter_by_metadata(self, question: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根据问题中的元数据信息（年份、关键词等）过滤检索结果
        
        Args:
            question: 问题文本
            results: 检索结果列表
            
        Returns:
            过滤后的结果列表
        """
        import re
        
        # 1. 提取问题中的年份范围
        year_range_pattern = r'(\d{4})\s*[-~至到]\s*(\d{4})'
        year_range_match = re.search(year_range_pattern, question)
        
        query_years = []
        if year_range_match:
            start_year = int(year_range_match.group(1))
            end_year = int(year_range_match.group(2))
            query_years = list(range(start_year, end_year + 1))
        else:
            # 提取单个年份
            single_years = re.findall(r'(\d{4})', question)
            query_years = [int(y) for y in single_years if 2000 <= int(y) <= 2100]
        
        # 2. 提取问题中的关键词（大写字母组合，如ERA、SPD等）
        query_keywords = set(re.findall(r'\b[A-Z]{2,}\b', question))
        
        # 3. 对结果进行评分和过滤
        scored_results = []
        for result in results:
            metadata = result['metadata']
            score = 0
            
            # 年份匹配评分
            if query_years:
                if 'year_range_start' in metadata and 'year_range_end' in metadata:
                    doc_start = metadata['year_range_start']
                    doc_end = metadata['year_range_end']
                    # 完全匹配
                    if all(doc_start <= year <= doc_end for year in query_years):
                        score += 100  # 高分
                    # 部分匹配
                    elif any(doc_start <= year <= doc_end for year in query_years):
                        score += 50
                elif 'year' in metadata:
                    if metadata['year'] in query_years:
                        score += 100
            
            # 关键词匹配评分
            if query_keywords:
                # keywords现在是逗号分隔的字符串，需要先分割
                keywords_str = metadata.get('keywords', '')
                doc_keywords = set(keywords_str.split(',')) if keywords_str else set()
                matches = len(query_keywords & doc_keywords)
                score += matches * 30
            
            # 文件名匹配评分（关键词在文件名中出现）
            filename = metadata.get('filename', '').lower()
            for kw in query_keywords:
                if kw.lower() in filename:
                    score += 20
            
            scored_results.append((score, result))
        
        # 4. 按分数排序
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # 5. 如果最高分 >= 50（有一定匹配），则只保留高分结果
        if scored_results and scored_results[0][0] >= 50:
            # 保留分数 >= 最高分一半的结果
            threshold = scored_results[0][0] / 2
            filtered = [result for score, result in scored_results if score >= threshold]
            
            # 打印过滤信息
            print(f"🔍 [元数据过滤] 从 {len(results)} 个结果中筛选出 {len(filtered)} 个高匹配度文档")
            if scored_results[0][0] >= 100:
                top_source = scored_results[0][1]['metadata'].get('source', '未知')
                print(f"   ✓ 找到强匹配文档: {top_source}")
            
            return filtered[:config.BASIC_TOP_K]  # 返回前K个
        
        # 6. 如果没有明显的元数据匹配，返回空列表（让调用者使用原始结果）
        return []


class IntermediateRAGStrategy(RAGStrategy):
    """
    中级题策略：单文档综合 - 宽泛检索 + 摘要合成
    1. 递归分块（1024 token，保持章节结构）
    2. 检索Top 10，确保来自同一文档
    3. 合成综合答案
    """
    
    def retrieve_and_answer(self, question: str) -> Dict[str, Any]:
        """
        执行中级题的检索和回答
        
        Args:
            question: 问题文本
            
        Returns:
            包含答案、来源、检索结果的字典
        """
        # 1. 宽泛检索
        top_k = config.INTERMEDIATE_TOP_K
        search_results = self.vector_store.search(
            query=question,
            collection_type="intermediate",
            top_k=top_k
        )
        
        if not search_results:
            return {
                "answer": "未找到相关信息",
                "sources": [],
                "retrieved_docs": []
            }
        
        if not search_results:
            return {
                "answer": "未找到直接相关的文档（知识库可能不包含该标准）",
                "sources": [],
                "retrieved_docs": []
            }
        
        # 2. 按源文件分组
        docs_by_source = {}
        for result in search_results:
            source = result['metadata'].get('source', 'unknown')
            if source not in docs_by_source:
                docs_by_source[source] = []
            docs_by_source[source].append(result)
        
        # 3. 选择文档数量最多的源（最相关的文档）
        main_source = max(docs_by_source.items(), key=lambda x: len(x[1]))
        selected_docs = main_source[1]
        
        # 4. 构建提示词并生成答案
        prompt = self._build_prompt(question, selected_docs)
        answer = self._call_llm(prompt)
        
        # 5. 提取引用信息
        sources = self._extract_sources(selected_docs)
        
        return {
            "answer": answer,
            "sources": sources,
            "retrieved_docs": selected_docs,
            "strategy": "intermediate"
        }
    
    def _build_prompt(self, question: str, documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """构建提示词"""
        # 构建文档内容
        doc_content = ""
        for i, doc in enumerate(documents, 1):
            metadata = doc['metadata']
            source_info = f"【{metadata.get('source', '未知')}, P{metadata.get('page', '?')}】"
            doc_content += f"\n\n--- 段落 {i} {source_info} ---\n{doc['content']}"
        
        system_prompt = """你是一个专业的问答助手。你的任务是综合分析来自同一文档不同部分的信息，形成完整、有条理的答案。

要求：
1. 这些段落来自同一个文档的不同部分，请将它们综合起来回答问题
2. 答案要全面、系统，形成完整的逻辑
3. 答案中必须标注所有引用的来源，格式为：【文件名, P页码】
4. 如果不同段落有补充或相关信息，请都纳入答案中
5. 保持答案的连贯性和条理性"""
        
        user_prompt = f"""参考文档（来自同一文档的不同部分）：
{doc_content}

问题：{question}

请综合上述所有段落的信息，给出完整、有条理的答案，并标注来源。"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[str]:
        """提取来源信息"""
        sources = set()
        for doc in documents:
            metadata = doc['metadata']
            source = f"【{metadata.get('source', '未知')}, P{metadata.get('page', '?')}】"
            sources.add(source)
        return sorted(list(sources))

class AdvancedRAGStrategy(RAGStrategy):
    """
    高级题策略：多文档综合 - 多轮检索 + Agent思维
    1. LLM分解问题为子问题
    2. 对每个子问题独立检索（可能来自不同文档）
    3. 汇总所有结果，进行对比分析
    """
    
    def retrieve_and_answer(self, question: str) -> Dict[str, Any]:
        """
        执行高级题的检索和回答
        
        Args:
            question: 问题文本
            
        Returns:
            包含答案、来源、检索结果的字典
        """
        # 1. 分解问题
        sub_questions = self._decompose_question(question)
        
        # 2. 对每个子问题进行检索
        all_results = []
        sub_answers = []
        
        for sub_q in sub_questions:
            results = self.vector_store.search(
                query=sub_q,
                collection_type="advanced",
                top_k=5
            )
            
            if results:
                all_results.extend(results)
                # 为每个子问题生成初步答案
                sub_answer = self._answer_sub_question(sub_q, results)
                sub_answers.append({
                    "question": sub_q,
                    "answer": sub_answer,
                    "sources": self._extract_sources(results)
                })
        
        # 3. 去重（基于内容相似度）
        unique_results = self._deduplicate_results(all_results)
        
        # 4. 综合所有信息生成最终答案
        prompt = self._build_final_prompt(question, sub_answers, unique_results)
        final_answer = self._call_llm(prompt, temperature=0.2)
        
        # 5. 提取所有来源
        all_sources = self._extract_sources(unique_results)
        
        return {
            "answer": final_answer,
            "sources": all_sources,
            "retrieved_docs": unique_results,
            "sub_questions": sub_questions,
            "sub_answers": sub_answers,
            "strategy": "advanced"
        }
    
    def _decompose_question(self, question: str) -> List[str]:
        """使用LLM分解复杂问题"""
        prompt = [
            {"role": "system", "content": """你是一个问题分析专家。你的任务是将复杂问题分解为2-4个更简单的子问题。

要求：
1. 每个子问题应该独立且明确
2. 子问题的答案组合起来能够回答原问题
3. 如果问题涉及比较，应该为每个对象创建独立的子问题
4. 直接输出子问题列表，每行一个，前面加序号"""},
            {"role": "user", "content": f"请将以下问题分解为子问题：\n{question}"}
        ]
        
        response = self._call_llm(prompt, temperature=0.1)
        
        # 解析子问题
        sub_questions = []
        for line in response.strip().split('\n'):
            # 移除序号和空白
            cleaned = line.strip()
            if cleaned and len(cleaned) > 5:
                # 移除开头的数字、点、括号等
                import re
                cleaned = re.sub(r'^[\d\.\))\]、]+\s*', '', cleaned)
                if cleaned:
                    sub_questions.append(cleaned)
        
        # 如果分解失败，使用原问题
        if not sub_questions:
            sub_questions = [question]
        
        return sub_questions
    
    def _answer_sub_question(self, sub_question: str, 
                            documents: List[Dict[str, Any]]) -> str:
        """回答子问题"""
        doc_content = ""
        for i, doc in enumerate(documents[:2], 1):  # 最多使用2个文档
            metadata = doc['metadata']
            source_info = f"【{metadata.get('source', '未知')}, P{metadata.get('page', '?')}】"
            # 截取前400字符
            content_brief = doc['content'][:400]
            doc_content += f"\n[文档{i}] {source_info}\n{content_brief}...\n"
        
        prompt = [
            {"role": "system", "content": "你是专业问答助手。简洁回答问题。"},
            {"role": "user", "content": f"文档：\n{doc_content}\n\n问题：{sub_question}\n\n简要回答："}
        ]
        
        return self._call_llm(prompt)
    
    def _build_final_prompt(self, question: str, sub_answers: List[Dict[str, Any]],
                           documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """构建最终答案的提示词"""
        # 构建子问题答案总结（精简版，每个答案最多200字）
        sub_answers_text = ""
        for i, sub in enumerate(sub_answers, 1):
            sources_str = "、".join(sub['sources'][:2])  # 只取前2个来源
            answer_brief = sub['answer'][:200] + "..." if len(sub['answer']) > 200 else sub['answer']
            sub_answers_text += f"\n{i}. {sub['question']}\n   {answer_brief}\n   来源：{sources_str}\n"
        
        # 构建支撑文档（最多5个，每个最多300字符）
        docs_text = ""
        seen_contents = set()
        doc_count = 0
        for doc in documents:
            if doc_count >= 5:  # 最多5个文档
                break
            content = doc['content'][:300]  # 截取前300字符
            if content not in seen_contents:
                metadata = doc['metadata']
                source_info = f"【{metadata.get('source', '未知')}, P{metadata.get('page', '?')}】"
                docs_text += f"\n[文档{doc_count+1}] {source_info}\n{content}...\n"
                seen_contents.add(content)
                doc_count += 1
        
        system_prompt = """你是专业的技术文档分析助手。基于多个文档信息进行综合分析。

要求：
1. 综合子问题答案和文档信息
2. 对比不同文档的差异
3. 答案简洁清晰，分点阐述
4. 必须标注来源：【文件名, P页码】"""
        
        user_prompt = f"""问题：{question}

子问题分析：
{sub_answers_text}

参考文档：
{docs_text}

请综合回答，标注来源。"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复的检索结果"""
        seen = set()
        unique = []
        
        for result in results:
            # 使用内容的前100字符作为去重依据
            key = result['content'][:100]
            if key not in seen:
                seen.add(key)
                unique.append(result)
        
        return unique
    
    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[str]:
        """提取来源信息"""
        sources = set()
        for doc in documents:
            metadata = doc['metadata']
            source = f"【{metadata.get('source', '未知')}, P{metadata.get('page', '?')}】"
            sources.add(source)
        return sorted(list(sources))


class RAGStrategyFactory:
    """RAG策略工厂"""
    
    @staticmethod
    def create_strategy(difficulty: DifficultyLevel, 
                       vector_store: VectorStore) -> RAGStrategy:
        """
        根据难度创建对应的RAG策略
        
        Args:
            difficulty: 难度等级
            vector_store: 向量数据库
            
        Returns:
            对应的RAG策略实例
        """
        if difficulty == DifficultyLevel.BASIC:
            return BasicRAGStrategy(vector_store)
        elif difficulty == DifficultyLevel.INTERMEDIATE:
            return IntermediateRAGStrategy(vector_store)
        elif difficulty == DifficultyLevel.ADVANCED:
            return AdvancedRAGStrategy(vector_store)
        else:
            raise ValueError(f"未知的难度等级: {difficulty}")
