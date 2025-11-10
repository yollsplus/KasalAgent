"""
配置管理模块
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """全局配置类"""
    
    # 项目路径
    BASE_DIR = Path(__file__).parent
    AI_DATABASE_PATH = BASE_DIR / "AI_database"
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
    
    # 模型配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
    RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-large")
    
    # 向量数据库配置
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "ai_database")
    
    # 分块配置
    BASIC_CHUNK_SIZE = int(os.getenv("BASIC_CHUNK_SIZE", 512))
    BASIC_CHUNK_OVERLAP = int(os.getenv("BASIC_CHUNK_OVERLAP", 50))
    INTERMEDIATE_CHUNK_SIZE = int(os.getenv("INTERMEDIATE_CHUNK_SIZE", 1024))
    INTERMEDIATE_CHUNK_OVERLAP = int(os.getenv("INTERMEDIATE_CHUNK_OVERLAP", 100))
    ADVANCED_CHUNK_SIZE = int(os.getenv("ADVANCED_CHUNK_SIZE", 1024))
    ADVANCED_CHUNK_OVERLAP = int(os.getenv("ADVANCED_CHUNK_OVERLAP", 150))
    
    # 检索配置
    BASIC_TOP_K = int(os.getenv("BASIC_TOP_K", 5))
    INTERMEDIATE_TOP_K = int(os.getenv("INTERMEDIATE_TOP_K", 10))
    ADVANCED_TOP_K = int(os.getenv("ADVANCED_TOP_K", 15))
    
    @classmethod
    def validate(cls):
        """验证配置是否完整"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("请在.env文件中配置OPENAI_API_KEY")
        if not cls.AI_DATABASE_PATH.exists():
            raise ValueError(f"AI_database目录不存在: {cls.AI_DATABASE_PATH}")

config = Config()
