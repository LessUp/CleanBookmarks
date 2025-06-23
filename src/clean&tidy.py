"""
一个用于清理和分类浏览器书签的 Python 脚本。

该脚本会读取一个 HTML 格式的书签文件，根据预定义的规则对书签进行分类和去重，
然后生成一个清理过的、可重新导入浏览器的 HTML 文件，以及一个 Markdown 格式的纯链接列表。

主要功能：
- 基于关键词对书签进行多级分类。
- 自动为特定分类（如 GitHub）创建更深层次的目录结构。
- 清理 URL，去除跟踪参数。
- 对清理后的 URL进行去重。
- 支持命令行参数，可自定义输入/输出文件。
"""
import os
import argparse
import json
import glob
from bs4 import BeautifulSoup, Doctype
import time
from urllib.parse import urlparse

def clean_url(raw_url: str) -> str:
    """去除查询参数与锚点，返回净化后的 URL"""
    if not raw_url:
        return ""
    parts = urlparse(raw_url)
    cleaned = f"{parts.scheme}://{parts.netloc}{parts.path}"
    return cleaned.rstrip("/")


def classify_bookmark(url, title, seen_urls, config):
    """
    根据配置文件的规则对单个书签进行分类。
    这是一个完全由配置驱动的通用分类引擎。

    Args:
        url (str): 书签的 URL。
        title (str): 书签的标题。
        seen_urls (set): 用于记录已处理过的 URL，以实现去重。
        config (dict): 从 config.json 加载的完整配置对象。

    Returns:
        tuple or None: 如果书签是唯一的，则返回一个元组，
                       第一个元素是分类路径（字符串或元组），
                       第二个元素是 (URL, 标题) 元组。
                       如果书签重复，则返回 (None, None)。
    """
    if not url:
        return None, None

    cleaned_url = clean_url(url)
    if cleaned_url in seen_urls:
        return None, None
    seen_urls.add(cleaned_url)

    lower_title = title.lower()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path_parts = [p for p in parsed.path.split("/") if p]
    
    # 按照 processing_order 中定义的顺序执行分类
    for rule_type in config.get("processing_order", []):
        
        # --- 1. 特殊域名规则处理器 ---
        if rule_type == "special_domain_rules":
            rules = config.get("special_domain_rules", {})
            for category_path_str, rule in rules.items():
                category_path = tuple(category_path_str.split('/'))
                if any(d in domain for d in rule.get("domains", [])):
                    # 检查是否需要按路径分割
                    if "split_by_path_segment" in rule and path_parts:
                        segment_index = rule["split_by_path_segment"] - 1
                        if segment_index < len(path_parts):
                            dynamic_part = path_parts[segment_index]
                            return category_path + (dynamic_part,), (url, title)
                    return category_path, (url, title)

        # --- 2. 内容格式规则处理器 ---
        elif rule_type == "format_rules":
            rules = config.get("format_rules", {})
            for category_path_str, rule in rules.items():
                category_path = tuple(category_path_str.split('/'))
                if any(d in domain for d in rule.get("domains", [])):
                    return category_path, (url, title)
                if any(c in url for c in rule.get("url_contains", [])):
                    return category_path, (url, title)
                if any(url.lower().endswith(e) for e in rule.get("url_ends_with", [])):
                    return category_path, (url, title)

        # --- 3. "稍后阅读"规则处理器 ---
        elif rule_type == "read_later_rules":
            rule = config.get("read_later_rules", {})
            # 域名匹配
            if any(d in domain for d in rule.get("domains", [])):
                # 检查路径限制
                restrictions = rule.get("path_restrictions", {})
                if domain in restrictions:
                    if any(p in url for p in restrictions[domain]):
                        return "稍后阅读", (url, title)
                else: # 没有路径限制，直接分类
                    return "稍后阅读", (url, title)
            # 标题关键词匹配
            if any(kw in lower_title for kw in rule.get("keywords_in_title", [])):
                return "稍后阅读", (url, title)

        # --- 4. 通用分类规则处理器 (基于权重评分) ---
        elif rule_type == "category_rules":
            rules_config = config.get("category_rules", {})
            scores = {}

            for category_path_str, category_data in rules_config.items():
                category_path = tuple(category_path_str.split('/'))
                scores[category_path] = 0
                
                for rule in category_data.get("rules", []):
                    weight = rule.get("weight", 1)
                    match_target_str = ""
                    
                    match_type = rule.get("match")
                    if match_type == "domain":
                        match_target_str = domain
                    elif match_type == "url":
                        match_target_str = url
                    elif match_type == "title":
                        match_target_str = lower_title
                    
                    if not match_target_str:
                        continue
                        
                    # 检查是否包含任一关键词
                    if any(kw in match_target_str for kw in rule.get("keywords", [])):
                        # 检查是否包含任一排除词
                        if any(nkw in match_target_str for nkw in rule.get("must_not_contain", [])):
                            continue # 包含排除词，此条规则不计分
                        
                        scores[category_path] += weight

            # 找出得分最高的分类
            if any(s > 0 for s in scores.values()):
                best_category = max(scores, key=scores.get)
                # 可选：设置一个阈值，防止低分误匹配
                if scores[best_category] > 0:
                    return best_category, (url, title)

    return "未分类", (url, title)


