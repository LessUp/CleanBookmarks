import argparse
import os
import sys
import time
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import json
import re
import socket
from urllib.request import Request, urlopen
import itertools
from concurrent.futures import ThreadPoolExecutor

class Folder:
    def __init__(self, name):
        self.name = name
        self.children = []

class Bookmark:
    def __init__(self, title, href, add_date=None, path=None):
        self.title = title
        self.href = href
        self.add_date = add_date
        self.path = path or []

class NetscapeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Folder('ROOT')
        self.stack = [self.root]
        self.in_h3 = False
        self.in_a = False
        self.capture = []
        self.pending_folder = None
        self.pending_folder_attrs = {}
        self.pending_a_attrs = {}

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): v for k, v in attrs}
        if tag.lower() == 'h3':
            self.in_h3 = True
            self.capture = []
            self.pending_folder_attrs = a
            self.pending_folder = Folder('')
        elif tag.lower() == 'a':
            self.in_a = True
            self.capture = []
            self.pending_a_attrs = a
        elif tag.lower() == 'dl':
            if self.pending_folder is not None:
                name = ''.join(self.capture).strip()
                self.pending_folder.name = name
                self.stack[-1].children.append(self.pending_folder)
                self.stack.append(self.pending_folder)
                self.pending_folder = None
                self.capture = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == 'h3':
            self.in_h3 = False
        elif t == 'a':
            title = ''.join(self.capture).strip()
            href = self.pending_a_attrs.get('href')
            add_date = self.pending_a_attrs.get('add_date')
            if href:
                path = [n.name for n in self.stack if n is not self.root]
                bm = Bookmark(title or href, href, int(add_date) if add_date and add_date.isdigit() else None, path)
                self.stack[-1].children.append(bm)
            self.in_a = False
            self.capture = []
            self.pending_a_attrs = {}
        elif t == 'dl':
            if len(self.stack) > 1:
                self.stack.pop()

    def handle_data(self, data):
        if self.in_h3 or self.in_a:
            self.capture.append(data)

def walk_bookmarks(node, acc=None):
    if acc is None:
        acc = []
    if isinstance(node, Bookmark):
        acc.append(node)
    elif isinstance(node, Folder):
        for c in node.children:
            walk_bookmarks(c, acc)
    return acc

TRACKING_KEYS = set([
    'utm_source','utm_medium','utm_campaign','utm_term','utm_content','utm_id','utm_name',
    'gclid','fbclid','msclkid','igshid','mkt_tok','mc_cid','mc_eid','ref','ref_src','referrer',
    'spm','scm','ved','ei','oq','aqs','srsltid','trk'
])

def normalize_url(url):
    try:
        parts = urlsplit(url)
        scheme = (parts.scheme or '').lower()
        netloc = (parts.netloc or '').lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        if ':' in netloc:
            host, port = netloc.rsplit(':', 1)
            if (scheme == 'http' and port == '80') or (scheme == 'https' and port == '443'):
                netloc = host
        path = parts.path or ''
        if len(path) > 1 and path.endswith('/'):
            path = path[:-1]
        q = []
        for k, v in parse_qsl(parts.query, keep_blank_values=True):
            kl = k.lower()
            if kl.startswith('utm_') or kl in TRACKING_KEYS:
                continue
            q.append((k, v))
        q.sort()
        query = urlencode(q, doseq=True)
        return urlunsplit((scheme, netloc, path, query, ''))
    except Exception:
        return url

TOP_CATS = [
    '工作',
    'AI·大模型',
    '编程语言',
    'Web·前端',
    'DevOps·运维',
    '开发工具',
    'API·平台',
    '学习与CS基础',
    'Homelab·服务器',
    '待分类',
]

HOST_HINTS_DEV = (
    'github.com','gitlab.com','huggingface.co','openai.com','mistral.ai','qwen.ai','langchain','go.dev',
    'developer','dev','docs','docker','k8s','kubernetes','aliyun','huaweicloud','cloud',
    'grafana','prometheus','kibana','elastic','notebooklm','perplexity','gemini.google.com','duckduckgo',
)

