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


def classify_bookmark(url, title, seen_urls, categories, domain_based_subcats):
    """
    根据 URL 和标题对单个书签进行分类。

    Args:
        url (str): 书签的 URL。
        title (str): 书签的标题。
        seen_urls (set): 用于记录已处理过的 URL，以实现去重。
        categories (dict): 从配置文件加载的分类规则。
        domain_based_subcats (set): 从配置文件加载的、需要按域名细分的子分类集合。

    Returns:
        tuple or None: 如果书签是唯一的，则返回一个元组，
                       第一个元素是分类路径（字符串或元组），
                       第二个元素是 (URL, 标题) 元组。
                       如果书签重复，则返回 (None, None)。
    """
    if not url:
        return None, None

    url = clean_url(url)
    if url in seen_urls:
        return None, None
    seen_urls.add(url)

    lower_title = title.lower()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path_parts = [p for p in parsed.path.split("/") if p]

    # ---- 专门处理 GitHub ----
    if domain == "github.com" and path_parts:
        owner = path_parts[0]
        return ("技术栈", "代码 & 开源", "GitHub", owner), (url, title)

    # ---- DevOps 域名 ----
    if any(dev in domain for dev in ["docker.com", "kubernetes.io", "helm.sh"]):
        return ("技术栈", "DevOps"), (url, title)

    # ---- 通用关键词匹配 ----
    for category, rules in categories.items():
        # 检查子分类
        if "sub_categories" in rules and rules["sub_categories"]:
            for sub_category, sub_rules in rules["sub_categories"].items():
                for keyword in sub_rules.get("keywords", []):
                    if keyword in domain or keyword in url or keyword in lower_title:
                        # 针对需按域名再细分的子分类，追加域名层级
                        if (category, sub_category) in domain_based_subcats:
                            return (category, sub_category, domain), (url, title)
                        return (category, sub_category), (url, title)
        # 检查主分类
        if "keywords" in rules:
            for keyword in rules.get("keywords", []):
                if keyword in domain or keyword in url or keyword in lower_title:
                    return category, (url, title)

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
    return structured


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
        "工作台", "生物信息", "AI 研究室", "技术栈", "效率工具", "学习 & 阅读", "休闲娱乐", "未分类"
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
    """
    parser = argparse.ArgumentParser(
        description="清理、合并并分类浏览器导出的 HTML 书签文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-i', '--input',
        nargs='+',  # 允许多个输入值
        required=True,
        help='一个或多个输入的 HTML 书签文件路径（用空格分隔）。\n示例: --input chrome.html edge.html'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help='指定分类规则的 JSON 配置文件路径。\n默认值: config.json'
    )
    parser.add_argument(
        '--output-html',
        default='bookmarks_cleaned.html',
        help='输出的已清理 HTML 文件路径。\n默认值: bookmarks_cleaned.html'
    )
    parser.add_argument(
        '--output-md',
        default='bookmarks.md',
        help='输出的 Markdown 文件路径。\n默认值: bookmarks.md'
    )
    args = parser.parse_args()

    input_files = args.input
    config_file = args.config
    output_html_file = args.output_html
    output_md_file = args.output_md

    # --- 加载配置 ---
    if not os.path.exists(config_file):
        print(f"❌ 错误：配置文件 '{config_file}' 不存在。")
        return
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        categories = loaded_config.get("categories", {})
        # JSON不支持集合(set)和元组(tuple)，需要转换
        domain_based_subcats_list = loaded_config.get("domain_based_subcats", [])
        domain_based_subcats = {tuple(item) for item in domain_based_subcats_list}
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
            category, item = classify_bookmark(url, title.strip(), seen_urls, categories, domain_based_subcats)
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