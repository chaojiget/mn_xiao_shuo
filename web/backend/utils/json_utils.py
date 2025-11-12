"""
JSON 解析工具：从 LLM 输出中尽力提取有效 JSON。

特性：
- 去除 ```json 代码块
- 提取首个成对的大括号/中括号 JSON 片段
- 修复常见问题（结尾多余逗号、对象紧邻缺少逗号）
"""

from __future__ import annotations

import json
import re
from typing import Any


def json_loads_relaxed(raw: str) -> Any:
    """宽松解析 JSON 字符串。

    优先 strict 解析，失败后尝试：
    - 去掉 markdown 代码块围栏
    - 提取首个 JSON 片段
    - 修复常见逗号问题
    """
    # 1) 快速路径
    try:
        return json.loads(raw)
    except Exception:
        pass

    s = (raw or "").strip()

    # 2) 去代码块/围栏
    if s.startswith("```json"):
        s = s[len("```json"):]
    if s.startswith("```"):
        s = s[len("```"):]
    if s.endswith("```"):
        s = s[: -len("```")]
    s = s.strip()

    # 3) 提取第一个 JSON 片段（括号配对，忽略字符串内部括号）
    def extract_json_payload(text: str) -> str:
        start_idx = None
        for i, ch in enumerate(text):
            if ch in "[{":
                start_idx = i
                break
        if start_idx is None:
            return text

        stack = []
        in_str = False
        esc = False
        for i in range(start_idx, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            else:
                if c == '"':
                    in_str = True
                    continue
                if c in "[{":
                    stack.append(c)
                elif c in "]}":
                    if stack:
                        stack.pop()
                        if not stack:
                            return text[start_idx : i + 1]
        return text[start_idx:]

    payload = extract_json_payload(s)

    try:
        return json.loads(payload)
    except Exception:
        pass

    # 4) 轻量修复
    fixed = re.sub(r",\s*([}\]])", r"\1", payload)
    fixed = re.sub(r"}\s*\n\s*{", "},{", fixed)
    fixed = re.sub(r"}\s+{", "},{", fixed)

    try:
        return json.loads(fixed)
    except Exception:
        fixed2 = re.sub(r",\s*([}\]])", r"\1", fixed)
        return json.loads(fixed2)

