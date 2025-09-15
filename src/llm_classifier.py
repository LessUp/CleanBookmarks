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

import os
import json
import hashlib
from typing import Dict, List, Optional, Tuple
import requests

_DEFAULT_SYSTEM_PROMPT = (
    "你是一个严格的书签分类助手。\n"
    "只从我提供的“有效类别列表”中选择一个最合适的类别；不要编造新类别。\n"
    "输出严格为 JSON：{category: 字符串, confidence: 0.0~1.0, reasons: [字符串,...]}。\n"
    "如果无法判断，category 返回 '未分类' 且 confidence 为 0.0。\n"
)

class LLMClassifier:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.llm_conf = self.config.get("llm", {}) or {}
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
        system_prompt = _DEFAULT_SYSTEM_PROMPT + "\n有效类别列表：\n" + "\n".join(f"- {c}" for c in categories)

        user_content = {
            "url": url,
            "title": title,
            "context": context or {},
            "instruction": "请仅选择一个最合适的类别，并给出 1~3 条简要理由。",
        }

        payload = {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)}
            ]
        }

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
            "method": "llm"
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

    def _collect_valid_categories(self, config: Dict) -> List[str]:
        cats = []
        if isinstance(config.get("category_order"), list):
            cats.extend([str(x) for x in config["category_order"]])
        # 也收集 category_rules 的顶层键
        rules = config.get("category_rules", {}) or {}
        for k in rules.keys():
            if k not in cats:
                cats.append(k)
        # 最后补充“未分类”
        if "未分类" not in cats:
            cats.append("未分类")
        return cats

    def _map_to_known_category(self, cat: str, valid: List[str]) -> str:
        if not cat:
            return "未分类"
        # 直接匹配
        if cat in valid:
            return cat
        # 忽略大小写和两端空白试匹配
        low = cat.strip().lower()
        for v in valid:
            if v.strip().lower() == low:
                return v
        # 允许用 '/' 拆分选择主分类
        if '/' in cat:
            main = cat.split('/', 1)[0].strip()
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
