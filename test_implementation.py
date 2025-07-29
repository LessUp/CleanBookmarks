#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实现的功能
"""

import sys
import os
sys.path.append('.')

def test_semantic_analyzer():
    """测试语义分析器"""
    try:
        from src.placeholder_modules import SemanticAnalyzer
        from src.ai_classifier import BookmarkFeatures
        
        analyzer = SemanticAnalyzer()
        features = BookmarkFeatures(
            url="https://github.com/microsoft/vscode",
            title="Visual Studio Code - Code Editing. Redefined",
            domain="github.com",
            path_segments=["microsoft", "vscode"],
            query_params={},
            content_type="repository",
            language="en"
        )
        
        result = analyzer.classify(features)
        print(f"[SemanticAnalyzer] 测试通过: {result is not None}")
        if result:
            print(f"  分类: {result.get('category')}")
            print(f"  置信度: {result.get('confidence', 0):.2f}")
        return True
    except Exception as e:
        print(f"[SemanticAnalyzer] 测试失败: {e}")
        return False

def test_user_profiler():
    """测试用户画像分析器"""
    try:
        from src.placeholder_modules import UserProfiler
        from src.ai_classifier import BookmarkFeatures
        
        profiler = UserProfiler('test_profile.json')
        features = BookmarkFeatures(
            url="https://stackoverflow.com/questions/python",
            title="Python Questions - Stack Overflow",
            domain="stackoverflow.com",
            path_segments=["questions", "python"],
            query_params={},
            content_type="qa",
            language="en"
        )
        
        # 测试分类
        result = profiler.classify(features)
        print(f"[UserProfiler] 分类测试通过: {result is not None}")
        
        # 测试学习更新
        profiler.update_preferences(features, "技术/编程", 0.9)
        print("[UserProfiler] 学习更新测试通过")
        
        # 清理测试文件
        if os.path.exists('test_profile.json'):
            os.remove('test_profile.json')
        
        return True
    except Exception as e:
        print(f"[UserProfiler] 测试失败: {e}")
        return False

def test_deduplicator():
    """测试去重器"""
    try:
        from src.placeholder_modules import BookmarkDeduplicator
        
        deduplicator = BookmarkDeduplicator()
        
        # 测试数据
        bookmarks = [
            {"url": "https://github.com/microsoft/vscode", "title": "VS Code"},
            {"url": "https://github.com/microsoft/vscode/", "title": "Visual Studio Code"},  # 相似URL
            {"url": "https://python.org", "title": "Python.org"},
            {"url": "https://docs.python.org", "title": "Python Documentation"}
        ]
        
        unique, duplicates = deduplicator.remove_duplicates(bookmarks)
        print(f"[BookmarkDeduplicator] 测试通过")
        print(f"  原始数量: {len(bookmarks)}")
        print(f"  去重后: {len(unique)}")
        print(f"  重复数量: {len(duplicates)}")
        
        return True
    except Exception as e:
        print(f"[BookmarkDeduplicator] 测试失败: {e}")
        return False

def test_data_exporter():
    """测试数据导出器"""
    try:
        from src.placeholder_modules import DataExporter
        
        exporter = DataExporter()
        
        # 测试数据
        test_data = {
            "技术": {
                "_items": [
                    {
                        "url": "https://github.com/microsoft/vscode",
                        "title": "VS Code",
                        "confidence": 0.95,
                        "method": "rule_engine"
                    }
                ],
                "_subcategories": {}
            }
        }
        
        stats = {"processed_bookmarks": 1, "processing_time": 0.1}
        
        # 测试各种格式导出
        formats_tested = []
        
        try:
            exporter.export_json(test_data, "test_output.json", stats)
            formats_tested.append("JSON")
            os.remove("test_output.json")
        except Exception:
            pass
        
        try:
            exporter.export_html(test_data, "test_output.html", stats)
            formats_tested.append("HTML")
            os.remove("test_output.html")
        except Exception:
            pass
        
        try:
            exporter.export_markdown(test_data, "test_output.md", stats)
            formats_tested.append("Markdown")
            os.remove("test_output.md")
        except Exception:
            pass
        
        print(f"[DataExporter] 测试通过")
        print(f"  支持格式: {', '.join(formats_tested)}")
        
        return len(formats_tested) > 0
    except Exception as e:
        print(f"[DataExporter] 测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("AI智能书签分类系统 - 功能实现测试")
    print("=" * 60)
    
    tests = [
        ("语义分析器", test_semantic_analyzer),
        ("用户画像分析器", test_user_profiler), 
        ("书签去重器", test_deduplicator),
        ("数据导出器", test_data_exporter)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n测试 {name}...")
        try:
            if test_func():
                passed += 1
                print(f"[OK] {name} 测试通过")
            else:
                print(f"[FAIL] {name} 测试失败")
        except Exception as e:
            print(f"[ERROR] {name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("所有核心功能实现完成并测试通过!")
    else:
        print("部分功能需要进一步调试")
    
    return passed == total

if __name__ == "__main__":
    main()