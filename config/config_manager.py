"""
H.Huddair's Nexus-Pulse - Level 1
Dynamic Config Engine: Manages dynamic JSON & YAML runtime configurations.
Synchronizes target_country, target_city, industry_niche, and ready_to_send safety switch.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_DIR = Path(__file__).resolve().parent
YAML_PATH = CONFIG_DIR / "settings.yaml"
JSON_PATH = CONFIG_DIR / "settings.json"


def _clean_yaml_value(val_str: str) -> Any:
    val_str = val_str.strip()
    if val_str.lower() == "true":
        return True
    if val_str.lower() == "false":
        return False
    if val_str.lower() in ("null", "none"):
        return None
    if (val_str.startswith('"') and val_str.endswith('"')) or (val_str.startswith("'") and val_str.endswith("'")):
        return val_str[1:-1]
    try:
        if "." in val_str:
            return float(val_str)
        return int(val_str)
    except ValueError:
        return val_str


def parse_simple_yaml(text: str) -> Dict[str, Any]:
    """Pure-python fallback YAML reader for key-value, sections, and string lists."""
    result: Dict[str, Any] = {}
    current_section = None
    current_list_key = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.strip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        # Check list item
        if stripped.startswith("- "):
            item = stripped[2:].strip().strip('"').strip("'")
            if current_list_key:
                if current_section:
                    result[current_section][current_list_key].append(item)
                else:
                    result[current_list_key].append(item)
            continue

        # Check key-value or section
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            key = k.strip()
            val = v.strip()

            if indent == 0:
                current_list_key = None
                if not val:
                    # New top-level section
                    current_section = key
                    result[current_section] = {}
                else:
                    current_section = None
                    result[key] = _clean_yaml_value(val)
            else:
                # Sub-key inside section
                if not val:
                    # Could be list
                    current_list_key = key
                    if current_section:
                        result[current_section][current_list_key] = []
                    else:
                        result[current_list_key] = []
                else:
                    current_list_key = None
                    if current_section:
                        result[current_section][key] = _clean_yaml_value(val)
                    else:
                        result[key] = _clean_yaml_value(val)

    return result


def dump_simple_yaml(data: Dict[str, Any]) -> str:
    """Pure-python clean YAML dumper for nested dictionaries and lists."""
    lines = ["# H.Huddair's Nexus-Pulse Dynamic Configuration", ""]
    
    # Priority root keys first
    priority_keys = ["target_country", "target_city", "industry_niche", "ready_to_send"]
    for pk in priority_keys:
        if pk in data:
            v = data[pk]
            if isinstance(v, bool):
                lines.append(f"{pk}: {str(v).lower()}")
            elif isinstance(v, str):
                lines.append(f'{pk}: "{v}"')
            else:
                lines.append(f"{pk}: {v}")

    lines.append("")

    for k, v in data.items():
        if k in priority_keys:
            continue
        if isinstance(v, dict):
            lines.append(f"{k}:")
            for sub_k, sub_v in v.items():
                if isinstance(sub_v, list):
                    lines.append(f"  {sub_k}:")
                    for item in sub_v:
                        lines.append(f'    - "{item}"')
                elif isinstance(sub_v, bool):
                    lines.append(f"  {sub_k}: {str(sub_v).lower()}")
                elif isinstance(sub_v, str):
                    lines.append(f'  {sub_k}: "{sub_v}"')
                else:
                    lines.append(f"  {sub_k}: {sub_v}")
            lines.append("")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f'  - "{item}"')
        else:
            if isinstance(v, bool):
                lines.append(f"{k}: {str(v).lower()}")
            elif isinstance(v, str):
                lines.append(f'{k}: "{v}"')
            else:
                lines.append(f"{k}: {v}")

    return "\n".join(lines) + "\n"


class DynamicConfigManager:
    """
    Enterprise Dynamic Config Manager.
    Reads/writes both JSON and YAML, keeping them synchronized in real time.
    """

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> Dict[str, Any]:
        """Reload configuration from disk, preferring JSON if present, then YAML."""
        if JSON_PATH.exists():
            try:
                with open(JSON_PATH, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                    return self._config
            except Exception:
                pass

        if YAML_PATH.exists():
            try:
                with open(YAML_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                self._config = parse_simple_yaml(content)
                self.save_all()  # sync to json
                return self._config
            except Exception:
                pass

        # Fallback defaults
        self._config = {
            "target_country": "Germany",
            "target_city": "Berlin",
            "industry_niche": "Commercial Construction & General Contractors",
            "ready_to_send": False,
            "system": {"app_name": "H.Huddair's Nexus-Pulse", "version": "1.0.0"}
        }
        self.save_all()
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Fetch config property with dot notation support (e.g., 'crawler.search_depth')."""
        if "." in key:
            parts = key.split(".")
            curr = self._config
            for part in parts:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                else:
                    return default
            return curr
        return self._config.get(key, default)

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """Update a config property with dot notation support and auto-sync."""
        if "." in key:
            parts = key.split(".")
            curr = self._config
            for part in parts[:-1]:
                if part not in curr or not isinstance(curr[part], dict):
                    curr[part] = {}
                curr = curr[part]
            curr[parts[-1]] = value
        else:
            self._config[key] = value

        if persist:
            self.save_all()

    def update(self, updates: Dict[str, Any]) -> None:
        """Batch update configuration values."""
        for k, v in updates.items():
            self.set(k, v, persist=False)
        self.save_all()

    def save_all(self) -> None:
        """Persist config to both settings.json and settings.yaml simultaneously."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Write JSON
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
        # Write YAML
        yaml_content = dump_simple_yaml(self._config)
        with open(YAML_PATH, "w", encoding="utf-8") as f:
            f.write(yaml_content)

    @property
    def target_country(self) -> str:
        return self.get("target_country", "Germany")

    @property
    def target_city(self) -> str:
        return self.get("target_city", "Berlin")

    @property
    def industry_niche(self) -> str:
        return self.get("industry_niche", "Commercial Construction")

    @property
    def ready_to_send(self) -> bool:
        return bool(self.get("ready_to_send", False))

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._config)


_global_config = None

def get_config() -> DynamicConfigManager:
    global _global_config
    if _global_config is None:
        _global_config = DynamicConfigManager()
    return _global_config
