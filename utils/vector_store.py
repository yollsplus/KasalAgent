"""
向量数据库和检索模块
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker
from pathlib import Path
import numpy as np
import re
from tqdm import tqdm

from utils.document_processor import Document
from config import config


class EmbeddingModel:
    """嵌入模型封装"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        print(f"加载嵌入模型: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文档"""
        embeddings = self.model.encode(
            texts, 
            show_progress_bar=False,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询"""
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()


class Reranker:
    """重排序模型 - 同时考虑内容相关度和元数据匹配度"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.RERANKER_MODEL
        print(f"加载重排序模型: {self.model_name}")
        self.model = FlagReranker(self.model_name, use_fp16=True)
        
    def rerank(self, query: str, documents: List[str], top_k: int = 1,
              metadatas: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        重排序文档，同时考虑内容相关度和元数据匹配度
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个
            metadatas: 文档元数据列表（可选）
            
        Returns:
            排序后的文档索引列表
        """
        if not documents:
            return []
        
        # 构建query-document对
        pairs = [[query, doc] for doc in documents]
        
        # 计算内容相关度分数
        content_scores = self.model.compute_score(pairs)
        
        # 如果只有一个文档，转换为列表
        if isinstance(content_scores, float):
            content_scores = [content_scores]
        
        # 归一化内容分数到[0, 1]
        content_scores = np.array(content_scores)
        if content_scores.max() > content_scores.min():
            content_scores = (content_scores - content_scores.min()) / (content_scores.max() - content_scores.min())
        
        # 计算元数据匹配分数
        metadata_scores = np.zeros(len(documents))
        if metadatas:
            metadata_scores = self._compute_metadata_scores(query, metadatas)
        
        # 加权融合分数 (内容权重0.7，元数据权重0.3)
        final_scores = 0.7 * content_scores + 0.3 * metadata_scores
        
        # 排序并返回top_k
        sorted_indices = np.argsort(final_scores)[::-1][:top_k]
        return sorted_indices.tolist()
    
    def _compute_metadata_scores(self, query: str, metadatas: List[Dict[str, Any]]) -> np.ndarray:
        """
        计算元数据匹配分数
        
        优先考虑：
        1. 年份范围匹配（完全匹配得1分）
        2. 关键词匹配
        3. 标题相关性
        """
        scores = np.zeros(len(metadatas))
        
        # 从查询中提取年份
        query_years = self._extract_years_from_query(query)
        
        for i, metadata in enumerate(metadatas):
            score = 0.0
            
            # 1. 年份匹配 (权重最高，0.6分)
            if query_years:
                year_score = self._match_year_range(query_years, metadata)
                score += 0.6 * year_score
            
            # 2. 关键词匹配 (0.25分)
            if 'keywords' in metadata:
                keyword_score = self._match_keywords(query, metadata['keywords'])
                score += 0.25 * keyword_score
            
            # 3. 文件标题相关性 (0.15分)
            if 'file_title' in metadata:
                title_score = self._compute_title_similarity(query, metadata['file_title'])
                score += 0.15 * title_score
            
            scores[i] = score
        
        return scores
    
    def _extract_years_from_query(self, query: str) -> List[int]:
        """从查询文本中提取年份"""
        # 查找年份范围，如 2025-2027
        year_range = re.search(r'(\d{4})\s*[-~年份]\s*(\d{4})', query)
        if year_range:
            start_year = int(year_range.group(1))
            end_year = int(year_range.group(2))
            return list(range(start_year, end_year + 1))
        
        # 查找单个年份
        years = []
        for match in re.finditer(r'(\d{4})', query):
            year = int(match.group(1))
            if 2000 <= year <= 2100:  # 合理的年份范围
                years.append(year)
        
        return years
    
    def _match_year_range(self, query_years: List[int], metadata: Dict[str, Any]) -> float:
        """
        计算年份范围匹配得分
        
        Returns:
            0 - 1 的匹配分数
        """
        if not query_years:
            return 0.0
        
        # 检查文档是否有年份范围
        if 'year_range_start' in metadata and 'year_range_end' in metadata:
            doc_start = metadata['year_range_start']
            doc_end = metadata['year_range_end']
            
            # 如果查询年份完全在文档年份范围内，得分为1
            if all(doc_start <= year <= doc_end for year in query_years):
                return 1.0
            
            # 如果有部分重叠，按重叠比例计分
            overlap = sum(1 for year in query_years if doc_start <= year <= doc_end)
            return overlap / len(query_years)
        
        # 检查单个年份
        if 'year' in metadata:
            doc_year = metadata['year']
            if doc_year in query_years:
                return 1.0
            # 如果年份接近（差1年），给予0.5分
            elif min(abs(doc_year - year) for year in query_years) == 1:
                return 0.5
        
        return 0.0
    
    def _match_keywords(self, query: str, keywords: str) -> float:
        """计算关键词匹配得分
        
        Args:
            query: 查询文本
            keywords: 逗号分隔的关键词字符串（如"ERA,SPD,CBTC"）
        """
        if not keywords:
            return 0.0
        
        # 将逗号分隔的字符串转换为列表
        keyword_list = [kw.strip() for kw in keywords.split(',')]
        matches = sum(1 for kw in keyword_list if kw.lower() in query.lower())
        return min(matches / len(keyword_list), 1.0)
    
    def _compute_title_similarity(self, query: str, title: str) -> float:
        """计算标题和查询的相似度（简单词匹配）"""
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        
        if not title_words:
            return 0.0
        
        intersection = len(query_words & title_words)
        return intersection / len(title_words)


