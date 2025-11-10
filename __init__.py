"""
项目包初始化文件
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "基于难度分级的RAG问答系统"

from .agent import QAAgent
from .config import config
from .utils.difficulty_judge import DifficultyLevel, DifficultyJudge

__all__ = [
    'QAAgent',
    'config',
    'DifficultyLevel',
    'DifficultyJudge'
]
