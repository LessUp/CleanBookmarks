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
import re
import glob
from bs4 import BeautifulSoup, Doctype
import time
from urllib.parse import urlparse
from collections import Counter
from functools import lru_cache

@lru_cache(maxsize=200_000)
def _parse_url_cached(url: str):
    """带 LRU 缓存的 urlparse，加速重复解析"""
    return urlparse(url)


def clean_url(raw_url: str) -> str:
    """去除查询参数与锚点，返回净化后的 URL"""
    if not raw_url:
        return ""
    try:
        parts = _parse_url_cached(raw_url)
        # 对于本地文件和特殊协议，保留原样
        if parts.scheme in ('file', 'javascript', 'chrome', 'about'):
            return raw_url
        cleaned = f"{parts.scheme}://{parts.netloc}{parts.path}"
        return cleaned.rstrip("/")
    except Exception:
        return raw_url # 解析失败则返回原始 URL


def clean_title(title, config):
    """根据配置清理书签标题"""
    cleaning_rules = config.get("title_cleaning_rules")
    if not cleaning_rules:
        return title
    
    # 替换规则优先，处理 & 等
    for old, new in cleaning_rules.get("replacements", {}).items():
        title = title.replace(old, new)

    for prefix in cleaning_rules.get("prefixes", []):
        if title.startswith(prefix):
            title = title[len(prefix):].lstrip()

    for suffix in cleaning_rules.get("suffixes", []):
        if title.endswith(suffix):
            title = title[:-len(suffix)].rstrip()

    return title.strip()


def classify_bookmark(url, title, seen_urls, config):
    """
    根据配置文件的规则对单个书签进行分类。这是一个采用"加权评分模型"的分类引擎。
    增加了 `priority_rules` 来处理必须优先匹配的规则。
    """
    if not url:
        return None, None

    cleaned_url = clean_url(url)
    if cleaned_url in seen_urls:
        return None, None
    seen_urls.add(cleaned_url)

    lower_title = title.lower()
    lower_url = url.lower()
    try:
        parsed = _parse_url_cached(url)
        domain = parsed.netloc.lower().replace("www.", "")
    except Exception:
        domain = ""

    scores = {}

    def apply_rules(rules_config, default_weight=1):
        for category_path_str, category_data in rules_config.items():
            category_path = tuple(category_path_str.split('/'))
            category_weight = category_data.get("weight", default_weight)

            for rule in category_data.get("rules", []):
                weight = rule.get("weight", category_weight)
                match_target_str = ""
                
                match_type = rule.get("match")
                if match_type == "domain":
                    match_target_str = domain
                elif match_type == "url":
                    match_target_str = lower_url
                elif match_type == "title":
                    match_target_str = lower_title
                elif match_type == "url_starts_with":
                    if any(lower_url.startswith(kw) for kw in rule.get("keywords", [])):
                        scores.setdefault(category_path, 0)
                        scores[category_path] += weight
                    continue
                elif match_type == "url_ends_with":
                    if any(lower_url.endswith(kw) for kw in rule.get("keywords", [])):
                        scores.setdefault(category_path, 0)
                        scores[category_path] += weight
                    continue
                elif match_type == "url_matches_regex":
                    if any(re.search(kw, lower_url) for kw in rule.get("keywords", [])):
                        scores.setdefault(category_path, 0)
                        scores[category_path] += weight
                    continue

                if not match_target_str:
                    continue
                
                # 关键词匹配
                keywords = rule.get("keywords", [])
                not_keywords = rule.get("must_not_contain", [])
                match_all = rule.get("match_all_keywords_in", {})

                if any(kw in match_target_str for kw in keywords):
                    if any(nkw in match_target_str for nkw in not_keywords):
                        continue
                    
                    # 检查是否需要匹配所有附加关键词
                    all_matched = True
                    for target, kws in match_all.items():
                        target_str = ""
                        if target == "title": target_str = lower_title
                        elif target == "url": target_str = lower_url
                        
                        if not all(kw in target_str for kw in kws):
                           all_matched = False
                           break
                    
                    if all_matched:
                        scores.setdefault(category_path, 0)
                        scores[category_path] += weight

    # 1. 应用高优先级规则
    apply_rules(config.get("priority_rules", {}), default_weight=100)
    
    # 如果已有高分匹配，则可能提前决定
    if scores:
        best_category_so_far = max(scores, key=scores.get)
        if scores[best_category_so_far] >= 100:
             return best_category_so_far, (url, title)

    # 2. 应用普通分类规则
    apply_rules(config.get("category_rules", {}), default_weight=5)

    if not scores:
        return "未分类", (url, title)

    best_category = max(scores, key=scores.get)
    return best_category, (url, title)


