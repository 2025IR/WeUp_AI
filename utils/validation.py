from typing import Dict, List, Tuple

def validate_params(schema: Dict, params: Dict) -> Tuple[bool, List[str]]:
    required = schema["parameters"].get("required", [])
    missing = [k for k in required if k not in params or params.get(k) in (None, "", [])]
    return (len(missing) == 0), missing