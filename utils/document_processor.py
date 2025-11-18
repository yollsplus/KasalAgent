"""
文档处理模块：负责TXT文件读取、文本分块、元数据提取
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from tqdm import tqdm


@dataclass
class Document:
    """文档数据类"""
    content: str
    metadata: Dict[str, Any]
    page_number: Optional[int] = None


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        
    def txt_to_documents(self, txt_path: Path) -> List[Document]:
        """
        读取TXT文件并转换为文档
        
        Args:
            txt_path: TXT文件路径
            
        Returns:
            文档列表
        """
        documents = []
        
        try:
            # 读取文本文件
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # 清理文本
            text = self._clean_text(text)
            
            if text.strip():
                # 尝试按页面分割（如果文本中有页面标记）
                pages = self._split_by_pages(text)
                
                # 提取文件元数据
                file_metadata = self._extract_file_metadata(txt_path)
                
                if len(pages) > 1:
                    # 有页面标记，按页面创建文档
                    for page_num, page_content in enumerate(pages, 1):
                        if page_content.strip():
                            documents.append(Document(
                                content=page_content,
                                metadata={
                                    "source": txt_path.name,
                                    "file_path": str(txt_path),
                                    "page": page_num,
                                    "category": self._extract_category(txt_path),
                                    **file_metadata  # 添加文件元数据
                                },
                                page_number=page_num
                            ))
                else:
                    # 没有页面标记，作为单个文档
                    documents.append(Document(
                        content=text,
                        metadata={
                            "source": txt_path.name,
                            "file_path": str(txt_path),
                            "page": 1,
                            "category": self._extract_category(txt_path),
                            **file_metadata  # 添加文件元数据
                        },
                        page_number=1
                    ))
            
        except Exception as e:
            print(f"处理TXT文件 {txt_path} 时出错: {e}")
            
        return documents
    
    def process_all_txts(self) -> List[Document]:
        """
        处理AI_database目录下的所有TXT文件
        
        Returns:
            所有文档的列表
        """
        all_documents = []
        txt_files = list(self.database_path.rglob("*.txt"))
        
        print(f"发现 {len(txt_files)} 个TXT文件")
        
        for txt_file in tqdm(txt_files, desc="处理TXT文件"):
            docs = self.txt_to_documents(txt_file)
            all_documents.extend(docs)
            
        print(f"共处理 {len(all_documents)} 个文档")
        return all_documents
    
    def _split_by_pages(self, text: str) -> List[str]:
        """
        尝试按页面标记分割文本
        常见的页面标记：\f, ---PAGE---, 第X页等
        """
        # 方式1：\f (form feed) 字符
        if '\f' in text:
            return [p.strip() for p in text.split('\f') if p.strip()]
        
        # 方式2：---PAGE--- 标记
        if '---PAGE---' in text:
            return [p.strip() for p in text.split('---PAGE---') if p.strip()]
        
        # 方式3：第X页标记
        page_pattern = r'\n第\s*\d+\s*页\n'
        if re.search(page_pattern, text):
            pages = re.split(page_pattern, text)
            return [p.strip() for p in pages if p.strip()]
        
        # 没有页面标记，返回整个文本
        return [text]
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()
    
    def _extract_category(self, file_path: Path) -> str:
        """
        从文件路径中提取分类信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            分类字符串
        """
        parts = file_path.parts
        
        # 找到AI_database的索引
        try:
            db_index = parts.index("AI_database")
            # 返回AI_database之后的所有路径部分
            categories = parts[db_index + 1:-1]  # 排除文件名
            return " > ".join(categories) if categories else "未分类"
        except ValueError:
            return "未分类"
    
    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        从文件名和路径中提取关键元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含年份、标题等信息的元数据字典
        """
        filename = file_path.name
        metadata = {}
        
        # 1. 提取年份范围 (如2025-2027、2024-2026等)
        year_pattern = r'(\d{4})\s*[-~]\s*(\d{4})'
        year_match = re.search(year_pattern, filename)
        if year_match:
            start_year = int(year_match.group(1))
            end_year = int(year_match.group(2))
            metadata['year_range_start'] = start_year
            metadata['year_range_end'] = end_year
            metadata['year_range_text'] = f"{start_year}-{end_year}"
        
        # 2. 提取单个年份
        single_year_pattern = r'(\d{4})'
        single_year_match = re.search(single_year_pattern, filename)
        if single_year_match and 'year_range_start' not in metadata:
            year = int(single_year_match.group(1))
            metadata['year'] = year
        
        # 3. 提取主要关键词 (文件名中的主要部分，去掉年份和扩展名)
        # 移除年份和扩展名，获取文件名的核心部分
        core_name = re.sub(r'(\d{4}[-~]\d{4}|\d{4}|\.txt)', '', filename)
        core_name = re.sub(r'[_\-\s]+', ' ', core_name).strip()
        if core_name:
            metadata['file_title'] = core_name
            
            # 提取关键词（比如SPD、CBTC、ERA等）
            # 先尝试提取大写字母组合
            key_words = re.findall(r'[A-Z]{2,}', core_name)
            # 如果没有大写组合，尝试提取单词（不区分大小写）
            if not key_words:
                key_words = re.findall(r'\b[a-zA-Z]{2,}\b', core_name)
                key_words = [w.upper() for w in key_words]  # 统一转大写
            if key_words:
                # ChromaDB只支持基本类型，将列表转换为逗号分隔的字符串
                metadata['keywords'] = ','.join(key_words)
        
        # 4. 添加完整文件名
        metadata['filename'] = filename
        
        return metadata