def build_structure(categorized_bookmarks, config):
    """
    根据 categorized_bookmarks 构造多层嵌套 dict，并应用领域驱动的二次分组。
    严格限制目录层级为最多两层。
    """
    structured = {}
    domain_grouping_rules = config.get("domain_grouping_rules", {})

    def add_nested(path_tuple, item):
        cur = structured
        # 强制截断为最多两层
        path_tuple = path_tuple[:2]
        for idx, key in enumerate(path_tuple):
            is_last = idx == len(path_tuple) - 1
            if key not in cur:
                # 最后一层才创建 _items
                cur[key] = {"_items": []} if is_last else {}
            if not isinstance(cur.get(key), dict):
                 cur[key] = {}
            cur = cur[key]
        if "_items" not in cur:
            cur["_items"] = []
        cur["_items"].append(item)

    for path, (url, title) in categorized_bookmarks:
        path_tuple = path if isinstance(path, tuple) else (path,)
        if not path_tuple:
            continue
            
        top_level_cat = path_tuple[0]
        final_path = path_tuple

        # 应用领域驱动分组规则
        grouping_domains = domain_grouping_rules.get(top_level_cat)
        if grouping_domains:
            try:
                domain = _parse_url_cached(url).netloc.lower().replace("www.", "")
                if domain in grouping_domains:
                    final_path = (top_level_cat, domain)
            except Exception:
                pass
        
        add_nested(final_path, (url, title))
    
    return structured