KEY_AI = ('ai','人工智能','大模型','ml','机器学习','深度学习','llm','chat','gpt','midjourney','comfyui','deepseek','perplexity','gemini','novix','kimi','qwen','baichuan')
KEY_LANG_GO = (' golang',' go ',' gin ',' gorm','go.dev')
KEY_LANG_CPP = ('c++','cpp','cuda','linux','kernel','bootlin')
KEY_LANG_RUST = ('rust','rust-lang')
KEY_WEB = ('web','frontend','javascript','typescript','vue','react','css','html','django','echarts','grid')
KEY_DEVOPS = ('devops','docker','k8s','kubernetes','cicd','ci/cd','teamcity','coverity','jenkins','observability','promql','grafana','kibana','prometheus','elastic')
KEY_TOOLS = ('ide','jetbrains','vscode','tmux','warp','yazi','coder','marscode','copilot','nav','trzsz','x-cmd')
KEY_API = ('api','sdk','docs','platform','console')
KEY_CS = ('teachyourselfcs','cs自学','ocw.mit.edu','algorithm','cs','计算机科学')
KEY_DPA = ('设计模式','architecture','ddd','event','patterns','架构')

KEY_HOME = ('unraid','nas','homelab','server','服务器','nextcloud','sftp','ssh')
KEY_LANG = ('语言','翻译','translation','dictionary','english','英语','汉英','英汉')
KEY_SCI = ('physics','chemistry','biology','genomics','math','数学','物理','化学','生物')
KEY_ART = ('艺术','music','摄影','设计','绘画','图像风格','ghibli')
KEY_SOC = ('经济','finance','marketing','管理','社会')
KEY_LIT = ('阅读','读书','小说','文学','poetry')
KEY_HIS = ('历史','history','地理','map')
KEY_REL = ('宗教','bible','佛','道','基督')
KEY_PSY = ('心理','哲学','philosophy','psychology')


def is_private_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        host = parts.hostname or ''
        if host.startswith('10.') or host.startswith('192.168.'):
            return True
        if host.startswith('172.'):
            segs = host.split('.')
            if len(segs) >= 2:
                try:
                    s1 = int(segs[1])
                    if 16 <= s1 <= 31:
                        return True
                except ValueError:
                    pass
        if parts.scheme in ('chrome-extension','file','data'):
            return True
    except Exception:
        return False
    return False


TITLE_RE = re.compile(r'<title[^>]*>(.*?)</title>', re.IGNORECASE | re.DOTALL)

def simple_fetch_title(url: str, timeout_sec: int = 3) -> str:
    if is_private_url(url):
        return ''
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        socket.setdefaulttimeout(timeout_sec)
        with urlopen(req, timeout=timeout_sec) as resp:
            ct = resp.headers.get('Content-Type','').lower()
            if 'text/html' not in ct and 'application/xhtml' not in ct and 'xml' not in ct:
                return ''
            raw = resp.read(40960)
            m = TITLE_RE.search(raw.decode('utf-8', errors='ignore'))
            if m:
                return m.group(1).strip()
    except Exception:
        return ''
    return ''


def load_rules(config_dir: str):
    dr = {}
    kr = {}
    try:
        p = os.path.join(config_dir, 'domain_rules.json')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                dr = json.load(f)
    except Exception:
        dr = {}
    try:
        p = os.path.join(config_dir, 'keyword_rules.json')
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                kr = json.load(f)
    except Exception:
        kr = {}
    return dr, kr


def apply_rule_for_url(title, url, path, domain_rules, keyword_rules):
    try:
        parts = urlsplit(url)
        host = (parts.hostname or '').lower()
    except Exception:
        host = ''
    for key, val in domain_rules.items():
        k = key.lower()
        if host.endswith(k) or (k and k in host):
            top = val.get('top')
            second = val.get('second')
            return top, second
    text = f"{title} {url} {'/'.join(path)}".lower()
    for key, val in keyword_rules.items():
        if key.lower() in text:
            top = val.get('top')
            second = val.get('second')
            return top, second
    return None, None


def classify_top(title, url, path):
    text = f"{title} {url} {'/'.join(path)}".lower()
    if 'zego' in text:
        return '工作'
    if 'bgi' in text or 'genomics' in text:
        return '工作'
    if any(k in text for k in KEY_AI):
        return 'AI·大模型'
    if any(k in text for k in KEY_LANG_GO + KEY_LANG_CPP + KEY_LANG_RUST):
        return '编程语言'
    if any(k in text for k in KEY_WEB):
        return 'Web·前端'
    if any(k in text for k in KEY_DEVOPS):
        return 'DevOps·运维'
    if any(k in text for k in KEY_TOOLS):
        return '开发工具'
    if any(k in text for k in KEY_API):
        return 'API·平台'
    if any(k in text for k in KEY_CS + KEY_DPA + KEY_LANG + KEY_SCI + KEY_ART + KEY_SOC + KEY_LIT + KEY_HIS + KEY_REL + KEY_PSY):
        return '学习与CS基础'
    if any(k in text for k in KEY_HOME):
        return 'Homelab·服务器'
    if any(h in text for h in HOST_HINTS_DEV):
        return '开发工具'
    return '待分类'