def build_structure(categorized_bookmarks):
    """根据 categorized_bookmarks 构造多层嵌套 dict，供后续 HTML / Markdown 复用"""
    structured = {}

    def add_nested(path_tuple, item):
        cur = structured
        for idx, key in enumerate(path_tuple):
            is_last = idx == len(path_tuple) - 1
            if key not in cur:
                cur[key] = {"_items": []} if is_last else {}
            cur = cur[key]
        if "_items" not in cur:
            cur["_items"] = []
        cur["_items"].append(item)

    for path, (url, title) in categorized_bookmarks:
        if isinstance(path, tuple):
            add_nested(path, (url, title))
        else:
            add_nested((path,), (url, title))
    
    def simplify_single_item_folders(node):
        """
        递归地合并只包含单个书签且无子文件夹的目录。
        这个实现通过构建新字典来避免迭代时修改的副作用。
        """
        if not isinstance(node, dict):
            return node

        # 1. 首先，递归简化所有子节点
        simplified_children = {}
        for key, value in node.items():
            if key != "_items":
                simplified_children[key] = simplify_single_item_folders(value)

        # 2. 然后，基于简化后的子节点，构建当前层级的新节点
        new_node = {}
        # 先把当前层级的书签带过来
        if "_items" in node:
            new_node["_items"] = node["_items"]

        for key, simplified_child in simplified_children.items():
            # 检查这个简化后的子节点是否可以被合并
            has_subfolders = any(k != "_items" for k in simplified_child)
            is_single_bookmark = len(simplified_child.get("_items", [])) == 1

            if not has_subfolders and is_single_bookmark:
                # 是单项文件夹，将其中的书签"提起"到当前层级
                single_item = simplified_child["_items"][0]
                if "_items" not in new_node:
                    new_node["_items"] = []
                
                new_title = f"[{key}] {single_item[1]}"
                new_node["_items"].append((single_item[0], new_title))
            else:
                # 不是单项文件夹，保持原样
                new_node[key] = simplified_child
        
        return new_node

    # 不要对顶层结构本身进行简化，而是对每个顶层分类的内部进行简化
    # return simplify_single_item_folders(structured) # 旧的、错误的方式

    simplified_structure = {}
    for top_level_cat, content in structured.items():
        simplified_structure[top_level_cat] = simplify_single_item_folders(content)

    return simplified_structure


