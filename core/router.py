import re
from capstone_ai.core.prompts import build_router_prompt
from capstone_ai.mcp.catalog import ToolCatalog
from capstone_ai.core.llm import LLMClient
from capstone_ai.core.context import format_context

class AutoRouter:
    def __init__(self, llm: LLMClient, catalog: ToolCatalog):
        self.llm = llm
        self.catalog = catalog

    def decide(self, user_input: str, context: dict | None = None) -> str:
        sys_prompt = build_router_prompt(self.catalog.list())
        messages = [{"role":"system", "content":sys_prompt}]
        if context:
            messages.append({"role":"system","content": format_context(context)})
        messages.append({"role":"user","content": user_input})
        route_token = self.llm.complete(
            messages,
            max_new_tokens=8,
            do_sample=False,
        ).strip()
        route_token = re.sub(r"[^A-Za-z0-9_]", "", route_token)
        return route_token or "CHAT"