def classify_sub(title, url, path):
    text = f"{title} {url} {'/'.join(path)}".lower()
    if 'zego' in text:
        return ('工作', 'ZEGO')
    if 'bgi' in text or 'genomics' in text:
        return ('工作', 'BGI')
    if any(k in text for k in KEY_LANG_GO):
        return ('编程语言', 'Go')
    if any(k in text for k in KEY_LANG_CPP):
        return ('编程语言', 'C++·系统')
    if any(k in text for k in KEY_LANG_RUST):
        return ('编程语言', 'Rust')
    if any(k in text for k in KEY_WEB):
        return ('Web·前端', None)
    if any(k in text for k in KEY_DEVOPS):
        return ('DevOps·运维', None)
    if any(k in text for k in KEY_TOOLS):
        return ('开发工具', None)
    if any(k in text for k in KEY_API):
        return ('API·平台', None)
    if any(k in text for k in KEY_AI):
        return ('AI·大模型', None)
    if any(k in text for k in KEY_HOME):
        return ('Homelab·服务器', None)
    if any(k in text for k in KEY_CS + KEY_DPA + KEY_LANG + KEY_SCI + KEY_ART + KEY_SOC + KEY_LIT + KEY_HIS + KEY_REL + KEY_PSY):
        return ('学习与CS基础', None)
    return ('待分类', None)


def find_or_create_folder(parent, name):
    for c in parent.children:
        if isinstance(c, Folder) and c.name == name:
            return c
    f = Folder(name)
    parent.children.append(f)
    return f


def render(folder, out, indent=0):
    sp = '    ' * indent
    for c in folder.children:
        if isinstance(c, Folder):
            out.append(f"{sp}<DT><H3>{escape_html(c.name)}</H3>")
            out.append(f"{sp}<DL><p>")
            render(c, out, indent+1)
            out.append(f"{sp}</DL><p>")
        else:
            href = c.href
            title = c.title or c.href
            add_date = str(c.add_date or int(time.time()))
            out.append(f"{sp}<DT><A HREF=\"{escape_html(href)}\" ADD_DATE=\"{add_date}\">{escape_html(title)}</A>")


