"""
文档处理模块：负责PDF转换、文本分块、元数据提取
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import pymupdf  # PyMuPDF
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
        
    def pdf_to_text(self, pdf_path: Path) -> List[Document]:
        """
        将PDF转换为文本，保留页码信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            文档列表，每个文档对应一页
        """
        documents = []
        
        try:
            doc = pymupdf.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # 清理文本
                text = self._clean_text(text)
                
                if text.strip():  # 只保留非空页面
                    documents.append(Document(
                        content=text,
                        metadata={
                            "source": str(pdf_path.name),
                            "file_path": str(pdf_path),
                            "page": page_num + 1,  # 页码从1开始
                            "category": self._extract_category(pdf_path)
                        },
                        page_number=page_num + 1
                    ))
            
            doc.close()
            
        except Exception as e:
            print(f"处理PDF文件 {pdf_path} 时出错: {e}")
            
        return documents
    
    def process_all_pdfs(self) -> List[Document]:
        """
        处理AI_database目录下的所有PDF文件
        
        Returns:
            所有文档的列表
        """
        all_documents = []
        pdf_files = list(self.database_path.rglob("*.pdf"))
        
        print(f"发现 {len(pdf_files)} 个PDF文件")
        
        for pdf_file in tqdm(pdf_files, desc="处理PDF文件"):
            docs = self.pdf_to_text(pdf_file)
            all_documents.extend(docs)
            
        print(f"共处理 {len(all_documents)} 个文档页面")
        return all_documents
    
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
