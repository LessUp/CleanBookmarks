import os
import re
import yaml
from typing import Dict, Optional, Tuple


class TaxonomyStandardizer:
    def __init__(self, config: Dict):
        self.config = config or {}
        self._subjects_map: Dict[str, str] = {}
        self._resource_types_map: Dict[str, str] = {}
        self._load_subjects()
        self._load_resource_types()

    def _get_path(self, key: str, default_path: str) -> str:
        tax = self.config.get("taxonomy", {}) or {}
        return tax.get(key, default_path)

    def _load_yaml(self, path: str) -> Dict:
        if not path or not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def _load_subjects(self):
        path = self._get_path("subjects_file", "taxonomy/subjects.yaml")
        data = self._load_yaml(path)
        subjects = data.get("subjects", []) or []
        for entry in subjects:
            preferred = str(entry.get("preferred", "")).strip()
            if not preferred:
                continue
            self._subjects_map[preferred.lower()] = preferred
            for v in entry.get("variants", []) or []:
                v = str(v).strip()
                if v:
                    self._subjects_map[v.lower()] = preferred

    def _load_resource_types(self):
        path = self._get_path("resource_types_file", "taxonomy/resource_types.yaml")
        data = self._load_yaml(path)
        rts = data.get("resource_types", {}) or {}
        for key, meta in rts.items():
            key_l = str(key).strip().lower()
            if key_l:
                self._resource_types_map[key_l] = key
            variants = (meta or {}).get("variants", []) or []
            for v in variants:
                v = str(v).strip()
                if v:
                    self._resource_types_map[v.lower()] = key

    def _strip_prefix(self, text: str) -> str:
        if not text:
            return ""
        s = str(text).strip()
        i = 0
        while i < len(s) and not ("\u4e00" <= s[i] <= "\u9fff" or s[i].isalnum()):
            i += 1
        return s[i:] if i < len(s) else s

    def normalize_subject(self, text: str) -> Optional[str]:
        if not text:
            return None
        t = self._strip_prefix(text)
        low = t.lower()
        return self._subjects_map.get(low, t)

    def normalize_resource_type(self, text: str) -> Optional[str]:
        if not text:
            return None
        t = self._strip_prefix(text)
        low = t.lower()
        return self._resource_types_map.get(low)

    def derive_from_category(self, category: str, content_type: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        if not category:
            return None, None
        cat = str(category).strip()
        main = cat
        sub = None
        if "/" in cat:
            parts = cat.split("/", 1)
            main = parts[0].strip()
            sub = parts[1].strip()
        subject = self.normalize_subject(main)
        resource_type = self.normalize_resource_type(sub) if sub else None
        if not resource_type and content_type:
            ct_map = {
                "code_repository": "code_repository",
                "documentation": "documentation",
                "video": "video",
                "academic_paper": "paper",
                "news": "news",
                "online_tool": "tool",
                "webpage": "webpage",
            }
            resource_type = ct_map.get(content_type)
        return subject, resource_type
