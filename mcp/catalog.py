from typing import Dict, List, Optional

class ToolCatalog:
    def __init__(self, tools: List[Dict]):
        self._tools = tools

    def list(self) -> List[Dict]:
        return self._tools

    def find(self, name: str) -> Optional[Dict]:
        for t in self._tools:
            if t["name"] == name:
                return t
        return None