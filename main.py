"""
AI Bookmark Classifier - Main Entry Point
AI智能书签分类器 - 主入口

这是新一代基于AI的智能书签分类系统的主入口文件。
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_classifier import AIBookmarkClassifier
from src.bookmark_processor import BookmarkProcessor
from src.cli_interface import CLIInterface

def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    os.makedirs("logs", exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/ai_classifier.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI智能书签分类系统 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --interactive                    # 启动交互模式
  %(prog)s -i bookmarks.html               # 处理单个文件
  %(prog)s -i tests/input/*.html --train   # 批量处理并训练模型
  %(prog)s --health-check                  # 运行健康检查
        """
    )
    
    # 基本参数
    parser.add_argument('-i', '--input', nargs='+', help='输入的HTML书签文件')
    parser.add_argument('-o', '--output', default='output', help='输出目录')
    parser.add_argument('-c', '--config', default='config.json', help='配置文件路径')
    
    # 模式选择
    parser.add_argument('--interactive', action='store_true', help='启动交互模式')
    parser.add_argument('--train', action='store_true', help='训练机器学习模型')
    parser.add_argument('--health-check', action='store_true', help='运行健康检查')
    
    # 高级选项
    parser.add_argument('--workers', type=int, default=4, help='并行处理线程数')
    parser.add_argument('--threshold', type=float, default=0.7, help='分类置信度阈值')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--no-ml', action='store_true', help='禁用机器学习功能')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        if args.interactive:
            # 交互模式
            cli = CLIInterface()
            cli.run()
        elif args.health_check:
            # 健康检查模式
            from src.health_checker import run_health_check
            run_health_check()
        elif args.input:
            # 批处理模式
            processor = BookmarkProcessor(
                config_path=args.config,
                max_workers=args.workers,
                use_ml=not args.no_ml
            )
            
            results = processor.process_files(
                input_files=args.input,
                output_dir=args.output,
                train_models=args.train
            )
            
            logger.info(f"处理完成: {results['processed_count']} 个书签已分类")
        else:
            # 显示帮助
            parser.print_help()
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        if args.log_level == 'DEBUG':
            raise
        sys.exit(1)

if __name__ == "__main__":
    main()