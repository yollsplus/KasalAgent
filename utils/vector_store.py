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
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def embed_query(self, text: str) -> List[float]:
        """嵌入查询"""
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()


class Reranker:
    """重排序模型"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or config.RERANKER_MODEL
        print(f"加载重排序模型: {self.model_name}")
        self.model = FlagReranker(self.model_name, use_fp16=True)
        
    def rerank(self, query: str, documents: List[str], top_k: int = 1) -> List[int]:
        """
        重排序文档
        
        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回前k个
            
        Returns:
            排序后的文档索引列表
        """
        if not documents:
            return []
        
        # 构建query-document对
        pairs = [[query, doc] for doc in documents]
        
        # 计算分数
        scores = self.model.compute_score(pairs)
        
        # 如果只有一个文档，返回单个索引
        if isinstance(scores, float):
            scores = [scores]
        
        # 排序并返回top_k
        sorted_indices = np.argsort(scores)[::-1][:top_k]
        return sorted_indices.tolist()


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
