"""
LLM Prompt Builder

负责构建高质量的提示词，以便 LLM 更准确地完成书签分类。
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Tuple


class LLMPromptBuilder:
    """集中处理 prompt 构建逻辑，便于复用与配置。"""

    DEFAULT_STEPS = [
        "解析书签的标题、URL、域名、上下文，识别主题与意图。",
        "将识别出的意图映射到提供的类别库，必要时推测最匹配的主/子分类。",
        "校验置信度范围 [0,1]，并用 JSON 输出最终结果。",
    ]

    DEFAULT_EXPECTED_KEYS = {
        "category": "最终的主分类或主/子分类字符串（必须来自提供的类别列表）",
        "confidence": "0~1 的浮点数，代表置信度；若不确定应降低分值。",
        "reasons": ["1~3 条简短中文理由，解释分类依据。"],
        "subcategory": "可选，若主分类下还可细分则给出。",
        "facets": {
            "resource_type_hint": "可选，指出内容形态，如教程、文档、视频。"
        },
        "priority_tags": ["可选，推荐使用的重点标签，如 '需要跟进'。"],
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        llm_conf = config.get("llm") or {}
        prompt_conf = llm_conf.get("prompt") or {}

        self._steps: List[str] = prompt_conf.get("steps") or self.DEFAULT_STEPS
        self._task_description: str = prompt_conf.get(
            "task_description",
            "请以智能代理的方式，完成浏览器书签的精准分类。",
        )
        self._scoring_notes: str = prompt_conf.get(
            "scoring_notes",
            "当置信度不足或类别不在列表中时，请返回 '未分类'，同时给出最主要的疑惑点。",
        )
        self._force_json: bool = prompt_conf.get("force_json", True)
        self._few_shots: List[Dict[str, Any]] = prompt_conf.get("few_shots") or []
        self._expected_schema: Dict[str, Any] = prompt_conf.get(
            "expected_schema", self.DEFAULT_EXPECTED_KEYS
        )

    # ------------------------------------------------------------------ #
    # 公共接口
    # ------------------------------------------------------------------ #
    def build_messages(
        self,
        *,
        bookmark: Dict[str, Any],
        hints: Dict[str, Any],
        category_library: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, str]], Optional[Dict[str, str]]]:
        """生成发送给 OpenAI 接口的 messages。"""
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt(category_library)}
        ]

        # Few-shot 示范
        for shot in self._few_shots:
            user_payload = {
                "demo": True,
                "bookmark": shot.get("bookmark", {}),
                "hints": shot.get("hints", {}),
                "category_library": self._trim_category_library(
                    category_library, shot.get("category_whitelist")
                ),
            }
            assistant_payload = shot.get("expected", {})
            if not assistant_payload:
                continue
            messages.append(
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False),
                }
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": json.dumps(assistant_payload, ensure_ascii=False),
                }
            )

        # 实际任务
        request_payload = {
            "task": self._task_description,
            "bookmark": bookmark,
            "hints": hints,
            "category_library": category_library,
            "workflow": self._steps,
            "expected_output_keys": self._expected_schema,
            "notes": self._scoring_notes,
        }
        messages.append(
            {"role": "user", "content": json.dumps(request_payload, ensure_ascii=False)}
        )

        response_format = {"type": "json_object"} if self._force_json else None
        return messages, response_format

    # ------------------------------------------------------------------ #
    # 内部辅助
    # ------------------------------------------------------------------ #
    def _build_system_prompt(
        self, category_library: List[Dict[str, Any]]
    ) -> str:
        """构建 system prompt。"""
        primary_categories = [
            entry["name"]
            for entry in category_library
            if "/" not in entry["name"]
        ]
        primary_hint = ", ".join(primary_categories[:12])

        steps_text = "\n".join(f"{idx+1}. {step}" for idx, step in enumerate(self._steps))

        schema_preview = json.dumps(
            self._expected_schema, ensure_ascii=False, indent=2
        )

        return (
            "你是 CleanBook-Agent，一名资深浏览器书签信息架构师。\n"
            "目标：在保持原始信息完整的前提下，为书签匹配最合适的分类，并输出结构化结果。\n"
            f"主分类参考（部分）：{primary_hint}\n"
            "请务必遵循以下工作流：\n"
            f"{steps_text}\n\n"
            "输出要求：\n"
            "- 严格使用 JSON，不添加额外文本。\n"
            "- 仅使用提供的类别，允许返回 '未分类'。\n"
            "- 置信度需与理由一致，避免夸大。\n"
            "- 若怀疑需要手动整理，可在 facets.priority_tags 中加入 'review'.\n\n"
            f"JSON 字段说明示例：\n{schema_preview}\n"
            "开始之前，请先充分分析信息，然后再给出最终 JSON。"
        )

    def _trim_category_library(
        self,
        library: List[Dict[str, Any]],
        whitelist: Optional[Iterable[str]],
    ) -> List[Dict[str, Any]]:
        """按需裁剪类别库，用于 few-shot 示例。"""
        if not whitelist:
            return library

        whitelist_set = set(whitelist)
        return [entry for entry in library if entry["name"] in whitelist_set]

    # ------------------------------------------------------------------ #
    # 属性
    # ------------------------------------------------------------------ #
    @property
    def force_json(self) -> bool:
        return self._force_json
