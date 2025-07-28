"""
Enhanced Bookmark Classification System - Main Script

This script provides an intelligent bookmark classification system with:
- Advanced ML-based classification
- Semantic similarity matching  
- Adaptive learning from user feedback
- Multi-language support
- Intelligent duplicate detection
- Interactive mode for user feedback

Usage:
    python advanced_clean_tidy.py [OPTIONS]
    python advanced_clean_tidy.py --interactive  # Interactive mode
    python advanced_clean_tidy.py --train  # Train ML models
    python advanced_clean_tidy.py --stats  # Show statistics
"""

import os
import sys
import argparse
import json
import glob
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_classifier import (
    AdvancedBookmarkClassifier,
    ClassificationResult,
    BookmarkFeatures
)
from bs4 import BeautifulSoup
import click

class EnhancedBookmarkProcessor:
    """Enhanced bookmark processor with advanced classification"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.classifier = AdvancedBookmarkClassifier(config_file)
        self.processed_bookmarks = []
        self.statistics = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def process_bookmarks(self, input_files: List[str], interactive: bool = False) -> Dict:
        """Process bookmark files with enhanced classification"""
        self.logger.info(f"Processing {len(input_files)} bookmark files...")
        
        # Load bookmarks from files
        all_bookmarks = self._load_bookmarks(input_files)
        
        if not all_bookmarks:
            self.logger.error("No bookmarks found in input files")
            return {}
        
        self.logger.info(f"Found {len(all_bookmarks)} bookmarks to process")
        
        # Process each bookmark
        results = []
        for i, bookmark in enumerate(all_bookmarks):
            url = bookmark.get('url', '')
            title = bookmark.get('title', '')
            
            if not url or not title:
                continue
            
            # Classify bookmark
            result = self.classifier.classify_bookmark(url, title)
            
            # Store result
            results.append({
                'url': url,
                'title': title,
                'category': result.category,
                'confidence': result.confidence,
                'alternatives': result.alternative_categories,
                'reasoning': result.reasoning
            })
            
            # Interactive mode - ask for feedback
            if interactive and result.confidence < 0.8:
                self._interactive_feedback(url, title, result)
            
            # Progress indicator
            if (i + 1) % 100 == 0:
                self.logger.info(f"Processed {i + 1}/{len(all_bookmarks)} bookmarks")
        
        self.processed_bookmarks = results
        self.statistics = self.classifier.get_statistics()
        
        return self._organize_results(results)
    
    def _load_bookmarks(self, input_files: List[str]) -> List[Dict]:
        """Load bookmarks from HTML files"""
        all_bookmarks = []
        
        for file_path in input_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'lxml')
                links = soup.find_all('a')
                
                for link in links:
                    url = link.get('href', '').strip()
                    title = (link.string or url).strip()
                    
                    if url and title:
                        all_bookmarks.append({
                            'url': url,
                            'title': title,
                            'source_file': file_path
                        })
                
                self.logger.info(f"Loaded {len(links)} bookmarks from {file_path}")
                
            except Exception as e:
                self.logger.error(f"Error loading {file_path}: {e}")
        
        return all_bookmarks
    
    def _interactive_feedback(self, url: str, title: str, result: ClassificationResult):
        """Interactive feedback collection"""
        print(f"\n📌 需要您的反馈:")
        print(f"URL: {url}")
        print(f"标题: {title}")
        print(f"建议分类: {result.category} (置信度: {result.confidence:.2f})")
        
        if result.alternative_categories:
            print("其他选项:")
            for i, (cat, conf) in enumerate(result.alternative_categories[:3]):
                print(f"  {i+1}. {cat} (置信度: {conf:.2f})")
        
        while True:
            choice = input("请选择: [Enter=接受建议] [数字=选择其他] [c=自定义分类]: ").strip()
            
            if not choice:  # Accept suggestion
                break
            elif choice == 'c':  # Custom category
                custom_cat = input("请输入自定义分类: ").strip()
                if custom_cat:
                    self._add_feedback(url, result.category, custom_cat, result.confidence)
                break
            elif choice.isdigit():  # Select alternative
                idx = int(choice) - 1
                if 0 <= idx < len(result.alternative_categories):
                    alt_cat = result.alternative_categories[idx][0]
                    self._add_feedback(url, result.category, alt_cat, result.confidence)
                    break
            
            print("无效选择，请重试")
    
    def _add_feedback(self, url: str, suggested: str, actual: str, confidence: float):
        """Add user feedback to learning system"""
        self.classifier.add_user_feedback(url, suggested, actual, confidence)
        self.logger.info(f"已记录反馈: {suggested} -> {actual}")
    
    def _organize_results(self, results: List[Dict]) -> Dict:
        """Organize results into hierarchical structure"""
        organized = {}
        
        for result in results:
            category = result['category']
            
            # Handle nested categories
            if '/' in category:
                parts = category.split('/')
                current = organized
                
                for i, part in enumerate(parts):
                    if part not in current:
                        current[part] = {} if i < len(parts) - 1 else {'_items': []}
                    current = current[part]
                
                if '_items' not in current:
                    current['_items'] = []
                current['_items'].append({
                    'url': result['url'],
                    'title': result['title'],
                    'confidence': result['confidence']
                })
            else:
                if category not in organized:
                    organized[category] = {'_items': []}
                
                organized[category]['_items'].append({
                    'url': result['url'],
                    'title': result['title'],
                    'confidence': result['confidence']
                })
        
        return organized
    
    def generate_outputs(self, organized_data: Dict, output_dir: str = "tests/output"):
        """Generate HTML output (Markdown 已移除)"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate HTML
        html_file = os.path.join(output_dir, "bookmarks_advanced.html")
        self._generate_html(organized_data, html_file)
        

        # Generate statistics report
        stats_file = os.path.join(output_dir, "classification_stats.json")
        self._generate_stats_report(stats_file)
        
        self.logger.info(f"Generated outputs in {output_dir}")
    
    def _generate_html(self, organized_data: Dict, output_file: str):
        """Generate enhanced HTML with confidence indicators"""
        lines = [
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
            "<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">",
            "<TITLE>智能分类书签 - Advanced Bookmark Classification</TITLE>",
            "<H1>智能分类书签</H1>",
            "<DL><p>"
        ]
        
        def write_category(name: str, data: Dict, indent: int = 1):
            ind = "    " * indent
            timestamp = str(int(datetime.now().timestamp()))
            
            lines.append(f"{ind}<DT><H3 ADD_DATE=\"{timestamp}\">{name}</H3>")
            lines.append(f"{ind}<DL><p>")
            
            # Sort subcategories
            subcats = sorted([k for k in data.keys() if k != '_items'])
            for subcat in subcats:
                write_category(subcat, data[subcat], indent + 1)
            
            # Add bookmarks
            if '_items' in data:
                items = data['_items']
                # Sort by confidence (highest first)
                items.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                
                for item in items:
                    confidence = item.get('confidence', 0)

                    # Check if confidence indicators should be shown
                    show_indicators = self.config.get('advanced_settings', {}).get('show_confidence_indicators', False)

                    if show_indicators:
                        conf_indicator = "🔥" if confidence > 0.8 else "📌" if confidence > 0.6 else "❓"
                        title_with_conf = f"{conf_indicator} {item['title']}"
                    else:
                        title_with_conf = item['title']

                    lines.append(f"{ind}    <DT><A HREF=\"{item['url']}\" ADD_DATE=\"{timestamp}\">{title_with_conf}</A>")
            
            lines.append(f"{ind}</DL><p>")
        
        # Process categories in order
        for category in sorted(organized_data.keys()):
            write_category(category, organized_data[category])
        
        lines.append("</DL><p>")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _generate_markdown(self, organized_data: Dict, output_file: str):
        """Generate enhanced Markdown with statistics"""
        lines = [
            "# 🚀 智能书签分类报告",
            f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## 📊 分类统计",
            f"- 总书签数: {len(self.processed_bookmarks)}",
            f"- 平均置信度: {self.statistics.get('average_confidence', 0):.2f}",
            f"- 分类准确率: {self.statistics.get('accuracy', 0):.2f}",
            ""
        ]
        
        def write_category(name: str, data: Dict, level: int = 2):
            prefix = "#" * min(level, 6)
            lines.append(f"{prefix} {name}")
            lines.append("")
            
            # Subcategories
            subcats = sorted([k for k in data.keys() if k != '_items'])
            for subcat in subcats:
                write_category(subcat, data[subcat], level + 1)
            
            # Items
            if '_items' in data:
                items = data['_items']
                items.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                
                for item in items:
                    confidence = item.get('confidence', 0)

                    # Check if confidence indicators should be shown
                    show_indicators = self.config.get('advanced_settings', {}).get('show_confidence_indicators', False)

                    if show_indicators:
                        conf_emoji = "🔥" if confidence > 0.8 else "📌" if confidence > 0.6 else "❓"
                        lines.append(f"- {conf_emoji} [{item['title']}]({item['url']}) *({confidence:.2f})*")
                    else:
                        lines.append(f"- [{item['title']}]({item['url']})")
                
                lines.append("")
        
        # Process categories
        for category in sorted(organized_data.keys()):
            write_category(category, organized_data[category])
        
        # Add statistics section
        lines.extend([
            "## 📈 详细统计",
            "### 分类分布",
            ""
        ])
        
        for category, count in self.statistics.get('category_distribution', {}).items():
            lines.append(f"- {category}: {count}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _generate_stats_report(self, output_file: str):
        """Generate detailed statistics report"""
        report = {
            "generation_time": datetime.now().isoformat(),
            "total_bookmarks": len(self.processed_bookmarks),
            "classification_stats": self.statistics,
            "top_categories": dict(self.statistics.get('category_distribution', {}).most_common(10)),
            "low_confidence_items": [
                {"url": item['url'], "title": item['title'], "confidence": item['confidence']}
                for item in self.processed_bookmarks
                if item['confidence'] < 0.5
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(
        description="高级书签分类系统 - 基于机器学习的智能书签整理工具",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '-i', '--input', nargs='+', default=[],
        help='输入的HTML书签文件路径'
    )
    parser.add_argument(
        '-c', '--config', default='config.json',
        help='配置文件路径'
    )
    parser.add_argument(
        '-o', '--output', default='tests/output',
        help='输出目录'
    )
    parser.add_argument(
        '--interactive', action='store_true',
        help='启用交互模式收集用户反馈'
    )
    parser.add_argument(
        '--train', action='store_true',
        help='训练机器学习模型'
    )
    parser.add_argument(
        '--stats', action='store_true',
        help='显示分类统计信息'
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = EnhancedBookmarkProcessor(args.config)
    
    # Handle different modes
    if args.train:
        print("🎯 训练模式暂未实现 - 请使用交互模式提供反馈来改进分类")
        return
    
    if args.stats:
        stats = processor.classifier.get_statistics()
        print("\n📊 分类统计:")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        return
    
    # Get input files
    input_files = args.input if args.input else glob.glob('tests/input/*.html')
    
    if not input_files:
        if os.path.exists('bookmarks_2025_7_1.html'):
            input_files = ['bookmarks_2025_7_1.html']
        else:
            print("❌ 错误: 未找到输入文件")
            return
    
    print(f"🚀 开始处理书签文件: {input_files}")
    
    # Process bookmarks
    organized_data = processor.process_bookmarks(input_files, args.interactive)
    
    if not organized_data:
        print("❌ 处理失败")
        return
    
    # Generate outputs
    processor.generate_outputs(organized_data, args.output)
    
    # Show summary
    stats = processor.statistics
    print(f"\n✅ 处理完成!")
    print(f"📈 总计: {stats.get('total_classified', 0)} 个书签")
    print(f"🎯 平均置信度: {stats.get('average_confidence', 0):.2f}")
    print(f"📊 分类准确率: {stats.get('accuracy', 0):.2f}")
    print(f"💾 输出保存至: {args.output}")

if __name__ == "__main__":
    main()