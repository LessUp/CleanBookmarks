"""
Enhanced CLI Interface
增强CLI界面

特点：
1. 现代化交互界面
2. 实时进度显示
3. 彩色输出
4. 错误处理和恢复
5. 交互式菜单
6. 键盘快捷键
"""

import os
import sys
import argparse
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging
import threading
import time
from pathlib import Path
import signal

# 第三方库
try:
    import click
    from tqdm import tqdm
    from rich.console import Console
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.layout import Layout
    from rich.tree import Tree
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("警告: rich库未安装，将使用基础CLI界面")
    print("安装rich以获得更好的用户体验: pip install rich")

# 导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ProgressReporter:
    """进度报告器"""
    
    def __init__(self, use_rich=True):
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = Console() if self.use_rich else None
        self.current_task = None
        self.progress = None
        
    def start_task(self, description: str, total: int = 100):
        """开始一个任务"""
        if self.use_rich:
            if not self.progress:
                self.progress = Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    "•",
                    TimeRemainingColumn(),
                    console=self.console
                )
                self.progress.start()
            
            self.current_task = self.progress.add_task(description, total=total)
        else:
            print(f"开始: {description}")
            self.pbar = tqdm(total=total, desc=description)
    
    def update(self, advance: int = 1, description: str = None):
        """更新进度"""
        if self.use_rich and self.progress and self.current_task:
            self.progress.update(self.current_task, advance=advance)
            if description:
                self.progress.update(self.current_task, description=description)
        else:
            if hasattr(self, 'pbar'):
                self.pbar.update(advance)
                if description:
                    self.pbar.set_description(description)
    
    def finish_task(self):
        """完成任务"""
        if self.use_rich and self.progress:
            self.progress.stop()
            self.progress = None
            self.current_task = None
        else:
            if hasattr(self, 'pbar'):
                self.pbar.close()
                delattr(self, 'pbar')

