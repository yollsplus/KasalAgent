"""
难度判断模块
"""
from enum import Enum


class DifficultyLevel(Enum):
    """难度等级枚举"""
    BASIC = "basic"           # 基础题：大海捞针
    INTERMEDIATE = "intermediate"  # 中级题：单文档综合
    ADVANCED = "advanced"      # 高级题：多文档综合


def judge_difficulty(question_id: str) -> DifficultyLevel:
    """
    根据题号判断难度
    
    Args:
        question_id: 题号（如 B001, I001, A001）
        
    Returns:
        难度等级
    """
    question_id = question_id.strip().upper()
    
    if question_id.startswith('B'):
        return DifficultyLevel.BASIC
    elif question_id.startswith('I'):
        return DifficultyLevel.INTERMEDIATE
    elif question_id.startswith('A'):
        return DifficultyLevel.ADVANCED
    
    # 默认返回中级
    return DifficultyLevel.INTERMEDIATE

