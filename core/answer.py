# capstone_ai/core/answer.py
from typing import Dict, Any, List, Optional
from capstone_ai.core.llm import LLMClient
import re

class AnswerSynthesizer:
    def __init__(self, llm):
        self.llm = llm

    def _sanitize(self, text: str) -> str:
        text = re.sub(r'("?(?:projectId|chatRoomId|userId|token)"?\s*:\s*)\d+',
                      r'\1"***"', text)
        for pat in [
            r"프로젝트\s*ID\s*[:：]?\s*\d+",
            r"프로젝트\s*[#:]?\s*\d+(?=\D)",
            r"projectId\s*[:=]\s*\d+",
            r"chatRoomId\s*[:=]\s*\d+",
            r"userId\s*[:=]\s*\d+",
            r"(?i)authorization\s*[:=]\s*\S+",
            r"(?i)bearer\s+[A-Za-z0-9\-\._]+",
        ]:
            text = re.sub(pat, lambda m: re.sub(r"\d+|[A-Za-z0-9\-\._]+", "***", m.group(0)), text)
        return text

    def _fmt_ko_date(self, s: Optional[str]) -> Optional[str]:
        if not s or not isinstance(s, str):
            return None
        try:
            date_part = s.split("T", 1)[0]
            y, m, d = date_part.split("-")
            y = int(y); m = int(m); d = int(d)
            return f"{y}년 {m}월 {d}일"
        except Exception:
            return None

    def _template(self, tool: str, params: Dict[str, Any], result: Dict[str, Any]) -> Optional[str]:
        status = result.get("http_status")
        ok = (status is None) or (200 <= int(status) < 400)

        if tool == "todo_create":
            name = params.get("todoName") or "새 작업"
            day  = self._fmt_ko_date(params.get("startDate"))
            if ok:
                if day:
                    return f"‘{name}’라는 이름의 새로운 작업이 {day}에 작업 생성이 성공적으로 완료되었습니다."
                return f"‘{name}’라는 이름의 새로운 작업 생성이 성공적으로 완료되었습니다."
            else:
                return f"‘{name}’ 작업 생성에 실패했습니다. 서버 응답을 확인해 다시 시도해 주시기 바랍니다."

        if tool == "change_role":
            user = params.get("userName") or params.get("memberName") or "해당 팀원"
            role = params.get("roleName") or params.get("roleIds") or "해당 역할"
            if ok:
                return f"‘{user}’님의 역할을 ‘{role}’로 변경이 성공적으로 완료되었습니다."
            else:
                return f"‘{user}’님의 역할을 ‘{role}’로 변경하는 과정에서 오류가 발생했습니다. 확인 후 다시 시도해 주시기 바랍니다."

        if tool == "meeting_create":
            title = (result.get("summary") or {}).get("title") or params.get("title") or "회의록"
            if ok:
                return f"‘{title}’ 회의록이 저장되었습니다."
            else:
                return "회의록 저장 과정에서 오류가 발생했습니다. 시간 범위와 채팅방 정보를 확인해 주시기 바랍니다."

        return None  

    def compose(self, history, tool_name: str, params: Dict[str, Any], result: Dict[str, Any]) -> str:
        msg = self._template(tool_name, params, result)
        if msg:
            return self._sanitize(msg)

        safe_params = {k: v for k, v in (params or {}).items() if k not in {"projectId","chatRoomId","userId","token"}}
        outline = {
            "tool": tool_name,
            "status": result.get("http_status", "unknown"),
        }
        messages = [
            {"role":"system","content":"한 문장, 한국어 존댓말, 내부 식별자 언급 금지."},
            {"role":"system","content":f"입력:{safe_params} 결과:{outline}"},
            {"role":"user","content":"사용자에게 한 문장으로 결과만 정중히 알려 주세요."}
        ]
        out = self.llm.complete(messages, max_new_tokens=60, temperature=0.4).strip()
        if not out or len(out) < 3:
            out = "요청하신 작업을 처리했습니다."
        return self._sanitize(out)