class TextChunker:
    """文本分块器"""
    
    @staticmethod
    def chunk_for_basic(documents: List[Document], chunk_size: int = 512, 
                       overlap: int = 50) -> List[Document]:
        """
        为基础题进行小块分割（精准检索）
        
        Args:
            documents: 文档列表
            chunk_size: 块大小（字符数）
            overlap: 重叠大小
            
        Returns:
            分块后的文档列表
        """
        chunked_docs = []
        
        for doc in documents:
            chunks = TextChunker._split_text(doc.content, chunk_size, overlap)
            
            for i, chunk in enumerate(chunks):
                chunked_docs.append(Document(
                    content=chunk,
                    metadata={
                        **doc.metadata,
                        "chunk_id": i,
                        "chunk_type": "basic",
                        "total_chunks": len(chunks)
                    },
                    page_number=doc.page_number
                ))
                
        return chunked_docs
    
    @staticmethod
    def chunk_for_intermediate(documents: List[Document], chunk_size: int = 1024,
                              overlap: int = 100) -> List[Document]:
        """
        为中级题进行递归分块（保持文档结构）
        
        Args:
            documents: 文档列表
            chunk_size: 块大小
            overlap: 重叠大小
            
        Returns:
            分块后的文档列表
        """
        chunked_docs = []
        
        # 按源文件分组
        docs_by_source = {}
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            if source not in docs_by_source:
                docs_by_source[source] = []
            docs_by_source[source].append(doc)
        
        # 对每个源文件进行分块
        for source, source_docs in docs_by_source.items():
            # 合并同一文件的所有页面
            full_text = "\n\n".join([d.content for d in source_docs])
            
            # 尝试按章节分割
            sections = TextChunker._split_by_sections(full_text)
            
            if len(sections) > 1:
                # 有章节结构，使用章节作为块
                for i, section in enumerate(sections):
                    chunked_docs.append(Document(
                        content=section,
                        metadata={
                            **source_docs[0].metadata,
                            "chunk_id": i,
                            "chunk_type": "intermediate_section",
                            "total_chunks": len(sections)
                        }
                    ))
            else:
                # 没有章节结构，使用滑动窗口
                chunks = TextChunker._split_text(full_text, chunk_size, overlap)
                for i, chunk in enumerate(chunks):
                    chunked_docs.append(Document(
                        content=chunk,
                        metadata={
                            **source_docs[0].metadata,
                            "chunk_id": i,
                            "chunk_type": "intermediate_window",
                            "total_chunks": len(chunks)
                        }
                    ))
        
        return chunked_docs
    
    @staticmethod
    def chunk_for_advanced(documents: List[Document], chunk_size: int = 1024,
                          overlap: int = 150) -> List[Document]:
        """
        为高级题进行分块（支持多文档检索）
        
        Args:
            documents: 文档列表
            chunk_size: 块大小
            overlap: 重叠大小
            
        Returns:
            分块后的文档列表
        """
        chunked_docs = []
        
        for doc in documents:
            chunks = TextChunker._split_text(doc.content, chunk_size, overlap)
            
            for i, chunk in enumerate(chunks):
                chunked_docs.append(Document(
                    content=chunk,
                    metadata={
                        **doc.metadata,
                        "chunk_id": i,
                        "chunk_type": "advanced",
                        "total_chunks": len(chunks)
                    },
                    page_number=doc.page_number
                ))
                
        return chunked_docs
    
    @staticmethod
    def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
        """滑动窗口分割文本"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk)
            
            start += chunk_size - overlap
            
        return chunks
    
    @staticmethod
    def _split_by_sections(text: str) -> List[str]:
        """
        尝试按章节分割文本
        识别常见的标题模式
        """
        # 匹配常见的标题模式
        patterns = [
            r'\n第[一二三四五六七八九十\d]+章[^\n]*\n',
            r'\n第[一二三四五六七八九十\d]+节[^\n]*\n',
            r'\n\d+\.\d+[^\n]*\n',
            r'\n[A-Z\d]+\.[^\n]*\n',
        ]
        
        sections = []
        current_pos = 0
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text))
            if len(matches) >= 2:  # 至少找到2个标题才认为有结构
                for i, match in enumerate(matches):
                    if i > 0:
                        section = text[current_pos:match.start()].strip()
                        if section:
                            sections.append(section)
                    current_pos = match.start()
                
                # 添加最后一节
                if current_pos < len(text):
                    section = text[current_pos:].strip()
                    if section:
                        sections.append(section)
                return sections
        
        # 如果没有找到章节结构，返回原文本
        return [text]