def generate_markdown(structured_bookmarks, md_file):
    """递归生成具有标准多级标题和排序的 Markdown 文件"""
    lines = ["# 书签整理"]

    def walk(node, depth=1):
        # 对子目录按字母顺序排序
        sorted_keys = sorted([k for k in node.keys() if k != "_items"])

        # 1. 处理子目录
        for key in sorted_keys:
            heading_level = min(depth + 1, 4)
            heading_prefix = "#" * heading_level
            lines.append(f"\n{heading_prefix} {key}\n")
            walk(node[key], depth + 1)

        # 2. 处理当前层级的书签
        if "_items" in node:
            # 对书签按标题排序
            sorted_items = sorted(node["_items"], key=lambda item: item[1])
            for url, title in sorted_items:
                lines.append(f"- [{title}]({url})")

    # 从顶层开始遍历
    top_order = [
        "工作台", "AI", "技术栈", "生物信息", "OnlineBooks", "技术资料", 
        "Lectures", "社区", "资讯", "求职", "娱乐", "OnlineTools", "学习", "稍后阅读", "本地网络 & 浏览器", "未分类"
    ]

    # 按指定顺序处理顶层分类
    for cat in top_order:
        if cat in structured_bookmarks:
            lines.append(f"\n## {cat}\n")
            walk(structured_bookmarks[cat], depth=1)
    
    # 处理其他未在顺序列表中的分类
    for cat in sorted(structured_bookmarks.keys()):
        if cat not in top_order:
             lines.append(f"\n## {cat}\n")
             walk(structured_bookmarks[cat], depth=1)

    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def create_bookmark_html(structured_bookmarks, output_file):
    """根据构造好的书签结构，生成 Netscape 格式的 HTML 文件。"""
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
        
        # 统一排序子文件夹和书签
        sorted_keys = sorted([k for k in content_dict.keys() if k != "_items"])
        
        for key in sorted_keys:
            write_folder(key, content_dict[key], indent + 1)
        
        if "_items" in content_dict:
            sorted_items = sorted(content_dict["_items"], key=lambda item: item[1])
            for url, title in sorted_items:
                # HTML实体编码，防止特殊字符破坏结构
                title_encoded = title.replace('&', '&').replace('<', '<').replace('>', '>')
                url_encoded = url.replace('&', '&')
                lines.append(f"{ind}    <DT><A HREF=\"{url_encoded}\" ADD_DATE=\"{ts}\">{title_encoded}</A>")

        lines.append(f"{ind}</DL><p>")

    top_order = [
        "工作台", "AI", "技术栈", "生物信息", "OnlineBooks", "技术资料", 
        "Lectures", "社区", "资讯", "求职", "娱乐", "OnlineTools", "学习", "稍后阅读", "本地网络 & 浏览器", "未分类"
    ]
    
    for cat in top_order:
        if cat in structured_bookmarks:
            write_folder(cat, structured_bookmarks[cat])
    
    for cat in sorted(structured_bookmarks.keys()):
        if cat not in top_order:
            write_folder(cat, structured_bookmarks[cat])

    lines.append("</DL><p>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _count_bookmarks_recursive(node):
    """递归地统计一个节点下书签的总数"""
    if not isinstance(node, dict): return 0
    count = len(node.get("_items", []))
    for key, value in node.items():
        if key != "_items":
            count += _count_bookmarks_recursive(value)
    return count

def print_statistics(structured_data, total_links_found, unique_links_count):
    """打印关于书签集合的统计信息"""
    print("\n📊----- 书签统计信息 -----📊")
    
    duplicates_found = total_links_found - unique_links_count
    print(f"✨ 去重成果: 共找到并移除了 {duplicates_found} 个重复链接。")

    print("\n📚 各分类书签数量:")
    category_counts = {}
    all_domains = []
    
    def collect_stats(node, cat_name):
        if not isinstance(node, dict): return
        category_counts[cat_name] = category_counts.get(cat_name, 0) + len(node.get("_items", []))
        
        for url, _ in node.get("_items", []):
            try:
                all_domains.append(_parse_url_cached(url).netloc.lower().replace("www.",""))
            except: pass
        
        for key, value in node.items():
            if key != "_items":
                collect_stats(value, f"{cat_name}/{key}")

    for category, content in structured_data.items():
        collect_stats(content, category)

    if category_counts:
        sorted_categories = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
        for category, count in sorted_categories:
            print(f"  - {category:<40} : {count} 个")

    if all_domains:
        print("\n🌐 您最常访问的 Top 10 网站:")
        top_10_domains = Counter(d for d in all_domains if d).most_common(10)
        for i, (domain, count) in enumerate(top_10_domains):
            print(f"  {i+1}. {domain} ({count} 次)")
        
    print("--------------------------\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="清理、合并并分类浏览器导出的 HTML 书签文件。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # ... (命令行参数解析部分与您原文件一致，此处省略以保持简洁)
    parser.add_argument('-i', '--input', nargs='+', default=[], help='输入的HTML书签文件路径。')
    parser.add_argument('-c', '--config', default='config.json', help='分类规则的JSON配置文件路径。')
    parser.add_argument('--output-html', default='tests/output/bookmarks_cleaned.html', help='输出的HTML文件路径。')
    parser.add_argument('--output-md', default='tests/output/bookmarks.md', help='输出的Markdown文件路径。')
    args = parser.parse_args()

    input_files = args.input if args.input else glob.glob('tests/input/*.html')
    if not input_files:
        # 如果命令行和默认目录都没有，就使用您上传的文件名
        if os.path.exists('bookmarks_2025_7_1.html'):
            input_files = ['bookmarks_2025_7_1.html']
            print(f"✅ 信息: 未找到输入文件，使用当前目录下的 'bookmarks_2025_7_1.html'")
        else:
            print("❌ 错误: 未找到任何输入文件。")
            return
    
    config_file = args.config
    output_html_file = args.output_html
    output_md_file = args.output_md

    output_dir = os.path.dirname(output_html_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ 成功加载配置文件: {config_file}")
    except Exception as e:
        print(f"❌ 错误: 加载配置文件 '{config_file}' 失败: {e}")
        return

    all_links = []
    print(f"\n📖 开始处理 {len(input_files)} 个书签文件...")
    for input_file in input_files:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'lxml')
            links = soup.find_all('a')
            all_links.extend(links)
            print(f"   - 已读取: {input_file} (找到 {len(links)} 个链接)")
        except Exception as e:
            print(f"⚠️ 警告: 处理文件 '{input_file}' 时出错: {e}")
    
    if not all_links:
        print("❌ 错误：未能在任何输入文件中找到有效的书签链接。")
        return

    print(f"\n🔍 共找到 {len(all_links)} 个书签链接（合并后）。")
    print("🚀 开始分类和去重...")

    categorized_bookmarks = []
    seen_urls = set()
    unclassified_log = []

    for link in all_links:
        url = link.get('href', '').strip()
        title = (link.string or url).strip()
        if url and title:
            category, item = classify_bookmark(url, title, seen_urls, config)
            if category and item:
                url_original, title_original = item
                cleaned_title = clean_title(title_original, config)
                categorized_bookmarks.append((category, (url_original, cleaned_title)))
                if category == "未分类":
                    unclassified_log.append(f"{url_original} | {title_original}")
    
    if unclassified_log:
        log_file_path = "unclassified_log.txt"
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(unclassified_log))
        print(f"⚠️ 注意: {len(unclassified_log)} 个书签被归为'未分类'，详情请见 {log_file_path}")

    print(f"✅ 分类完成！共整理出 {len(categorized_bookmarks)} 个有效书签。")
    
    structured_data = build_structure(categorized_bookmarks, config)
    
    print_statistics(structured_data, len(all_links), len(seen_urls))
    
    print(f"📝 正在生成 Markdown 输出: {output_md_file}")
    generate_markdown(structured_data, output_md_file)
    
    print(f"🌐 正在生成 HTML 输出: {output_html_file}")
    create_bookmark_html(structured_data, output_html_file)
    
    print("\n🎉 全部完成！您的书签已焕然一新。")

if __name__ == '__main__':
    main()