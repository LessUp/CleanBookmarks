"""
LLM Bookmark Organizer

利用 OpenAI 兼容接口对已分类书签进行二次聚类、分组与洞察总结。

设计目标：
- 通过汇总后的类别画像，将整体整理任务交给 LLM 完成；
- 输出稳定的 JSON，便于落地到既有导出流水线；
- 失败时自动回退到传统分类结构，不影响主流程。
"""
from __future__ import annotations

import json
import logging
import os
import hashlib
from collections import Counter
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

_SYSTEM_PROMPT = (
    "You are an elite bookmark knowledge architect. "
    "Reorganize categories for maximum clarity and usefulness. "
    "Always respond with strict JSON. "
    "The JSON must contain the keys: category_mapping, primary_order, secondary_order, "
    "fallback_primary, fallback_secondary_label, category_insights and optional notes. "
    "Never invent bookmarks; only reorganize what is provided. "
    "Prefer concise yet expressive Chinese labels when appropriate."
)


@dataclass
class LLMOrganizerStats:
    enabled: bool = False
    calls: int = 0
    cache_hits: int = 0
    failures: int = 0


class LLMBookmarkOrganizer:
    """通过 LLM 生成更高层次的书签组织结构。"""

    def __init__(self, config_path: str = "config.json", config: Optional[Dict[str, Any]] = None):
        self.config_path = config_path
        self.config = config or self._load_config()
        self.llm_conf: Dict[str, Any] = self.config.get("llm", {}) or {}
        self.organizer_conf: Dict[str, Any] = self.llm_conf.get("organizer", {}) or {}
        self.logger = logging.getLogger(__name__)

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = LLMOrganizerStats(
            enabled=self.enabled(),
            calls=0,
            cache_hits=0,
            failures=0,
        )

        self._model = self.organizer_conf.get("model") or self.llm_conf.get("model", "gpt-4o-mini")
        self._temperature = float(self.organizer_conf.get("temperature", self.llm_conf.get("temperature", 0.0)))
        self._top_p = float(self.organizer_conf.get("top_p", self.llm_conf.get("top_p", 1.0)))
        self._timeout = int(self.organizer_conf.get("timeout_seconds", self.llm_conf.get("timeout_seconds", 40)))
        self._max_retries = int(self.organizer_conf.get("max_retries", self.llm_conf.get("max_retries", 1)))
        self._max_tokens = int(self.organizer_conf.get("max_tokens", 1800))
        self._force_json = bool(self.organizer_conf.get("force_json", True))

    # ------------------------------------------------------------------ #
    # 公共接口
    # ------------------------------------------------------------------ #
    def enabled(self) -> bool:
        if not self.llm_conf.get("enable", False):
            return False
        organizer_enable = self.organizer_conf.get("enable")
        if organizer_enable is None:
            # 默认跟随上层 llm.enable
            return True
        return bool(organizer_enable)

    def organize(
        self,
        bookmarks: List[Dict[str, Any]],
        baseline: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """使用 LLM 生成新的组织结构。"""
        if not self.enabled():
            return None

        api_key_env = self.llm_conf.get("api_key_env", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_env, "")
        if not api_key:
            self.logger.debug("LLM Organizer skipped: API key not provided.")
            return None

        if not bookmarks:
            return None

        dataset_summary = self._build_dataset_summary(bookmarks)
        if not dataset_summary["categories"]:
            return None

        llm_payload = self._build_llm_payload(dataset_summary)
        llm_response = self._call_llm(api_key, llm_payload)
        if not llm_response:
            return None

        try:
            mapping = llm_response.get("category_mapping") or {}
            primary_order = llm_response.get("primary_order") or []
            secondary_order = llm_response.get("secondary_order") or {}
            fallback_primary = llm_response.get("fallback_primary") or "其他"
            fallback_secondary = llm_response.get("fallback_secondary_label") or None

            organized = self._apply_mapping(
                bookmarks=bookmarks,
                mapping=mapping,
                primary_order=primary_order,
                secondary_order=secondary_order,
                fallback_primary=fallback_primary,
                fallback_secondary=fallback_secondary,
            )

            meta = {
                "llm_model": self._model,
                "primary_order": primary_order,
                "fallback_primary": fallback_primary,
                "fallback_secondary": fallback_secondary,
                "category_insights": llm_response.get("category_insights", []),
                "notes": llm_response.get("notes", []),
                "organizer_stats": self.get_stats(),
            }

            return {
                "organized": organized,
                "meta": meta,
                "raw_llm_response": llm_response,
                "summary_input": dataset_summary,
            }
        except Exception as exc:
            self.logger.warning(f"LLM organizer mapping failed, fallback to baseline: {exc}")
            return {"organized": baseline or {}, "meta": {"error": str(exc)}}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "enabled": self._stats.enabled,
            "calls": self._stats.calls,
            "cache_hits": self._stats.cache_hits,
            "failures": self._stats.failures,
        }

    # ------------------------------------------------------------------ #
    # 构建 LLM 输入
    # ------------------------------------------------------------------ #
    def _build_dataset_summary(self, bookmarks: List[Dict[str, Any]]) -> Dict[str, Any]:
        max_examples = int(self.organizer_conf.get("max_examples_per_category", 5))
        max_domains = int(self.organizer_conf.get("max_domains_per_category", 5))
        summaries: List[Dict[str, Any]] = []

        by_category: Dict[str, Dict[str, Any]] = {}
        for bookmark in bookmarks:
            category = (bookmark.get("category") or "未分类").strip() or "未分类"
            bucket = by_category.setdefault(
                category,
                {
                    "titles": [],
                    "domains": Counter(),
                    "confidences": [],
                    "total": 0,
                },
            )
            bucket["total"] += 1
            bucket["confidences"].append(float(bookmark.get("confidence", 0.0)))

            title = bookmark.get("title")
            if title and len(bucket["titles"]) < max_examples:
                bucket["titles"].append(title[:160])

            domain = urlparse(bookmark.get("url", "")).netloc.lower().replace("www.", "")
            if domain:
                bucket["domains"][domain] += 1

        for category, payload in by_category.items():
            confidences = payload["confidences"] or [0.0]
            summaries.append(
                {
                    "category": category,
                    "count": payload["total"],
                    "avg_confidence": round(mean(confidences), 3),
                    "confidence_bins": self._confidence_bins(confidences),
                    "top_domains": [d for d, _ in payload["domains"].most_common(max_domains)],
                    "sample_titles": payload["titles"],
                }
            )

        summaries.sort(key=lambda item: item["count"], reverse=True)

        return {
            "bookmark_count": len(bookmarks),
            "categories": summaries,
            "existing_category_order": self.config.get("category_order", []),
        }

    def _build_llm_payload(self, dataset_summary: Dict[str, Any]) -> Dict[str, Any]:
        instructions = {
            "task": "Reorganize bookmark categories with multi-level grouping.",
            "constraints": [
                "Keep the number of primary categories manageable (ideally 6~12).",
                "Ensure each primary category groups semantically coherent bookmarks.",
                "Use secondary categories only when they clarify intent or media type.",
                "Prefer maintaining existing emotional icons (emoji) when they carry meaning.",
                "If a category has very low confidence or mixed content, merge it into the fallback bucket.",
            ],
            "expected_output": {
                "category_mapping": "Map original category string to {primary: str, secondary: Optional[str]}",
                "primary_order": "Ordered list of primary category names for final rendering",
                "secondary_order": "Dict[primary] -> list of secondary names in desired order",
                "fallback_primary": "Name of the default bucket for uncategorised items",
                "fallback_secondary_label": "Optional label for sub-bucket inside fallback",
                "category_insights": "Array of {primary, summary, recommendations}",
                "notes": "Optional array of global suggestions or clean-up ideas",
            },
            "dataset": dataset_summary,
        }

        user_content = json.dumps(instructions, ensure_ascii=False)

        payload: Dict[str, Any] = {
            "model": self._model,
            "temperature": self._temperature,
            "top_p": self._top_p,
            "max_tokens": self._max_tokens,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        }

        if self._force_json:
            payload["response_format"] = {"type": "json_object"}

        return payload

    # ------------------------------------------------------------------ #
    # LLM 调用
    # ------------------------------------------------------------------ #
    def _call_llm(self, api_key: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cache_key = hashlib.md5(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        if cache_key in self._cache:
            self._stats.cache_hits += 1
            return self._cache[cache_key]

        base_url = (self.llm_conf.get("base_url") or "https://api.openai.com").rstrip("/")
        url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        last_error: Optional[str] = None
        for _ in range(self._max_retries + 1):
            try:
                self._stats.calls += 1
                response = requests.post(url, headers=headers, json=payload, timeout=self._timeout)
                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    continue

                body = response.json()
                content = (
                    body.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )

                parsed = self._safe_parse_json(content)
                if parsed:
                    self._cache[cache_key] = parsed
                    return parsed

                last_error = f"Invalid JSON from LLM: {content[:200]}"
            except Exception as exc:
                last_error = str(exc)

        self._stats.failures += 1
        if last_error:
            self.logger.warning(f"LLM organizer call failed: {last_error}")
        return None

    # ------------------------------------------------------------------ #
    # JSON 解析与映射
    # ------------------------------------------------------------------ #
    def _safe_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        text = (text or "").strip()
        if not text:
            return None
        if text.startswith("```"):
            text = text.strip("`")
            text = text.replace("json\n", "", 1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    return json.loads(text[start : end + 1])
            except Exception:
                return None
        return None

    def _apply_mapping(
        self,
        bookmarks: List[Dict[str, Any]],
        mapping: Dict[str, Dict[str, Optional[str]]],
        primary_order: List[str],
        secondary_order: Dict[str, List[str]],
        fallback_primary: str,
        fallback_secondary: Optional[str],
    ) -> Dict[str, Any]:
        organized: Dict[str, Dict[str, Any]] = {}

        for bookmark in bookmarks:
            original_category = (bookmark.get("category") or "未分类").strip() or "未分类"
            map_entry = mapping.get(original_category, {})

            primary = (map_entry.get("primary") or fallback_primary or original_category.split("/", 1)[0]).strip()
            if not primary:
                primary = fallback_primary or "未分类"

            secondary = map_entry.get("secondary")
            if secondary:
                secondary = secondary.strip() or None

            node = organized.setdefault(primary, {"_items": [], "_subcategories": {}})

            if secondary:
                node["_subcategories"].setdefault(secondary, {"_items": []})["_items"].append(bookmark)
            else:
                node["_items"].append(bookmark)

        # 将不在 mapping 中但仍需保留的分类加入 fallback
        for bookmark in bookmarks:
            original_category = (bookmark.get("category") or "未分类").strip() or "未分类"
            if original_category in mapping:
                continue
            # 如果已经分配则跳过；否则放入 fallback
            primary = fallback_primary or "未分类"
            node = organized.setdefault(primary, {"_items": [], "_subcategories": {}})
            if fallback_secondary:
                node["_subcategories"].setdefault(fallback_secondary, {"_items": []})["_items"].append(bookmark)
            else:
                node["_items"].append(bookmark)

        # 排序主分类
        ordered: Dict[str, Dict[str, Any]] = {}
        temp = dict(organized)
        for primary in primary_order:
            if primary in temp:
                ordered[primary] = temp.pop(primary)

        if temp:
            remaining = sorted(
                temp.items(),
                key=lambda item: self._count_items(item[1]),
                reverse=True,
            )
            for key, value in remaining:
                ordered[key] = value

        # 排序子分类与条目
        for primary, node in ordered.items():
            node["_items"].sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
            subdict = node["_subcategories"]
            if not subdict:
                continue
            order = secondary_order.get(primary, [])
            sub_temp = dict(subdict)
            new_subdict: Dict[str, Dict[str, Any]] = {}
            for secondary in order:
                if secondary in sub_temp:
                    new_subdict[secondary] = sub_temp.pop(secondary)
            if sub_temp:
                rest = sorted(
                    sub_temp.items(),
                    key=lambda item: self._count_items(item[1]),
                    reverse=True,
                )
                for name, value in rest:
                    new_subdict[name] = value
            for value in new_subdict.values():
                value["_items"].sort(key=lambda x: x.get("confidence", 0.0), reverse=True)
            node["_subcategories"] = new_subdict

        return ordered

    # ------------------------------------------------------------------ #
    # 辅助方法
    # ------------------------------------------------------------------ #
    def _confidence_bins(self, confidences: List[float]) -> Dict[str, int]:
        bins = {"high": 0, "medium": 0, "low": 0}
        for value in confidences:
            if value >= 0.8:
                bins["high"] += 1
            elif value >= 0.5:
                bins["medium"] += 1
            else:
                bins["low"] += 1
        return bins

    def _count_items(self, node: Dict[str, Any]) -> int:
        total = len(node.get("_items", []))
        for sub in node.get("_subcategories", {}).values():
            total += len(sub.get("_items", []))
        return total

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
