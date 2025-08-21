from typing import Any, Dict
import os

from capstone_ai.api.models import ChatRequest, ChatResponse
from capstone_ai.core.llm import LLMClient
from capstone_ai.core.memory import InMemoryHistory
from capstone_ai.core.router import AutoRouter
from capstone_ai.core.prompts import build_schema_prompt
from capstone_ai.mcp.catalog import ToolCatalog
from capstone_ai.mcp.executor import CompositeExecutor, ExecSpec
from capstone_ai.mcp.clarify import ClarifyManager
from capstone_ai.utils.json_utils import parse_json_object
from capstone_ai.utils.params import apply_defaults_and_coerce, validate_required
from capstone_ai.mcp.tools import TOOLS
from capstone_ai.mcp.adapter import MCPClient
from capstone_ai.core.answer import AnswerSynthesizer
from capstone_ai.config import MCP_ENDPOINT
from capstone_ai.mcp.dispatch import ToolDispatcher
from capstone_ai.mcp.dispatch_table import DISPATCH_TABLE
from capstone_ai.service.meeting_pipeline import run_meeting_pipeline


class ChatService:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = InMemoryHistory()
        self.catalog = ToolCatalog(TOOLS)
        self.router = AutoRouter(self.llm, self.catalog)
        self.executor = CompositeExecutor(mcp_client=MCPClient(endpoint=MCP_ENDPOINT))
        self.clarify = ClarifyManager()
        self.synth = AnswerSynthesizer(self.llm)
        self.dispatcher = ToolDispatcher(DISPATCH_TABLE)


    def _run_chat(self, cid: str, user_input: str) -> ChatResponse:
        history = self.memory.get_chat(cid)
        self.memory.append_chat(cid, "user", user_input)
        answer = self.llm.complete(history, max_new_tokens=512, temperature=0.7)
        self.memory.append_chat(cid, "assistant", answer)
        return ChatResponse(project_id=cid, route="chat", output=answer)


    def _run_mcp(self, cid: str, tool_name: str, schema: Dict[str, Any], user_input: str) -> ChatResponse:
        schema_prompt = build_schema_prompt(schema, context={"projectId": cid})
        raw = self.llm.complete(
            [{"role": "system", "content": schema_prompt}, {"role": "user", "content": user_input}],
            max_new_tokens=256, temperature=0.2
        )
        params = parse_json_object(raw)
        params = apply_defaults_and_coerce(schema, params)

        ok, missing = validate_required(schema, params)
        if not ok:
            self.clarify.set_pending(cid, tool_name, schema, params)
            question = self.clarify.make_question_kor(tool_name, schema, missing)
            self.memory.append_tool(
                cid, "assistant", question,
                meta={"type": "clarify", "tool": tool_name, "missing": missing}
            )
            return ChatResponse(project_id=cid, route="clarify", output=question, missing=missing)

        spec_dict = self.dispatcher.pick(
            tool_name, params, context={"projectId": cid, "env": os.getenv("APP_ENV", "prod")}
        )
        allowed = {"type", "name", "url", "method", "mapping"}
        spec = ExecSpec(**{k: v for k, v in spec_dict.items() if k in allowed})
        result = self.executor.execute(tool_name, params, spec)

        route_label = "http" if (getattr(spec, "type", "") or "").lower() == "http" else "mcp"
        try:
            nlg = self.synth.compose(self.memory.get_chat(cid), tool_name, params, result)
            result_out = {**result, "_answer": nlg}
            self.memory.append_chat(cid, "assistant", nlg)
        except Exception:
            result_out = result
            self.memory.append_chat(cid, "assistant", f"[{tool_name}] {result}")
        self.memory.append_chat(cid, "user", user_input)
        return ChatResponse(project_id=cid, route=route_label, output=result_out)

    def _resume_from_clarify(self, cid: str, user_input: str) -> ChatResponse:
        state = self.clarify.get(cid)
        if not state:
            return ChatResponse(project_id=cid, route="chat", output="이전 보류 요청을 찾지 못했습니다. 다시 요청해 주시겠습니까?")

        tool_name = state["tool_name"]
        schema = state["schema"]
        collected = state.get("collected", {}) or {}

        hint = (
            "You previously asked for missing parameters. "
            f"Here are collected params so far: {collected}. "
            "Merge the user's new info and return the full parameters object."
        )
        schema_prompt = build_schema_prompt(schema, prefix_hint=hint, context={"projectId": cid})
        raw = self.llm.complete(
            [{"role": "system", "content": schema_prompt}, {"role": "user", "content": user_input}],
            max_new_tokens=256, temperature=0.2
        )
        new_params = parse_json_object(raw)
        merged = apply_defaults_and_coerce(schema, {**collected, **new_params})

        def _normalize_change_role_params(p: dict) -> dict:
            q = dict(p)
            if "userName" not in q and "memberName" in q:
                q["userName"] = q.pop("memberName")
            if "roleName" not in q:
                if "roleIds" in q:
                    q["roleName"] = str(q.pop("roleIds"))
                elif "role" in q:
                    q["roleName"] = q.pop("role")
            if "project_id" in q:
                try:
                    q["project_id"] = int(q["project_id"])
                except Exception:
                    pass
            return q

        if tool_name == "change_role":
            merged = _normalize_change_role_params(merged)

        ok, missing = validate_required(schema, merged)
        if tool_name == "change_role":
            must = [k for k in ("projectId", "userName", "roleName") if not merged.get(k)]
            if must:
                missing = list(sorted(set((missing or []) + must)))
                ok = False

        if not ok:
            self.clarify.update_collected(cid, merged)
            question = self.clarify.make_question_kor(tool_name, schema, missing)
            self.memory.append_tool(
                cid, "assistant", question,
                meta={"type": "clarify", "tool": tool_name, "missing": missing}
            )
            return ChatResponse(project_id=cid, route="clarify", output=question, missing=missing)

        self.clarify.clear(cid)
        spec_dict = self.dispatcher.pick(
            tool_name, merged, context={"projectId": merged.get("projectId", cid), "env": os.getenv("APP_ENV", "prod")}
        )
        allowed = {"type", "name", "url", "method", "mapping"}
        spec = ExecSpec(**{k: v for k, v in spec_dict.items() if k in allowed})
        result = self.executor.execute(tool_name, merged, spec)
        route_label = "http" if (getattr(spec, "type", "") or "").lower() == "http" else "mcp"

        self.memory.append_tool(cid, "user", user_input, meta={"type": "clarify", "tool": tool_name})
        try:
            nlg = self.synth.compose(self.memory.get_chat(cid), tool_name, merged, result)
            out = {**result, "_answer": nlg}
            self.memory.append_chat(cid, "assistant", nlg)
        except Exception:
            out = result
            self.memory.append_chat(cid, "assistant", f"[{tool_name}] {result}")
        return ChatResponse(project_id=cid, route=route_label, output=out)

    def _normalize_meeting_params(self, p: dict, cid: str) -> dict:
        q = dict(p)
        if "projectId" not in q and cid:
            try:
                q["projectId"] = int(cid)
            except:
                pass
        for k in ("projectId", "chatRoomId"):
            if k in q:
                try:
                    q[k] = int(q[k])
                except:
                    pass
        return q

    def _run_meeting(self, cid: str, schema: dict, user_input: str) -> ChatResponse:
        schema_prompt = build_schema_prompt(schema, context={"projectId": int(cid)})
        raw = self.llm.complete(
            [{"role": "system", "content": schema_prompt}, {"role": "user", "content": user_input}],
            max_new_tokens=256, temperature=0.2
        )
        params = parse_json_object(raw)
        params = apply_defaults_and_coerce(schema, params)
        params = self._normalize_meeting_params(params, cid)

        ok, missing = validate_required(schema, params)
        if not ok:
            self.clarify.set_pending(cid, "meeting_create", schema, params)
            ask = self.clarify.make_question_kor("meeting_create", schema, missing)
            self.memory.append_tool(
                cid, "assistant", ask,
                meta={"type": "clarify", "tool": "meeting_create", "missing": missing}
            )
            return ChatResponse(project_id=cid, route="clarify", output=ask, missing=missing)

        result = run_meeting_pipeline(self.executor, self.llm, params, user_input)

        save_info = result.get("save") or {}
        http_status = save_info.get("http_status", 200) if isinstance(save_info, dict) else 500
        if http_status < 400:
            title = (result.get("summary") or {}).get("title", "회의록")
            answer = (
                "회의록을 생성했습니다.\n"
                f"- 범위: {params['startTime'].replace('T',' ')} ~ {params['endTime'].replace('T',' ')}\n"
                f"- 제목: {title}\n"
            )
        else:
            answer = "[ERROR] 회의록 생성 중 오류가 발생했습니다. 서버 응답을 확인해 주세요."

        self.memory.append_chat(cid, "assistant", answer)
        return ChatResponse(project_id=cid, route="http", output={**result, "_answer": answer})

    def handle(self, req: ChatRequest) -> ChatResponse:
        cid = req.project_id
        user_input = req.user_input
        mode = (req.mode or "auto").lower()
        chat_room_id = getattr(req, "chat_room_id", None)

        ctx: Dict[str, Any] = {"projectId": int(cid)}
        if chat_room_id is not None:
            try:
                ctx["chatRoomId"] = int(chat_room_id)
            except:
                pass
        self.memory.ensure_context(cid, ctx)

        if self.clarify.has(cid):
            return self._resume_from_clarify(cid, user_input)

        if mode == "chat":
            return self._run_chat(cid, user_input)

        if mode in ("auto", "mcp"):
            route_token = self.router.decide(user_input, context={"projectId": cid})
            schema = self.catalog.find(route_token)

            if route_token == "CHAT" or schema is None:
                return self._run_chat(cid, user_input)

            if route_token == "meeting_create":
                return self._run_meeting(cid, schema, user_input)

            return self._run_mcp(cid, route_token, schema, user_input)

        return self._run_chat(cid, user_input)