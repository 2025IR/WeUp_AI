from typing import Dict, List, Optional, Any

from capstone_ai.core.system_prompt import DEFAULT_SYSTEM_PROMPT


class InMemoryHistory:
    """
    히스토리 분리 정책
    - 일반 대화용(chat): 시스템 프롬프트/컨텍스트 포함. NLG 등 모델 입력의 기본 히스토리.
    - 툴(clarify)용(tool): 'clarify' 왕복만 누적. 실행 완료 후에는 필요 시 clear_tool()로 정리.
    """

    def __init__(self) -> None:
        self._chat: Dict[str, List[Dict[str, Any]]] = {}
        self._tool: Dict[str, List[Dict[str, Any]]] = {}

    def _ensure_chat_session(self, cid: str) -> None:
        """세션이 없으면 시스템 프롬프트로 초기화."""
        if cid not in self._chat:
            self._chat[cid] = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]

    # ===== 기존 인터페이스(하위 호환) =====
    def get(self, cid: str) -> List[Dict[str, Any]]:
        """하위 호환: 일반 대화 히스토리를 반환."""
        self._ensure_chat_session(cid)
        return self._chat[cid]

    def append(self, cid: str, role: str, content: str) -> None:
        """하위 호환: 일반 대화 히스토리에 추가."""
        self.append_chat(cid, role, content)

    # ===== 일반 대화(Chat) =====
    def get_chat(self, cid: str) -> List[Dict[str, Any]]:
        self._ensure_chat_session(cid)
        return self._chat[cid]

    def append_chat(self, cid: str, role: str, content: str) -> None:
        self._ensure_chat_session(cid)
        self._chat[cid].append({"role": role, "content": content})

    def ensure_system(self, cid: str, system_prompt: Optional[str], *, override: bool = True) -> None:
        """
        세션의 시스템 메시지를 설정/갱신 (일반 대화 히스토리 전용).
        - override=True: 맨 앞의 system 메시지 내용을 교체
        - override=False: 앞이 system이 아니면 삽입
        """
        if system_prompt is None:
            return
        self._ensure_chat_session(cid)
        msgs = self._chat[cid]
        if override or msgs[0]["role"] != "system":
            if msgs and msgs[0]["role"] == "system":
                msgs[0]["content"] = system_prompt
            else:
                msgs.insert(0, {"role": "system", "content": system_prompt})

    def ensure_context(self, cid: str, ctx: Dict[str, Any]) -> None:
        """
        [CONTEXT] 블록을 일반 대화 히스토리의 두 번째(system 다음) 위치에 유지.
        기존 컨텍스트가 있으면 갱신, 없으면 삽입.
        """
        from capstone_ai.core.context import format_context

        self._ensure_chat_session(cid)
        msgs = self._chat[cid]
        ctx_str = format_context(ctx)

        if len(msgs) >= 2 and msgs[1]["role"] == "system" and msgs[1]["content"].startswith("[CONTEXT]"):
            msgs[1]["content"] = ctx_str  # 기존 컨텍스트 갱신
        else:
            msgs.insert(1, {"role": "system", "content": ctx_str})

    def get_tool(self, cid: str) -> List[Dict[str, Any]]:
        """툴 clarify 히스토리 조회(모델 입력에는 기본적으로 사용하지 않음)."""
        return self._tool.get(cid, [])

    def append_tool(self, cid: str, role: str, content: str, meta: Optional[Dict[str, Any]] = None) -> None:
        """
        clarify 왕복만 기록.
        meta 예시: {"type": "clarify", "tool": "change_role", "missing": ["projectId"...]}
        """
        if cid not in self._tool:
            self._tool[cid] = []
        item: Dict[str, Any] = {"role": role, "content": content}
        if meta:
            item["meta"] = meta
        self._tool[cid].append(item)

    def clear_tool(self, cid: str) -> None:
        """툴 clarify 히스토리 삭제(실행 완료 후 정리)."""
        if cid in self._tool:
            del self._tool[cid]