class VectorStore:
    """向量数据库管理"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or config.VECTOR_DB_PATH
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化ChromaDB
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.embedding_model = EmbeddingModel()
        
        # 为不同难度创建不同的集合
        self.collections = {
            "basic": self._get_or_create_collection("basic_collection"),
            "intermediate": self._get_or_create_collection("intermediate_collection"),
            "advanced": self._get_or_create_collection("advanced_collection")
        }
        
    def _get_or_create_collection(self, name: str):
        """获取或创建集合"""
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(name=name)
    
    def add_documents(self, documents: List[Document], collection_type: str = "basic"):
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表
            collection_type: 集合类型（basic/intermediate/advanced）
        """
        if collection_type not in self.collections:
            raise ValueError(f"未知的集合类型: {collection_type}")
        
        collection = self.collections[collection_type]
        
        # 批量处理
        batch_size = 100
        for i in tqdm(range(0, len(documents), batch_size), 
                     desc=f"添加文档到{collection_type}集合"):
            batch = documents[i:i + batch_size]
            
            # 准备数据
            texts = [doc.content for doc in batch]
            embeddings = self.embedding_model.embed_documents(texts)
            ids = [f"{collection_type}_{i + j}" for j in range(len(batch))]
            metadatas = [doc.metadata for doc in batch]
            
            # 添加到数据库
            collection.add(
                embeddings=embeddings,
                documents=texts,
                ids=ids,
                metadatas=metadatas
            )
    
    def search(self, query: str, collection_type: str = "basic", 
              top_k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            collection_type: 集合类型
            top_k: 返回前k个结果
            filter_dict: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        if collection_type not in self.collections:
            raise ValueError(f"未知的集合类型: {collection_type}")
        
        collection = self.collections[collection_type]
        
        # 嵌入查询
        query_embedding = self.embedding_model.embed_query(query)
        
        # 搜索
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_dict
        )
        
        # 格式化结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted_results
    
    def get_collection_stats(self, collection_type: str) -> Dict[str, Any]:
        """获取集合统计信息"""
        if collection_type not in self.collections:
            raise ValueError(f"未知的集合类型: {collection_type}")
        
        collection = self.collections[collection_type]
        count = collection.count()
        
        return {
            "collection_type": collection_type,
            "document_count": count
        }
    
    def clear_collection(self, collection_type: str):
        """清空指定集合"""
        if collection_type not in self.collections:
            raise ValueError(f"未知的集合类型: {collection_type}")
        
        # 删除旧集合
        try:
            self.client.delete_collection(name=f"{collection_type}_collection")
        except:
            pass
        
        # 重新创建
        self.collections[collection_type] = self._get_or_create_collection(
            f"{collection_type}_collection"
        )
    
    def clear_all(self):
        """清空所有集合"""
        for collection_type in self.collections.keys():
            self.clear_collection(collection_type)
