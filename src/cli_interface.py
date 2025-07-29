"""
CLI Interface - 交互式命令行界面

提供现代化的交互式用户界面
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.tree import Tree
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("警告: rich库未安装，将使用基础CLI界面")

from .bookmark_processor import BookmarkProcessor
from .ai_classifier import AIBookmarkClassifier

class CLIInterface:
    """CLI交互界面"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.processor = None
        self.classifier = None
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """运行交互界面"""
        self._print_welcome()
        
        try:
            while True:
                choice = self._show_main_menu()
                
                if choice == 'q':
                    break
                elif choice == '1':
                    self._process_bookmarks()
                elif choice == '2':
                    self._view_results()
                elif choice == '3':
                    self._manage_models()
                elif choice == '4':
                    self._health_check()
                elif choice == '5':
                    self._show_statistics()
                elif choice == '6':
                    self._settings()
                elif choice == 'h':
                    self._show_help()
                
                if choice != 'q':
                    self._pause()
        
        except KeyboardInterrupt:
            self._info("程序被用户中断")
        except Exception as e:
            self._error(f"程序执行出错: {e}")
        finally:
            self._info("感谢使用AI智能书签分类系统!")
    
    def _print_welcome(self):
        """打印欢迎信息"""
        welcome_text = """
🚀 AI智能书签分类系统 v2.0

基于人工智能的下一代书签管理工具
- 🧠 AI智能分类算法
- ⚡ 高性能并行处理  
- 🎯 个性化推荐系统
- 🔍 智能去重检测
- 📊 详细统计分析
        """
        
        if RICH_AVAILABLE:
            panel = Panel(welcome_text.strip(), border_style="blue", title="欢迎")
            self.console.print(panel)
        else:
            print("=" * 50)
            print(welcome_text.strip())
            print("=" * 50)
    
    def _show_main_menu(self) -> str:
        """显示主菜单"""
        options = {
            '1': '📂 处理书签文件',
            '2': '📊 查看处理结果', 
            '3': '🤖 模型管理',
            '4': '🏥 健康检查',
            '5': '📈 统计分析',
            '6': '⚙️ 设置',
            'h': '❓ 帮助',
            'q': '🚪 退出'
        }
        
        if RICH_AVAILABLE:
            self.console.print("\n[bold cyan]主菜单[/bold cyan]")
            for key, desc in options.items():
                self.console.print(f"  [green]{key}[/green]: {desc}")
            
            return Prompt.ask("请选择操作", choices=list(options.keys()), show_choices=False)
        else:
            print("\n主菜单:")
            for key, desc in options.items():
                print(f"  {key}: {desc}")
            
            while True:
                choice = input("请选择操作: ").strip().lower()
                if choice in options:
                    return choice
                print("无效选择，请重试")
    
    def _process_bookmarks(self):
        """处理书签文件"""
        self._info("书签处理")
        
        # 选择输入文件
        input_files = self._select_input_files()
        if not input_files:
            self._warning("没有选择输入文件")
            return
        
        # 选择输出目录
        output_dir = self._get_output_directory()
        
        # 处理选项
        use_ml = self._confirm("是否启用机器学习分类?", default=True)
        train_models = self._confirm("是否训练模型?", default=False) if use_ml else False
        workers = self._get_worker_count()
        
        # 初始化处理器
        self.processor = BookmarkProcessor(
            max_workers=workers,
            use_ml=use_ml
        )
        
        # 开始处理
        self._info(f"开始处理 {len(input_files)} 个文件...")
        
        try:
            if RICH_AVAILABLE:
                with Progress(
                    TextColumn("[bold blue]处理进度"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%",
                    TimeRemainingColumn(),
                    console=self.console
                ) as progress:
                    task = progress.add_task("处理中...", total=100)
                    
                    # 这里应该有实际的进度更新逻辑
                    import time
                    for i in range(100):
                        time.sleep(0.02)  # 模拟处理
                        progress.update(task, advance=1)
            
            stats = self.processor.process_files(
                input_files=input_files,
                output_dir=output_dir,
                train_models=train_models
            )
            
            self._show_processing_results(stats)
            
        except Exception as e:
            self._error(f"处理失败: {e}")
    
    def _select_input_files(self) -> List[str]:
        """选择输入文件"""
        input_dir = "tests/input"
        
        if not os.path.exists(input_dir):
            self._warning(f"输入目录 {input_dir} 不存在")
            return []
        
        html_files = [f for f in os.listdir(input_dir) if f.endswith('.html')]
        
        if not html_files:
            self._warning(f"在 {input_dir} 中没有找到HTML文件")
            return []
        
        self._info(f"找到 {len(html_files)} 个HTML文件:")
        
        selected_files = []
        for file in html_files:
            if self._confirm(f"处理文件 {file}?", default=True):
                selected_files.append(os.path.join(input_dir, file))
        
        return selected_files
    
    def _get_output_directory(self) -> str:
        """获取输出目录"""
        if RICH_AVAILABLE:
            return Prompt.ask("输出目录", default="output")
        else:
            output = input("输出目录 (默认: output): ").strip()
            return output if output else "output"
    
    def _get_worker_count(self) -> int:
        """获取工作线程数"""
        if RICH_AVAILABLE:
            return int(Prompt.ask("并行线程数", default="4"))
        else:
            while True:
                try:
                    count = input("并行线程数 (默认: 4): ").strip()
                    return int(count) if count else 4
                except ValueError:
                    print("请输入有效数字")
    
    def _show_processing_results(self, stats: Dict):
        """显示处理结果"""
        if RICH_AVAILABLE:
            table = Table(title="处理结果统计", border_style="green")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="yellow")
            
            metrics = [
                ("总书签数", stats['total_bookmarks']),
                ("成功处理", stats['processed_bookmarks']), 
                ("去除重复", stats['duplicates_removed']),
                ("处理错误", stats['errors']),
                ("处理时间", f"{stats['processing_time']:.2f}秒"),
                ("处理速度", f"{stats.get('processing_speed', 0):.1f} 书签/秒")
            ]
            
            for metric, value in metrics:
                table.add_row(metric, str(value))
            
            self.console.print(table)
        else:
            print("\n处理结果统计:")
            print(f"  总书签数: {stats['total_bookmarks']}")
            print(f"  成功处理: {stats['processed_bookmarks']}")
            print(f"  去除重复: {stats['duplicates_removed']}")
            print(f"  处理错误: {stats['errors']}")
            print(f"  处理时间: {stats['processing_time']:.2f}秒")
    
    def _view_results(self):
        """查看处理结果"""
        self._info("查看处理结果")
        
        output_dir = "output"
        if not os.path.exists(output_dir):
            self._warning("没有找到输出目录")
            return
        
        files = [f for f in os.listdir(output_dir) if f.endswith(('.html', '.json', '.md'))]
        if not files:
            self._warning("没有找到结果文件")
            return
        
        # 显示文件列表
        self._info("可用的结果文件:")
        for i, file in enumerate(files, 1):
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            print(f"  {i}. {file} ({size} 字节)")
        
        # 选择文件查看
        try:
            if RICH_AVAILABLE:
                choice = int(Prompt.ask(f"选择文件 (1-{len(files)})", default="1"))
            else:
                choice = int(input(f"选择文件 (1-{len(files)}): ") or "1")
            
            if 1 <= choice <= len(files):
                selected_file = files[choice - 1]
                self._view_file_content(os.path.join(output_dir, selected_file))
        except ValueError:
            self._error("无效的选择")
    
    def _view_file_content(self, file_path: str):
        """查看文件内容"""
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'statistics' in data:
                    self._show_json_statistics(data['statistics'])
                else:
                    print("JSON内容预览:")
                    print(json.dumps(data, ensure_ascii=False, indent=2)[:1000] + "...")
            
            elif file_path.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print("Markdown内容预览:")
                print(content[:1000] + "..." if len(content) > 1000 else content)
            
            else:
                self._info(f"文件路径: {file_path}")
                self._info(f"文件大小: {os.path.getsize(file_path)} 字节")
                
        except Exception as e:
            self._error(f"读取文件失败: {e}")
    
    def _show_json_statistics(self, stats: Dict):
        """显示JSON统计信息"""
        if RICH_AVAILABLE:
            table = Table(title="统计信息", border_style="blue")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="yellow")
            
            for key, value in stats.items():
                if isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=False)
                table.add_row(key.replace('_', ' ').title(), str(value))
            
            self.console.print(table)
        else:
            print("统计信息:")
            for key, value in stats.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
    
    def _manage_models(self):
        """管理AI模型"""
        self._info("AI模型管理")
        
        model_options = {
            '1': '📊 查看模型状态',
            '2': '💾 保存当前模型',
            '3': '📂 加载已保存模型',
            '4': '🎯 重新训练模型',
            '5': '🧹 清理模型缓存'
        }
        
        choice = self._show_menu(model_options, "模型管理菜单")
        
        if choice == '1':
            self._show_model_status()
        elif choice == '2':
            self._save_model()
        elif choice == '3':
            self._load_model()
        elif choice == '4':
            self._retrain_model()
        elif choice == '5':
            self._clear_model_cache()
    
    def _health_check(self):
        """健康检查"""
        self._info("书签健康检查")
        self._warning("此功能需要网络连接，可能需要较长时间")
        
        if not self._confirm("继续进行健康检查?"):
            return
        
        # 这里应该实现实际的健康检查逻辑
        self._info("健康检查功能开发中...")
    
    def _show_statistics(self):
        """显示统计信息"""
        self._info("系统统计信息")
        
        if self.processor:
            stats = self.processor.get_statistics()
            self._show_processing_results(stats)
        else:
            self._warning("尚未处理任何书签文件")
    
    def _settings(self):
        """设置管理"""
        self._info("系统设置")
        
        settings_options = {
            '1': '📝 查看当前配置',
            '2': '✏️ 修改配置',
            '3': '🔄 重载配置',
            '4': '💾 导出配置'
        }
        
        choice = self._show_menu(settings_options, "设置菜单")
        
        if choice == '1':
            self._show_current_config()
        elif choice == '2':
            self._modify_config()
        elif choice == '3':
            self._reload_config()
        elif choice == '4':
            self._export_config()
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
🚀 AI智能书签分类系统帮助

