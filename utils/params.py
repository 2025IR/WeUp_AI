# capstone_ai/utils/params.py
from typing import Dict, Any, Tuple, List

def apply_defaults_and_coerce(schema: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """schema.parameters.properties 의 default/enum/type 에 맞게 기본값과 타입을 보정."""
    props = schema.get("parameters", {}).get("properties", {}) or {}
    out = dict(params or {})
    for k, p in props.items():
        if k not in out and "default" in p:
            out[k] = p["default"]
        # 간단한 타입 보정(문자→숫자 등) — 필요 시 확장
        if k in out and isinstance(out[k], str):
            if p.get("type") == "number":
                try:
                    out[k] = float(out[k]) if "." in out[k] else int(out[k])
                except Exception:
                    pass
    return out

def validate_required(schema: Dict[str, Any], params: Dict[str, Any]) -> Tuple[bool, List[str]]:
    required = schema.get("parameters", {}).get("required", []) or []
    missing = [k for k in required if k not in params or params.get(k) in (None, "", [])]
    return (len(missing) == 0), missing