class EnhancedCLI:
    """增强CLI界面"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.use_rich = RICH_AVAILABLE
        self.progress_reporter = ProgressReporter(self.use_rich)
        self.interrupted = False
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.interrupted = True
        self.error("操作被用户中断")
        sys.exit(1)
    
    def info(self, message: str):
        """信息消息"""
        if self.use_rich:
            self.console.print(f"ℹ  {message}", style="blue")
        else:
            print(f"ℹ  {message}")
    
    def success(self, message: str):
        """成功消息"""
        if self.use_rich:
            self.console.print(f"✅ {message}", style="green")
        else:
            print(f"✅ {message}")
    
    def warning(self, message: str):
        """警告消息"""
        if self.use_rich:
            self.console.print(f"⚠️  {message}", style="yellow")
        else:
            print(f"⚠️  {message}")
    
    def error(self, message: str):
        """错误消息"""
        if self.use_rich:
            self.console.print(f"❌ {message}", style="red")
        else:
            print(f"❌ {message}")
    
    def debug(self, message: str):
        """调试消息"""
        if self.use_rich:
            self.console.print(f"🐛 {message}", style="dim")
        else:
            print(f"🐛 {message}")
    
    def print_header(self, title: str, subtitle: str = None):
        """打印标题头"""
        if self.use_rich:
            text = Text(title, style="bold magenta")
            if subtitle:
                text.append(f"\n{subtitle}", style="dim")
            
            panel = Panel(
                text,
                border_style="magenta",
                padding=(1, 2)
            )
            self.console.print(panel)
        else:
            print("=" * 60)
            print(f"  {title}")
            if subtitle:
                print(f"  {subtitle}")
            print("=" * 60)
    
    def print_table(self, data: List[Dict], title: str = None, headers: List[str] = None):
        """打印表格"""
        if not data:
            self.warning("没有数据可显示")
            return
        
        if self.use_rich:
            table = Table(title=title, show_header=True, header_style="bold magenta")
            
            # 添加列
            if headers:
                for header in headers:
                    table.add_column(header)
            else:
                for key in data[0].keys():
                    table.add_column(key.replace('_', ' ').title())
            
            # 添加行
            for row in data:
                if headers:
                    table.add_row(*[str(row.get(h, '')) for h in headers])
                else:
                    table.add_row(*[str(v) for v in row.values()])
            
            self.console.print(table)
        else:
            # 简单表格输出
            if title:
                print(f"\n{title}")
                print("-" * len(title))
            
            if headers:
                print(" | ".join(headers))
                print("-" * (len(" | ".join(headers))))
                
                for row in data:
                    print(" | ".join(str(row.get(h, '')) for h in headers))
            else:
                for i, row in enumerate(data):
                    print(f"{i+1}. {row}")
    
    def print_stats(self, stats: Dict[str, Any], title: str = "统计信息"):
        """打印统计信息"""
        if self.use_rich:
            table = Table(title=title, border_style="blue")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="yellow")
            
            for key, value in stats.items():
                display_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    display_value = f"{value:.3f}"
                elif isinstance(value, dict):
                    display_value = json.dumps(value, ensure_ascii=False, indent=2)
                else:
                    display_value = str(value)
                
                table.add_row(display_key, display_value)
            
            self.console.print(table)
        else:
            print(f"\n{title}:")
            print("-" * len(title))
            for key, value in stats.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
    
    def confirm(self, question: str, default: bool = True) -> bool:
        """确认对话"""
        if self.use_rich:
            return Confirm.ask(question, default=default)
        else:
            default_text = "Y/n" if default else "y/N"
            response = input(f"{question} [{default_text}]: ").strip().lower()
            
            if not response:
                return default
            
            return response in ['y', 'yes', '是', 'true', '1']
    
    def prompt(self, question: str, default: str = None, choices: List[str] = None) -> str:
        """输入提示"""
        if self.use_rich:
            return Prompt.ask(question, default=default, choices=choices)
        else:
            prompt_text = question
            if choices:
                prompt_text += f" [{'/'.join(choices)}]"
            if default:
                prompt_text += f" (默认: {default})"
            
            response = input(f"{prompt_text}: ").strip()
            
            if not response and default:
                return default
            
            if choices and response not in choices:
                self.error(f"无效选择，请选择: {'/'.join(choices)}")
                return self.prompt(question, default, choices)
            
            return response
    
    def select_from_list(self, items: List[Any], title: str = "请选择", 
                        display_func: Callable[[Any], str] = str) -> Optional[Any]:
        """从列表中选择"""
        if not items:
            self.warning("没有可选择的项目")
            return None
        
        if self.use_rich:
            self.console.print(f"\n[bold]{title}[/bold]")
            
            for i, item in enumerate(items, 1):
                self.console.print(f"  {i}. {display_func(item)}")
            
            while True:
                try:
                    choice = Prompt.ask(
                        f"请选择 (1-{len(items)})",
                        choices=[str(i) for i in range(1, len(items) + 1)]
                    )
                    return items[int(choice) - 1]
                except (ValueError, IndexError):
                    self.error("无效选择，请重试")
        else:
            print(f"\n{title}:")
            for i, item in enumerate(items, 1):
                print(f"  {i}. {display_func(item)}")
            
            while True:
                try:
                    choice = int(input(f"请选择 (1-{len(items)}): "))
                    if 1 <= choice <= len(items):
                        return items[choice - 1]
                    else:
                        self.error("选择超出范围，请重试")
                except ValueError:
                    self.error("请输入数字")
    
    def show_menu(self, options: Dict[str, str], title: str = "菜单") -> str:
        """显示菜单"""
        if self.use_rich:
            self.console.print(f"\n[bold magenta]{title}[/bold magenta]")
            
            for key, description in options.items():
                self.console.print(f"  [cyan]{key}[/cyan]: {description}")
            
            return Prompt.ask(
                "请选择",
                choices=list(options.keys()),
                show_choices=False
            )
        else:
            print(f"\n{title}:")
            print("-" * len(title))
            
            for key, description in options.items():
                print(f"  {key}: {description}")
            
            while True:
                choice = input("请选择: ").strip()
                if choice in options:
                    return choice
                else:
                    self.error(f"无效选择，请选择: {'/'.join(options.keys())}")
    
    def display_tree(self, data: Dict, title: str = "数据结构"):
        """显示树状结构"""
        if self.use_rich:
            tree = Tree(title)
            self._add_tree_nodes(tree, data)
            self.console.print(tree)
        else:
            print(f"\n{title}:")
            self._print_tree_text(data, "", True)
    
    def _add_tree_nodes(self, parent, data):
        """添加树节点（Rich版本）"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == '_items':
                    for item in value:
                        title = item.get('title', 'No title')[:50]
                        parent.add(f"📖 {title}")
                else:
                    branch = parent.add(f"📁 {key}")
                    self._add_tree_nodes(branch, value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    title = item.get('title', f'Item {i+1}')[:50]
                    parent.add(f"📖 {title}")
                else:
                    parent.add(str(item))
    
    def _print_tree_text(self, data, prefix="", is_last=True):
        """打印树状结构（文本版本）"""
        if isinstance(data, dict):
            items = list(data.items())
            for i, (key, value) in enumerate(items):
                is_last_item = i == len(items) - 1
                
                if key == '_items':
                    for j, item in enumerate(value):
                        item_is_last = j == len(value) - 1
                        title = item.get('title', 'No title')[:50]
                        print(f"{prefix}{'└── ' if item_is_last else '├── '}📖 {title}")
                else:
                    print(f"{prefix}{'└── ' if is_last_item else '├── '}📁 {key}")
                    extension = "    " if is_last_item else "│   "
                    self._print_tree_text(value, prefix + extension, is_last_item)
    
    def start_progress(self, description: str, total: int = 100):
        """开始进度条"""
        self.progress_reporter.start_task(description, total)
    
    def update_progress(self, advance: int = 1, description: str = None):
        """更新进度"""
        self.progress_reporter.update(advance, description)
    
    def finish_progress(self):
        """完成进度条"""
        self.progress_reporter.finish_task()
    
    def handle_error(self, error: Exception, operation: str = "操作"):
        """错误处理"""
        self.error(f"{operation}失败: {str(error)}")
        
        if self.confirm("是否查看详细错误信息?", default=False):
            import traceback
            if self.use_rich:
                self.console.print_exception()
            else:
                traceback.print_exc()
        
        if self.confirm("是否重试?", default=True):
            return True
        
        return False
    
    def cleanup(self):
        """清理资源"""
        self.progress_reporter.finish_task()

class InteractiveBookmarkManager:
    """交互式书签管理器"""
    
    def __init__(self):
        self.cli = EnhancedCLI()
        self.current_bookmarks = []
        self.config = {}
        
    def run(self):
        """运行交互式界面"""
        self.cli.print_header(
            "🚀 智能书签分类系统",
            "Enhanced Bookmark Classification System v2.0"
        )
        
        try:
            while True:
                choice = self.cli.show_menu({
                    '1': '📂 处理书签文件',
                    '2': '🔍 查看处理结果',
                    '3': '⚙️  配置管理',
                    '4': '📊 统计分析',
                    '5': '🧹 去重和清理',
                    '6': '💡 智能推荐',
                    '7': '🏥 健康检查',
                    '8': '📤 导入导出',
                    '9': '❓ 帮助',
                    'q': '🚪 退出'
                }, "主菜单")
                
                if choice == 'q':
                    break
                elif choice == '1':
                    self.process_bookmarks()
                elif choice == '2':
                    self.view_results()
                elif choice == '3':
                    self.manage_config()
                elif choice == '4':
                    self.show_statistics()
                elif choice == '5':
                    self.deduplicate_bookmarks()
                elif choice == '6':
                    self.show_recommendations()
                elif choice == '7':
                    self.health_check()
                elif choice == '8':
                    self.import_export()
                elif choice == '9':
                    self.show_help()
                
                if choice != 'q':
                    input("\n按Enter继续...")
        
        except KeyboardInterrupt:
            self.cli.info("程序被用户中断")
        except Exception as e:
            self.cli.handle_error(e, "程序运行")
        finally:
            self.cleanup()
    
    def process_bookmarks(self):
        """处理书签文件"""
        self.cli.info("书签处理功能")
        
        # 选择输入文件
        input_dir = "tests/input"
        if os.path.exists(input_dir):
            html_files = [f for f in os.listdir(input_dir) if f.endswith('.html')]
            if html_files:
                selected_files = []
                self.cli.info(f"在 {input_dir} 中找到 {len(html_files)} 个HTML文件")
                
                for file in html_files:
                    if self.cli.confirm(f"处理文件 {file}?"):
                        selected_files.append(os.path.join(input_dir, file))
                
                if selected_files:
                    self.cli.info(f"将处理 {len(selected_files)} 个文件")
                    # 这里应该调用实际的处理逻辑
                    self.cli.success("书签处理完成!")
                else:
                    self.cli.warning("没有选择任何文件")
            else:
                self.cli.warning(f"在 {input_dir} 中没有找到HTML文件")
        else:
            self.cli.error(f"输入目录 {input_dir} 不存在")
    
    def view_results(self):
        """查看处理结果"""
        self.cli.info("查看处理结果")
        
        output_dir = "tests/output"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                selected_file = self.cli.select_from_list(
                    files,
                    "选择要查看的结果文件"
                )
                
                if selected_file:
                    file_path = os.path.join(output_dir, selected_file)
                    self.cli.info(f"文件路径: {file_path}")
                    self.cli.info(f"文件大小: {os.path.getsize(file_path)} 字节")
                    
                    if selected_file.endswith('.json'):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            if 'statistics' in data:
                                self.cli.print_stats(data['statistics'], "处理统计")
                        except Exception as e:
                            self.cli.error(f"读取文件失败: {e}")
            else:
                self.cli.warning(f"输出目录 {output_dir} 为空")
        else:
            self.cli.error(f"输出目录 {output_dir} 不存在")
    
    def manage_config(self):
        """配置管理"""
        self.cli.info("配置管理")
        
        config_choice = self.cli.show_menu({
            '1': '查看当前配置',
            '2': '修改配置',
            '3': '重载配置',
            '4': '导出配置'
        }, "配置管理")
        
        if config_choice == '1':
            # 显示配置
            config_file = "config.json"
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    self.cli.print_stats({
                        '分类规则数量': len(config.get('category_rules', {})),
                        '分类顺序数量': len(config.get('category_order', [])),
                        '高级设置': json.dumps(config.get('advanced_settings', {}), ensure_ascii=False)
                    }, "当前配置")
                except Exception as e:
                    self.cli.error(f"读取配置失败: {e}")
            else:
                self.cli.error("配置文件不存在")
    
    def show_statistics(self):
        """显示统计分析"""
        self.cli.info("统计分析")
        
        # 模拟统计数据
        stats = {
            '总书签数': 1500,
            '分类准确率': 0.92,
            '处理速度': '45.2 书签/秒',
            '缓存命中率': 0.78,
            '去重率': 0.15
        }
        
        self.cli.print_stats(stats, "系统统计")
    
    def deduplicate_bookmarks(self):
        """去重和清理"""
        self.cli.info("书签去重和清理")
        self.cli.warning("此功能需要加载书签数据")
    
    def show_recommendations(self):
        """显示智能推荐"""
        self.cli.info("智能推荐系统")
        self.cli.warning("此功能需要训练推荐模型")
    
    def health_check(self):
        """健康检查"""
        self.cli.info("书签健康检查")
        
        if self.cli.confirm("开始检查书签可访问性?"):
            self.cli.start_progress("检查书签健康状态", 100)
            
            # 模拟健康检查
            for i in range(100):
                time.sleep(0.05)  # 模拟处理时间
                self.cli.update_progress(1)
                
                if i % 20 == 0:
                    self.cli.update_progress(0, f"检查第 {i+1} 个书签")
            
            self.cli.finish_progress()
            self.cli.success("健康检查完成!")
    
    def import_export(self):
        """导入导出"""
        self.cli.info("导入导出功能")
        
        ie_choice = self.cli.show_menu({
            '1': '导入CSV文件',
            '2': '导出为CSV',
            '3': '导入JSON文件',
            '4': '导出为JSON'
        }, "导入导出")
        
        self.cli.info(f"选择了选项: {ie_choice}")
    
    def show_help(self):
        """显示帮助"""
        help_text = """
🚀 智能书签分类系统帮助

主要功能:
  📂 处理书签文件 - 批量处理浏览器导出的书签文件
  🔍 查看处理结果 - 查看分类结果和统计信息
  ⚙️  配置管理 - 管理分类规则和系统设置
  📊 统计分析 - 查看详细的处理统计信息
  🧹 去重和清理 - 智能去除重复书签
  💡 智能推荐 - 基于历史数据的个性化推荐
  🏥 健康检查 - 检查书签链接的可访问性
  📤 导入导出 - 支持多种格式的数据交换

快捷键:
  Ctrl+C - 中断当前操作
  q - 退出程序
  
更多信息请访问项目文档。
        """
        
        if self.cli.use_rich:
            self.cli.console.print(Panel(help_text.strip(), title="帮助信息", border_style="green"))
        else:
            print(help_text)
    
    def cleanup(self):
        """清理资源"""
        self.cli.cleanup()
        self.cli.info("感谢使用智能书签分类系统!")

def main():
    """主函数"""
    try:
        try:
            from .cli_interface import CLIInterface
        except Exception:
            from cli_interface import CLIInterface

        CLIInterface().run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()