import json
from typing import Any, Dict

def parse_json_object(text: str) -> Dict[str, Any]:
    """가장 바깥 한 개의 JSON 객체만 파싱 (간단·견고)"""
    s = text.find("{"); e = text.rfind("}")
    if s == -1 or e == -1 or e < s:
        return {}
    try:
        return json.loads(text[s:e+1])
    except Exception:
        return {}