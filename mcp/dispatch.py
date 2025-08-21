from __future__ import annotations
from typing import Dict, Any, List, Optional

class ToolDispatcher:
    """
    툴 이름과 파라미터/컨텍스트를 보고, 해당 API 스펙을 돌려줍니다.
    - 화이트리스트(안전)
    - 필요 시 프로젝트/환경별 분기 지원
    """
    def __init__(self, table: Dict[str, Any]):
        self.table = table

    def pick(self, tool: str, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        if tool not in self.table:
            raise ValueError(f"Unknown tool: {tool}")

        entry = self.table[tool]
        if isinstance(entry, list):
            for rule in entry:
                if self._match(rule.get("when", {}), params, context):
                    return rule["exec"]
            raise ValueError(f"No matching exec rule for tool={tool}")
        return entry["exec"] if "exec" in entry else entry

    def _match(self, cond: Dict[str, Any], params: Dict[str, Any], context: Dict[str, Any]) -> bool:
        pid = params.get("project_id") or context.get("project_id")
        env = (context.get("env") or "").lower()

        if "project_id_in" in cond:
            try:
                if int(pid) not in set(int(x) for x in cond["project_id_in"]):
                    return False
            except Exception:
                return False
        if "env_equals" in cond:
            if env != str(cond["env_equals"]).lower():
                return False
        if "tool_equals" in cond:
            if cond["tool_equals"] != params.get("_tool", context.get("_tool")):
                return False
        return True