def generate_markdown(structured_bookmarks, md_file):
    """递归生成 Markdown 文件"""
    lines = []

    def walk(node, depth=0):
        indent = "  " * depth
        for key, value in sorted(node.items()):
            if key == "_items":
                for url, title in value:
                    lines.append(f"{indent}- [{title}]({url})")
                continue
            lines.append(f"{indent}### {key}" if depth == 0 else f"{indent}- **{key}**")
            walk(value, depth + 1)

    walk(structured_bookmarks)
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def create_bookmark_html(structured_bookmarks, output_file):
    """
    根据构造好的书签结构，生成 Netscape-Bookmark-file-1 格式的 HTML 文件。

    这种格式的文件可以被主流浏览器（如 Chrome, Edge, Firefox）正确识别和导入。

    Args:
        structured_bookmarks (dict): 经过 `build_structure` 函数处理后的嵌套字典。
        output_file (str): 输出 HTML 文件的路径。
    """
    ts = str(int(time.time()))
    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        "<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">",
        "<TITLE>Bookmarks</TITLE>",
        "<H1>Bookmarks</H1>",
        "<DL><p>"
    ]

    def write_folder(name, content_dict, indent=1):
        ind = "    " * indent
        lines.append(f"{ind}<DT><H3 ADD_DATE=\"{ts}\" LAST_MODIFIED=\"{ts}\">{name}</H3>")
        lines.append(f"{ind}<DL><p>")
        # 遍历子元素
        for key, value in sorted(content_dict.items()):
            if key == "_items":
                for url, title in value:
                    lines.append(f"{ind}    <DT><A HREF=\"{url}\" ADD_DATE=\"{ts}\">{title}</A>")
            else:
                write_folder(key, value, indent + 1)
        lines.append(f"{ind}</DL><p>")

    # 按固定顺序写顶层，以保持一致
    top_order = [
        "工作台", "生物信息", "AI 研究室", "技术栈", "效率工具", "学习 & 阅读", "休闲娱乐", "稍后阅读", "未分类"
    ]
    for cat in top_order:
        if cat in structured_bookmarks:
            write_folder(cat, structured_bookmarks[cat])
    # 针对可能新增的其他顶层类别
    for cat in sorted(structured_bookmarks.keys()):
        if cat not in top_order:
            write_folder(cat, structured_bookmarks[cat])

    lines.append("</DL><p>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    """
    主函数，用于解析命令行参数并执行书签清理和分类的核心流程。
    支持多策略配置选择。
    """
    parser = argparse.ArgumentParser(
        description="清理、合并并分类浏览器导出的 HTML 书签文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-i', '--input',
        nargs='+',
        default=[],
        help='一个或多个输入的 HTML 书签文件路径（用空格分隔）。\n如果未提供，脚本会自动扫描 "tests/input" 目录。'
    )
    parser.add_argument(
        '-c', '--config',
        default=None, # 默认值改为 None，以便检测用户是否指定
        help='指定分类规则的 JSON 配置文件路径。\n如果未提供，将自动搜索 config_*.json 文件并提供选择。'
    )
    parser.add_argument(
        '--output-html',
        default='tests/output/bookmarks_cleaned.html',
        help='输出的已清理 HTML 文件路径。\n默认值: tests/output/bookmarks_cleaned.html'
    )
    parser.add_argument(
        '--output-md',
        default='tests/output/bookmarks.md',
        help='输出的 Markdown 文件路径。\n默认值: tests/output/bookmarks.md'
    )
    args = parser.parse_args()

    config_file = args.config
    
    # --- 多策略配置选择 ---
    if not config_file:
        # 优先寻找主配置文件
        available_configs = []
        if os.path.exists('config.json'):
            available_configs.append('config.json')
        
        # 寻找其他策略文件
        other_configs = sorted(glob.glob('config_*.json'))
        for cfg in other_configs:
            if cfg not in available_configs:
                available_configs.append(cfg)

        if not available_configs:
            print("❌ 错误：未找到任何配置文件（config.json 或 config_*.json）。")
            return
        elif len(available_configs) == 1:
            config_file = available_configs[0]
            print(f"✅ 检测到单个配置，已自动选择: {config_file}")
        else:
            print("\n请选择要使用的分类策略：")
            # 将 config.json 标记为默认
            for i, f in enumerate(available_configs):
                default_marker = " (默认最强策略)" if f == 'config.json' else ""
                print(f"  [{i + 1}] {f}{default_marker}")
            
            while True:
                try:
                    choice_str = input("请输入选项编号 (直接回车使用默认): ")
                    if not choice_str and 'config.json' in available_configs:
                        config_file = 'config.json'
                        break
                    
                    choice = int(choice_str)
                    if 1 <= choice <= len(available_configs):
                        config_file = available_configs[choice - 1]
                        break
                    else:
                        print("❌ 输入无效，请输入列表中的编号。")
                except ValueError:
                    print("❌ 输入无效，请输入数字。")
            print(f"✅ 您已选择策略: {config_file}")


    input_files = args.input
    # 如果没有通过命令行参数提供输入文件，则从默认目录扫描
    if not input_files:
        input_dir = 'tests/input'
        if os.path.isdir(input_dir):
            print(f"✅ 信息：未从命令行获取输入，将自动扫描 '{input_dir}' 目录。")
            input_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.html')]
        else:
            print(f"❌ 错误：默认输入目录 '{input_dir}' 不存在或不是一个目录。请使用 --input 参数指定文件。")
            return
            
    if not input_files:
        print(f"❌ 错误：在指定的路径或默认目录 'tests/input' 中未找到任何 .html 书签文件。")
        return

    output_html_file = args.output_html
    output_md_file = args.output_md

    # --- 确保输出目录存在 ---
    output_dir = os.path.dirname(output_html_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✅ 创建输出目录: {output_dir}")

    # --- 加载配置 ---
    if not os.path.exists(config_file):
        print(f"❌ 错误：配置文件 '{config_file}' 不存在。")
        return
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ 成功加载配置文件: {config_file}")
    except json.JSONDecodeError:
        print(f"❌ 错误：配置文件 '{config_file}' 格式不正确，请检查是否为有效的 JSON。")
        return
    except Exception as e:
        print(f"❌ 错误：加载配置文件时发生未知错误: {e}")
        return
    # --- 配置加载完毕 ---

    all_links = []
    print(f"\n📖 开始处理 {len(input_files)} 个书签文件...")

    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"⚠️ 警告：输入文件 '{input_file}' 不存在，已跳过。")
            continue
        
        print(f"   - 正在读取: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'lxml')
        links = soup.find_all('a')
        all_links.extend(links)

    if not all_links:
        print("❌ 错误：未能在任何输入文件中找到有效的书签链接。")
        return

    print(f"\n🔍 共找到 {len(all_links)} 个书签链接（合并后）。")

    categorized_bookmarks = []
    seen_urls = set()

    print("🚀 开始分类和去重...")
    for link in all_links:
        url = link.get('href')
        title = link.string
        if url and title:
            category, item = classify_bookmark(url, title.strip(), seen_urls, config)
            if category and item:
                categorized_bookmarks.append((category, item))

    print(f"✅ 分类完成！共整理出 {len(categorized_bookmarks)} 个有效书签。")
    
    structured_data = build_structure(categorized_bookmarks)
    
    print(f"📝 正在生成 Markdown 输出: {output_md_file}")
    generate_markdown(structured_data, output_md_file)
    
    print(f"🌐 正在生成 HTML 输出: {output_html_file}")
    create_bookmark_html(structured_data, output_html_file)
    
    print("\n🎉 全部完成！")


if __name__ == '__main__':
    main()