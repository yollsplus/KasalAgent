"""
难度判断模块
"""
import re
from enum import Enum
from typing import Optional


class DifficultyLevel(Enum):
    """难度等级枚举"""
    BASIC = "basic"           # 基础题：大海捞针
    INTERMEDIATE = "intermediate"  # 中级题：单文档综合
    ADVANCED = "advanced"      # 高级题：多文档综合


class DifficultyJudge:
    """难度判断器"""
    
    def __init__(self):
        # 这里留空，由用户自定义规则
        self.custom_rules = {}
        
    def judge_difficulty(self, question_id: str) -> DifficultyLevel:
        """
        根据题号判断难度
        
        Args:
            question_id: 题号（字符串格式）
            
        Returns:
            难度等级
            
        示例规则（用户可以修改）：
            - B开头：基础题
            - I开头：中级题
            - A开头：高级题
            - 或者根据数字范围判断
        """
        # 默认规则示例（用户需要根据实际情况修改）
        question_id = question_id.strip().upper()
        
        # 规则1：根据前缀字母判断
        if question_id.startswith('B'):
            return DifficultyLevel.BASIC
        elif question_id.startswith('I'):
            return DifficultyLevel.INTERMEDIATE
        elif question_id.startswith('A'):
            return DifficultyLevel.ADVANCED
        
        # 规则2：根据数字范围判断
        numbers = re.findall(r'\d+', question_id)
        if numbers:
            num = int(numbers[0])
            if num < 100:
                return DifficultyLevel.BASIC
            elif num < 200:
                return DifficultyLevel.INTERMEDIATE
            else:
                return DifficultyLevel.ADVANCED
        
        # 规则3：根据特定模式判断
        if '比较' in question_id or '对比' in question_id or '综合' in question_id:
            return DifficultyLevel.ADVANCED
        elif '总结' in question_id or '概述' in question_id:
            return DifficultyLevel.INTERMEDIATE
        
        # 默认返回中级
        return DifficultyLevel.INTERMEDIATE
    
    def add_custom_rule(self, pattern: str, difficulty: DifficultyLevel):
        """
        添加自定义规则
        
        Args:
            pattern: 匹配模式（正则表达式）
            difficulty: 对应的难度等级
        """
        self.custom_rules[pattern] = difficulty
    
    def judge_with_custom_rules(self, question_id: str) -> DifficultyLevel:
        """
        使用自定义规则判断难度
        
        Args:
            question_id: 题号
            
        Returns:
            难度等级
        """
        # 先检查自定义规则
        for pattern, difficulty in self.custom_rules.items():
            if re.match(pattern, question_id):
                return difficulty
        
        # 没有匹配的自定义规则，使用默认判断
        return self.judge_difficulty(question_id)
    
    def get_difficulty_description(self, difficulty: DifficultyLevel) -> str:
        """
        获取难度描述
        
        Args:
            difficulty: 难度等级
            
        Returns:
            难度描述
        """
        descriptions = {
            DifficultyLevel.BASIC: "基础题（大海捞针）- 精准检索单一答案",
            DifficultyLevel.INTERMEDIATE: "中级题（单文档综合）- 整合同一文档多个段落",
            DifficultyLevel.ADVANCED: "高级题（多文档综合）- 跨文档对比分析"
        }
        return descriptions.get(difficulty, "未知难度")


# ==========================================
# 用户自定义区域 - 请在这里添加您的判断规则
# ==========================================

def custom_difficulty_judge(question_id: str) -> DifficultyLevel:
    """
    用户自定义的难度判断函数
    
    请根据您的实际需求修改此函数
    
    Args:
        question_id: 题号
        
    Returns:
        难度等级
    
    示例1：根据题号前缀
        if question_id.startswith('BASIC_'):
            return DifficultyLevel.BASIC
    
    示例2：根据题号数字范围
        num = int(re.search(r'\d+', question_id).group())
        if num <= 50:
            return DifficultyLevel.BASIC
    
    示例3：根据题号格式
        if '-' in question_id:
            parts = question_id.split('-')
            if parts[0] == 'L1':
                return DifficultyLevel.BASIC
    """
    # TODO: 在这里实现您的判断逻辑
    # 目前使用默认判断
    judge = DifficultyJudge()
    return judge.judge_difficulty(question_id)
