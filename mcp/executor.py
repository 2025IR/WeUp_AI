from typing import Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ExecSpec:
    type: str               
    name: Optional[str] = None     
    method: Optional[str] = None   
    url: Optional[str] = None      
    mapping: Optional[Dict[str, str]] = None 

class BaseExecutor:
    def execute(self, tool_name: str, params: Dict[str, Any], spec: ExecSpec) -> Dict[str, Any]:
        raise NotImplementedError

class LocalExecutor(BaseExecutor):
    def execute(self, tool_name: str, params: Dict[str, Any], spec: ExecSpec) -> Dict[str, Any]:
        fn = (spec.name or tool_name)
        if fn == "get_current_weather":
            loc = params.get("location", "Seoul, KR")
            unit = params.get("unit", "metric")
            return {"tool": tool_name, "location": loc, "unit": unit, "temp": 28.3, "condition": "Partly Cloudy"}
        if fn == "web_search":
            q = params.get("q", "example")
            k = int(params.get("top_k", 3))
            hits = [{"title": f"Result {i+1} for {q}", "url": f"https://example.com/{i+1}"} for i in range(k)]
            return {"tool": tool_name, "results": hits}
        if fn == "compute_sum":
            nums: List[float] = params.get("numbers", [])
            return {"tool": tool_name, "sum": float(sum(nums))}
        return {"tool": tool_name, "error": f"Unknown local fn: {fn}"}

class MCPExecutor(BaseExecutor):
    def __init__(self, client: "MCPClient"):
        self.client = client

    def execute(self, tool_name: str, params: Dict[str, Any], spec: ExecSpec) -> Dict[str, Any]:
        result = self.client.call_tool(spec.name or tool_name, params, timeout=spec_timeout(spec))
        return {"tool": tool_name, "result": result}

def spec_timeout(spec: ExecSpec) -> int:
    return 30

class HttpExecutor(BaseExecutor):
    def execute(self, tool_name: str, params: Dict[str, Any], spec: ExecSpec) -> Dict[str, Any]:
        import requests, json, logging
        log = logging.getLogger("dna.http")

        method  = (spec.method or "GET").upper()
        mapping = spec.mapping or {}
        url     = spec.url or ""
        if not url:
            return {"tool": tool_name, "error": "HTTP spec.url missing"}

        q, body = {}, {}
        for pk, target in mapping.items():
            if pk in params and params[pk] is not None:
                if target.startswith("query."):
                    q[target.split(".", 1)[1]] = params[pk]
                elif target.startswith("body."):
                    body[target.split(".", 1)[1]] = params[pk]

        headers = {"Accept": "application/json"}  
        timeout = spec_timeout(spec)

        try:
            log.info("[HTTP EXEC] %s %s params=%s body=%s",
                     method, url, q, json.dumps(body, ensure_ascii=False))
        except Exception:
            pass

        try:
            if method == "GET":
                r = requests.get(url, params=q, headers=headers, timeout=timeout)
            else:
                r = requests.request(method, url, params=q, json=(body or None),
                                     headers=headers, timeout=timeout)
            try:
                sent_body = r.request.body
                if isinstance(sent_body, bytes):
                    sent_body = sent_body.decode("utf-8", "ignore")
                log.info("[HTTP EXEC SENT] %s %s sent_body=%s", method, url, sent_body)
            except Exception:
                pass
            content_type = r.headers.get("content-type", "")

            if r.status_code >= 400:
                err_json = None
                try:
                    err_json = r.json()
                except Exception:
                    err_json = None
                return {
                    "tool": tool_name,
                    "http_status": r.status_code,
                    "reason": r.reason,
                    "url": url,
                    "error_code": (err_json or {}).get("error"),
                    "error_message": (err_json or {}).get("message") or r.text[:2000],
                    "response_body": (err_json if err_json is not None else r.text[:2000]),
                }

            data = r.json() if content_type.startswith("application/json") else r.text
            return {"tool": tool_name, "http_status": r.status_code, "data": data}

        except requests.RequestException as e:
            return {"tool": tool_name, "error": str(e), "url": url}

class CompositeExecutor:
    def __init__(self, mcp_client: Optional["MCPClient"]=None):
        self.local = LocalExecutor()
        self.http = HttpExecutor()
        self.mcp = MCPExecutor(mcp_client) if mcp_client else None

    def execute(self, tool_name: str, params: Dict[str, Any], spec: ExecSpec) -> Dict[str, Any]:
        t = (spec.type or "local").lower()
        if t == "local":
            return self.local.execute(tool_name, params, spec)
        if t == "http":
            return self.http.execute(tool_name, params, spec)
        if t == "mcp":
            if not self.mcp:
                return {"tool": tool_name, "error": "MCP client not configured"}
            return self.mcp.execute(tool_name, params, spec)
        return {"tool": tool_name, "error": f"Unknown exec type: {spec.type}"}