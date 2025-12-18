"""
LLM Classifier - 可选大模型分类器

- 通过通用 OpenAI-Compatible 接口进行分类推断
- 根据配置文件 `config.json` 的 `llm` 配置段启用/禁用
- KISS：仅负责与 LLM 对话并返回标准化分类结果，具体融合由上层完成

配置示例（添加到 config.json 顶层）：
{
  "llm": {
    "enable": false,
    "provider": "openai",                 # 兼容 OpenAI 接口的服务商
    "base_url": "https://api.openai.com", # 若为自建服务，填相应 URL
    "model": "gpt-4o-mini",
    "api_key_env": "OPENAI_API_KEY",      # 从该环境变量读取 API Key
    "temperature": 0.0,
    "top_p": 1.0,
    "timeout_seconds": 25,
    "max_retries": 1
  }
}
"""
from __future__ import annotations

import json
import hashlib
import os
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests

class LLMClassifier:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.llm_conf = self.config.get("llm", {}) or {}
        from .llm_prompt_builder import LLMPromptBuilder
        self.prompt_builder = LLMPromptBuilder(self.config)
        self._cache: Dict[str, Dict] = {}
        self._stats = {
            "enabled": bool(self.llm_conf.get("enable", False)),
            "calls": 0,
            "cache_hits": 0,
            "failures": 0
        }

    # -------------------- Public API --------------------
    def enabled(self) -> bool:
        return bool(self.llm_conf.get("enable", False))

    def classify(self, url: str, title: str, context: Optional[Dict] = None) -> Optional[Dict]:
        if not self.enabled():
            return None

        api_key_env = self.llm_conf.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_env, "")
        if not api_key:
            # 未设置 API Key，跳过 LLM
            return None

        # 构建缓存键
        h = hashlib.md5(f"{url}::{title}".encode()).hexdigest()
        if h in self._cache:
            self._stats["cache_hits"] += 1
            return self._cache[h]

        base_url = (self.llm_conf.get("base_url") or "https://api.openai.com").rstrip("/")
        model = self.llm_conf.get("model", "gpt-4o-mini")
        temperature = float(self.llm_conf.get("temperature", 0.0))
        top_p = float(self.llm_conf.get("top_p", 1.0))
        timeout = int(self.llm_conf.get("timeout_seconds", 25))
        max_retries = int(self.llm_conf.get("max_retries", 1))

        categories = self._collect_valid_categories(self.config)
        category_library = self._build_category_library(categories)
        bookmark_payload = self._build_bookmark_payload(url, title, context or {})
        hints = self._build_hint_profile(url, title, bookmark_payload)
        messages, response_format = self.prompt_builder.build_messages(
            bookmark=bookmark_payload,
            hints=hints,
            category_library=category_library,
        )

        payload = {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "messages": messages,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        url_chat = f"{base_url}/v1/chat/completions"

        data = None
        last_err = None
        for _ in range(max_retries + 1):
            try:
                self._stats["calls"] += 1
                resp = requests.post(url_chat, headers=headers, json=payload, timeout=timeout)
                if resp.status_code >= 400:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    continue
                j = resp.json()
                content = j.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                data = self._safe_parse_json(content)
                if data:
                    break
                last_err = f"invalid JSON: {content[:200]}"
            except Exception as e:
                last_err = str(e)

        if not data:
            self._stats["failures"] += 1
            return None

        category = self._map_to_known_category(data.get("category", "未分类"), categories)
        confidence = float(data.get("confidence", 0.0))
        reasons = data.get("reasons") or data.get("reason") or []
        if isinstance(reasons, str):
            reasons = [reasons]

        result = {
            "category": category,
            "confidence": max(0.0, min(1.0, confidence)),
            "reasoning": [f"LLM: {r}" for r in reasons],
            "method": "llm",
            "facets": data.get("facets") or {},
            "subcategory": data.get("subcategory"),
            "priority_tags": data.get("priority_tags", []),
        }
        self._cache[h] = result
        return result

    def get_stats(self) -> Dict:
        return dict(self._stats)

    # -------------------- Internal helpers --------------------
    def _load_config(self) -> Dict:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _strip_category_prefix(text: str) -> str:
        if not text:
            return ""
        s = str(text).strip()
        i = 0
        while i < len(s) and not ("\u4e00" <= s[i] <= "\u9fff" or s[i].isalnum()):
            i += 1
        return s[i:].strip() if i < len(s) else s

    def _normalize_category_string(self, category: str) -> str:
        if not category:
            return ""
        cat = str(category).strip()
        if not cat:
            return ""
        if '/' in cat:
            main, sub = cat.split('/', 1)
            main_n = self._strip_category_prefix(main)
            sub_n = self._strip_category_prefix(sub)
            return f"{main_n}/{sub_n}" if sub_n else main_n
        return self._strip_category_prefix(cat)

    def _collect_valid_categories(self, config: Dict) -> List[str]:
        cats = []
        if isinstance(config.get("category_order"), list):
            for x in config["category_order"]:
                nx = self._normalize_category_string(str(x))
                if nx and nx not in cats:
                    cats.append(nx)
        # 也收集 category_rules 的顶层键
        rules = config.get("category_rules", {}) or {}
        for k in rules.keys():
            nk = self._normalize_category_string(k)
            if nk and nk not in cats:
                cats.append(nk)
        # 最后补充“未分类”
        if "未分类" not in cats:
            cats.append("未分类")
        return cats

    def _map_to_known_category(self, cat: str, valid: List[str]) -> str:
        cat_n = self._normalize_category_string(cat)
        if not cat_n:
            return "未分类"
        # 直接匹配
        if cat_n in valid:
            return cat_n
        # 忽略大小写和两端空白试匹配
        low = cat_n.strip().lower()
        for v in valid:
            if v.strip().lower() == low:
                return v
        # 允许用 '/' 拆分选择主分类
        if '/' in cat_n:
            main = cat_n.split('/', 1)[0].strip()
            for v in valid:
                if v.strip().lower() == main.lower():
                    return v
        return "未分类"

    def _safe_parse_json(self, text: str) -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None
        # 容错：裁剪围绕的 ```json ``` 包裹
        if text.startswith("```"):
            # 去掉围栏
            text = text.strip('`')
            # 去掉可能的 json 标记
            text = text.replace("json\n", "", 1)
        try:
            return json.loads(text)
        except Exception:
            # 再尝试一次：寻找首个 '{' 到最后一个 '}'
            try:
                start = text.find('{')
                end = text.rfind('}')
                if start >= 0 and end > start:
                    return json.loads(text[start:end+1])
            except Exception:
                return None
        return None

    def _build_category_library(self, categories: List[str]) -> List[Dict[str, str]]:
        library = []
        for name in categories:
            entry = {"name": name, "description": ""}
            if "/" in name:
                main, sub = name.split("/", 1)
                entry["parent"] = main
                entry["description"] = f"{main} 下的 {sub}"
            else:
                entry["parent"] = None
                entry["description"] = f"主分类 {name}"
            library.append(entry)
        return library

    def _build_bookmark_payload(self, url: str, title: str, context: Dict[str, any]) -> Dict[str, any]:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path_segments = [seg for seg in parsed.path.split("/") if seg]
        query_params = parse_qs(parsed.query)

        keywords = self._extract_keywords(title)

        payload = {
            "url": url,
            "title": title,
            "domain": domain,
            "path_segments": path_segments[:8],
            "query_params": {k: v[:5] for k, v in query_params.items()},
            "keywords": keywords[:12],
            "context": context,
        }
        return payload

    def _build_hint_profile(self, url: str, title: str, bookmark_payload: Dict[str, any]) -> Dict[str, any]:
        title_lower = title.lower()
        hints: Dict[str, any] = {
            "contains_code": any(token in title_lower for token in ["github", "repo", "代码", "编程"]),
            "contains_doc": any(token in title_lower for token in ["doc", "文档", "documentation"]),
            "likely_video": self._is_video_url(url),
            "likely_news": any(token in title_lower for token in ["news", "资讯", "快讯"]),
            "likely_forum": any(token in bookmark_payload["domain"] for token in ["forum", "bbs", "community"]),
        }
        hints["language"] = self._detect_language(title)
        hints["secure_scheme"] = url.lower().startswith("https://")
        return hints

    def _extract_keywords(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-zA-Z\u4e00-\u9fff]{2,}", text.lower())
        seen = set()
        keywords = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                keywords.append(token)
        return keywords

    def _detect_language(self, text: str) -> str:
        if re.search(r"[\u4e00-\u9fff]", text):
            return "zh"
        if re.search(r"[a-zA-Z]", text):
            return "en"
        return "unknown"

    def _is_video_url(self, url: str) -> bool:
        lower = url.lower()
        return any(host in lower for host in ["youtube.com", "bilibili.com", "vimeo.com"])