主要功能:
📂 处理书签文件 - 批量处理浏览器导出的书签
📊 查看处理结果 - 查看分类结果和统计报告
🤖 模型管理 - 管理AI分类模型
🏥 健康检查 - 检查书签链接有效性
📈 统计分析 - 查看详细处理统计
⚙️ 设置 - 管理系统配置

使用流程:
1. 将浏览器导出的书签文件放在 tests/input/ 目录
2. 选择"处理书签文件"开始智能分类
3. 查看生成的HTML、JSON、Markdown结果文件
4. 根据需要调整配置和重新训练模型

更多信息请查看项目文档。
        """
        
        if RICH_AVAILABLE:
            panel = Panel(help_text.strip(), title="帮助信息", border_style="green")
            self.console.print(panel)
        else:
            print(help_text)
    
    # 辅助方法
    def _show_menu(self, options: Dict[str, str], title: str) -> str:
        """显示菜单并获取选择"""
        if RICH_AVAILABLE:
            self.console.print(f"\n[bold magenta]{title}[/bold magenta]")
            for key, desc in options.items():
                self.console.print(f"  [green]{key}[/green]: {desc}")
            
            return Prompt.ask("请选择", choices=list(options.keys()), show_choices=False)
        else:
            print(f"\n{title}:")
            for key, desc in options.items():
                print(f"  {key}: {desc}")
            
            while True:
                choice = input("请选择: ").strip()
                if choice in options:
                    return choice
                print("无效选择，请重试")
    
    def _confirm(self, question: str, default: bool = True) -> bool:
        """确认对话"""
        if RICH_AVAILABLE:
            return Confirm.ask(question, default=default)
        else:
            default_text = "Y/n" if default else "y/N"
            response = input(f"{question} [{default_text}]: ").strip().lower()
            
            if not response:
                return default
            
            return response in ['y', 'yes', '是', 'true', '1']
    
    def _info(self, message: str):
        """信息消息"""
        if RICH_AVAILABLE:
            self.console.print(f"ℹ️  [blue]{message}[/blue]")
        else:
            print(f"ℹ️  {message}")
    
    def _warning(self, message: str):
        """警告消息"""
        if RICH_AVAILABLE:
            self.console.print(f"⚠️  [yellow]{message}[/yellow]")
        else:
            print(f"⚠️  {message}")
    
    def _error(self, message: str):
        """错误消息"""
        if RICH_AVAILABLE:
            self.console.print(f"❌ [red]{message}[/red]")
        else:
            print(f"❌ {message}")
    
    def _success(self, message: str):
        """成功消息"""
        if RICH_AVAILABLE:
            self.console.print(f"✅ [green]{message}[/green]")
        else:
            print(f"✅ {message}")
    
    def _pause(self):
        """暂停等待用户输入"""
        input("\n按Enter继续...")
    
    # 占位符方法 - 待实现
    def _show_model_status(self):
        self._info("模型状态查看功能开发中...")
    
    def _save_model(self):
        self._info("模型保存功能开发中...")
    
    def _load_model(self):
        self._info("模型加载功能开发中...")
    
    def _retrain_model(self):
        self._info("模型重训练功能开发中...")
    
    def _clear_model_cache(self):
        self._info("缓存清理功能开发中...")
    
    def _show_current_config(self):
        self._info("配置查看功能开发中...")
    
    def _modify_config(self):
        self._info("配置修改功能开发中...")
    
    def _reload_config(self):
        self._info("配置重载功能开发中...")
    
    def _export_config(self):
        self._info("配置导出功能开发中...")