def escape_html(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')


def write_netscape_html(root_folders, output_path):
    lines = []
    lines.append("<!DOCTYPE NETSCAPE-Bookmark-file-1>")
    lines.append("<!-- This is an automatically generated file.")
    lines.append("     It will be read and overwritten.")
    lines.append("     DO NOT EDIT! -->")
    lines.append("<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=UTF-8\">")
    lines.append("<TITLE>Bookmarks</TITLE>")
    lines.append("<H1>Bookmarks</H1>")
    lines.append("<DL><p>")
    tmp_root = Folder('ROOT')
    for f in root_folders:
        tmp_root.children.append(f)
    render(tmp_root, lines, 1)
    lines.append("</DL>")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


def merge_and_classify(inputs, output_path, changelog_dir, fetch_mode: str = 'none', fetch_limit: int = 0, fetch_timeout_sec: int = 3, fetch_workers: int = 8, config_dir: str = ''):
    total_in = 0
    by_file = {}
    all_bms = []
    for ip in inputs:
        try:
            with open(ip, 'r', encoding='utf-8') as f:
                data = f.read()
        except UnicodeDecodeError:
            with open(ip, 'r', encoding='latin-1') as f:
                data = f.read()
        p = NetscapeParser()
        p.feed(data)
        bms = walk_bookmarks(p.root)
        by_file[os.path.basename(ip)] = len(bms)
        total_in += len(bms)
        all_bms.extend(bms)
    dedup = {}
    for bm in all_bms:
        key = normalize_url(bm.href)
        if key not in dedup:
            dedup[key] = Bookmark(bm.title, key, bm.add_date, bm.path)
        else:
            if len(bm.title or '') > len(dedup[key].title or ''):
                dedup[key].title = bm.title
    after = list(dedup.values())
    fetched = 0
    targets = []
    if fetch_mode == 'uncertain':
        for bm in after:
            if classify_top(bm.title or '', bm.href or '', bm.path) == '待分类':
                targets.append(bm)
    elif fetch_mode == 'all':
        targets = after[:]
    if fetch_mode != 'none':
        if fetch_limit and fetch_limit < len(targets):
            targets = targets[:fetch_limit]
        with ThreadPoolExecutor(max_workers=max(1, fetch_workers)) as ex:
            futs = [ex.submit(simple_fetch_title, bm.href, fetch_timeout_sec) for bm in targets]
            for bm, fut in zip(targets, futs):
                try:
                    t = fut.result()
                except Exception:
                    t = ''
                if t:
                    bm.title = t
        fetched = len(targets)
    drules, krules = load_rules(config_dir or os.path.join(os.path.dirname(output_path), 'config'))
    top_map = {name: Folder(name) for name in TOP_CATS}
    used_names = set()
    for bm in after:
        rtop, rsecond = apply_rule_for_url(bm.title or '', bm.href or '', bm.path, drules, krules)
        if rtop not in TOP_CATS and rtop is not None:
            rtop = '待分类'
        top_name = rtop or classify_top(bm.title or '', bm.href or '', bm.path)
        used_names.add(top_name)
        top_folder = top_map[top_name]
        second, third = classify_sub(bm.title or '', bm.href or '', bm.path)
        if rsecond:
            second = rsecond
        target_parent = top_folder
        if second and second in TOP_CATS:
            target_parent = top_map[second]
        elif second:
            target_parent = find_or_create_folder(top_folder, second)
        if third:
            target_parent = find_or_create_folder(target_parent, third)
        target_parent.children.append(Bookmark(bm.title, bm.href, bm.add_date))
    ordered = [top_map[name] for name in TOP_CATS if name in used_names]
    write_netscape_html(ordered, output_path)
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    os.makedirs(changelog_dir, exist_ok=True)
    log_path = os.path.join(changelog_dir, time.strftime('%Y%m%d_%H%M%S') + '_bookmarks_merge.md')
    lines = []
    lines.append(f"时间: {ts}")
    lines.append(f"输入文件: {', '.join(os.path.basename(x) for x in inputs)}")
    lines.append(f"每个输入文件书签数: {by_file}")
    lines.append(f"合计书签数(输入): {total_in}")
    lines.append(f"去重后书签数(输出): {len(after)}")
    lines.append(f"去重数量: {total_in - len(after)}")
    lines.append("一级目录(自定义≤10): " + ', '.join(f.name for f in ordered))
    lines.append(f"规则目录: {config_dir or os.path.join(os.path.dirname(output_path), 'config')}")
    lines.append(f"规则条目: domain={len(drules)}, keyword={len(krules)}")
    lines.append(f"抓取模式: {fetch_mode}, 抓取尝试数: {fetched}, 并发: {fetch_workers}")
    lines.append(f"输出: {output_path}")
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return {
        'input_total': total_in,
        'output_total': len(after),
        'dedup_removed': total_in - len(after),
        'top_used': [f.name for f in ordered],
        'output': output_path,
        'log': log_path,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', nargs='+', required=True)
    parser.add_argument('--output', default='')
    parser.add_argument('--changelog_dir', default='changelog')
    parser.add_argument('--config_dir', default='config')
    parser.add_argument('--fetch_mode', choices=['none','uncertain','all'], default='none')
    parser.add_argument('--fetch_limit', type=int, default=0)
    parser.add_argument('--fetch_timeout_sec', type=int, default=3)
    parser.add_argument('--fetch_workers', type=int, default=8)
    args = parser.parse_args()
    inputs = [os.path.abspath(x) for x in args.inputs]
    for pth in inputs:
        if not os.path.exists(pth):
            print(f"文件不存在: {pth}", file=sys.stderr)
            sys.exit(1)
    out = args.output
    if not out:
        out = os.path.join(os.path.dirname(inputs[0]), time.strftime('merged_bookmarks_%Y_%m_%d_%H%M.html'))
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    changelog_dir = os.path.abspath(os.path.join(os.path.dirname(out), args.changelog_dir))
    config_dir = os.path.abspath(os.path.join(os.path.dirname(out), args.config_dir))
    res = merge_and_classify(inputs, out, changelog_dir, fetch_mode=args.fetch_mode, fetch_limit=args.fetch_limit, fetch_timeout_sec=args.fetch_timeout_sec, fetch_workers=args.fetch_workers, config_dir=config_dir)
    print(res)

if __name__ == '__main__':
    main()
