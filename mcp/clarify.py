from typing import Any, Dict, List

class ClarifyManager:
    def __init__(self):
        self._pending: Dict[str, Dict[str, Any]] = {}

    def has(self, cid: str) -> bool:
        return cid in self._pending

    def set_pending(self, cid: str, tool_name: str, schema: Dict[str, Any], collected: Dict[str, Any]):
        self._pending[cid] = {
            "tool_name": tool_name,
            "schema": schema,
            "required": schema["parameters"].get("required", []),
            "collected": collected,
        }

    def get(self, cid: str) -> Dict[str, Any]:
        return self._pending[cid]

    def update_collected(self, cid: str, merged: Dict[str, Any]):
        self._pending[cid]["collected"] = merged

    def clear(self, cid: str):
        if cid in self._pending:
            del self._pending[cid]

    def make_question_kor(self, tool_name: str, schema: Dict[str, Any], missing: List[str]) -> str:
        props = schema["parameters"].get("properties", {})
        bullets = []
        for k in missing:
            desc = props.get(k, {}).get("description", "")
            bullets.append(f"- {k}: {desc}" if desc else f"- {k}")
        return (
            f"요청을 처리하려면 다음 정보가 필요합니다(도구: {tool_name}).\n"
            f"부족한 항목을 알려주세요:\n" + "\n".join(bullets) +
            "\n\n예: location 은 'Seoul, KR' 형식으로 답해주세요."
        )