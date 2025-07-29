"""
Health Checker - 系统健康检查

检查系统各组件的运行状态和配置有效性
"""

import os
import json
import logging
import sys
from typing import Dict, List
from pathlib import Path

def run_health_check():
    """运行系统健康检查"""
    import sys
    import os
    
    # 添加当前目录到Python路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    logger = logging.getLogger(__name__)
    
    print("AI智能书签分类系统 - 健康检查")
    print("=" * 50)
    
    issues = []
    
    # 1. 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 8):
        issues.append(f"[ERROR] Python版本过低: {python_version.major}.{python_version.minor}, 需要 >= 3.8")
    else:
        print(f"[OK] Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 2. 检查依赖包
    required_packages = [
        ('beautifulsoup4', 'bs4'), ('lxml', 'lxml'), ('rich', 'rich'), 
        ('numpy', 'numpy'), ('scikit-learn', 'sklearn')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"[OK] 依赖包: {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            issues.append(f"[ERROR] 缺少依赖包: {package_name}")
    
    if missing_packages:
        print(f"\n安装缺少的依赖包:")
        print(f"pip install {' '.join(missing_packages)}")
    
    # 3. 检查目录结构
    required_dirs = ['src', 'tests/input', 'tests/output', 'models', 'logs']
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"[OK] 目录结构: {dir_path}")
        else:
            print(f"[WARN] 目录不存在: {dir_path} (将自动创建)")
            os.makedirs(dir_path, exist_ok=True)
    
    # 4. 检查配置文件
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_sections = ['category_rules', 'ai_settings']
            for section in required_sections:
                if section in config:
                    print(f"[OK] 配置节: {section}")
                else:
                    issues.append(f"[ERROR] 配置文件缺少节: {section}")
        
        except json.JSONDecodeError as e:
            issues.append(f"[ERROR] 配置文件格式错误: {e}")
    else:
        issues.append("[ERROR] 配置文件 config.json 不存在")
    
    # 5. 检查核心模块
    core_modules = [
        'src.ai_classifier',
        'src.bookmark_processor',
        'src.rule_engine',
        'src.cli_interface'
    ]
    
    for module in core_modules:
        try:
            __import__(module)
            print(f"[OK] 核心模块: {module}")
        except ImportError as e:
            issues.append(f"[ERROR] 模块导入失败: {module} - {e}")
    
    # 6. 检查测试数据
    test_input_dir = "tests/input"
    if os.path.exists(test_input_dir):
        html_files = [f for f in os.listdir(test_input_dir) if f.endswith('.html')]
        if html_files:
            print(f"[OK] 测试数据: 找到 {len(html_files)} 个HTML文件")
        else:
            print("[WARN] 测试数据: 没有找到HTML书签文件")
    
    # 输出健康检查结果
    print("\n" + "=" * 50)
    if issues:
        print(f"[ERROR] 发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"   {issue}")
        print("\n请解决以上问题后重新运行系统")
        return False
    else:
        print("[OK] 系统健康检查通过!")
        print("系统已准备就绪，可以开始使用")
        return True

if __name__ == "__main__":
    run_health_check()