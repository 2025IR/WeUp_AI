from typing import Any, Dict
import requests, uuid
from capstone_ai.config import MCP_AUTH_HEADER, MCP_AUTH_TOKEN

class MCPClient:
    """단순 HTTP JSON-RPC 2.0 클라이언트. 엔드포인트가 ws:// 인 경우는 주석 안내 참조."""
    def __init__(self, endpoint: str, timeout: int = 30):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def call_tool(self, name: str, args: Dict[str, Any], timeout: int | None = None) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": name,
            "params": args or {}
        }
        headers = {}
        if MCP_AUTH_TOKEN:
            headers[MCP_AUTH_HEADER] = MCP_AUTH_TOKEN 
        r = requests.post(self.endpoint, json=payload, headers=headers, timeout=timeout or self.timeout)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"MCP error {data['error']}")
        return data.get("result")
