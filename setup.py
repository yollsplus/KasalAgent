"""
初始化脚本：帮助用户快速设置和检查环境
"""
import sys
import os
from pathlib import Path
import subprocess


def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("   需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_env_file():
    """检查.env文件"""
    print("\n检查环境配置...")
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists():
        print("⚠️  .env文件不存在")
        if env_example_path.exists():
            response = input("   是否从.env.example创建？(y/n): ")
            if response.lower() == 'y':
                env_example_path.read_text()
                with open(env_path, 'w') as f:
                    f.write(env_example_path.read_text())
                print("✅ 已创建.env文件，请编辑并填入API Key")
                return False
        return False
    
    # 检查必要配置
    env_content = env_path.read_text()
    if 'your_openai_api_key_here' in env_content:
        print("⚠️  请在.env文件中配置OPENAI_API_KEY")
        return False
    
    print("✅ .env文件配置完成")
    return True


def check_ai_database():
    """检查AI_database目录"""
    print("\n检查文档数据库...")
    db_path = Path("AI_database")
    
    if not db_path.exists():
        print("❌ AI_database目录不存在")
        return False
    
    pdf_files = list(db_path.rglob("*.pdf"))
    if not pdf_files:
        print("⚠️  AI_database目录下没有PDF文件")
        return False
    
    print(f"✅ 找到 {len(pdf_files)} 个PDF文件")
    return True


def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    
    required_packages = [
        'langchain',
        'chromadb',
        'sentence_transformers',
        'pymupdf',
        'openai',
        'FlagEmbedding'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n缺少 {len(missing)} 个依赖包")
        response = input("是否现在安装？(y/n): ")
        if response.lower() == 'y':
            print("\n开始安装依赖包...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            return True
        return False
    
    return True


def check_vector_db():
    """检查向量数据库"""
    print("\n检查向量数据库...")
    db_path = Path("vector_db")
    
    if not db_path.exists():
        print("⚠️  向量数据库未初始化")
        print("   首次运行时会自动创建")
        return False
    
    # 检查是否有数据
    chroma_path = db_path / "chroma.sqlite3"
    if chroma_path.exists():
        print("✅ 向量数据库已存在")
        return True
    else:
        print("⚠️  向量数据库为空，需要索引文档")
        return False


def test_import():
    """测试模块导入"""
    print("\n测试模块导入...")
    
    try:
        from config import config
        print("✅ config")
        
        from utils.document_processor import DocumentProcessor
        print("✅ document_processor")
        
        from utils.vector_store import VectorStore
        print("✅ vector_store")
        
        from utils.difficulty_judge import DifficultyJudge
        print("✅ difficulty_judge")
        
        from rag_strategies import RAGStrategyFactory
        print("✅ rag_strategies")
        
        from agent import QAAgent
        print("✅ agent")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def print_summary(checks):
    """打印检查摘要"""
    print("\n" + "="*60)
    print("环境检查摘要")
    print("="*60)
    
    total = len(checks)
    passed = sum(checks.values())
    
    for name, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有检查通过！可以开始使用了")
        print("\n快速开始：")
        print("  python main.py          # 启动交互式问答")
        print("  python tools.py         # 数据库管理工具")
        print("\n详细文档请参考 README.md")
    else:
        print("\n⚠️  部分检查未通过，请根据上述提示进行修复")
        print("\n常见问题：")
        print("  1. 缺少依赖：pip install -r requirements.txt")
        print("  2. 未配置API Key：编辑.env文件")
        print("  3. 缺少文档：将PDF文件放入AI_database目录")


def main():
    """主函数"""
    print("="*60)
    print("RAG问答系统 - 环境初始化检查")
    print("="*60)
    
    checks = {}
    
    # 依次检查各项
    checks['Python版本'] = check_python_version()
    checks['依赖包'] = check_dependencies()
    checks['环境配置'] = check_env_file()
    checks['文档数据库'] = check_ai_database()
    checks['向量数据库'] = check_vector_db()
    checks['模块导入'] = test_import()
    
    # 打印摘要
    print_summary(checks)
    
    # 如果环境OK，询问是否索引
    if all(checks.values()):
        response = input("\n是否现在索引文档？(y/n): ")
        if response.lower() == 'y':
            print("\n开始索引文档...")
            from agent import QAAgent
            agent = QAAgent()
            agent.index_documents()


if __name__ == "__main__":
    main()
