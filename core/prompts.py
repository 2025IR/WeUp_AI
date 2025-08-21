import json
from typing import Dict, List
from capstone_ai.config import MODEL_ID, GEN_MAX_TOKENS
from capstone_ai.config import CUTTING_KNOWLEDGE, TODAY

def build_router_prompt(tools: List[Dict]) -> str:
    lines = [
        "Environment: ipython",
        f"Cutting Knowledge Date: {CUTTING_KNOWLEDGE}",
        f"Today Date: {TODAY}",
        "",
        "You can access tools via the MCP server.",
        "Decide routing for the user request.",
        "",
        "Output EXACTLY ONE token:",
        "• If the request requires a tool, output the BEST tool NAME from the catalog below.",
        "• Otherwise, output: CHAT",
        "",
        "ABSOLUTE RULES:",
        "• No explanations. No punctuation. No quotes.",
        "• Must match regex: ^(CHAT|[A-Za-z0-9_]+)$",
        "",
        "TOOLS CATALOG:"
    ]
    for t in tools:
        lines.append(f"- {t['name']}: {t['description']}")
    return "\n".join(lines)

def build_schema_prompt(schema: Dict, prefix_hint: str | None = None, context: Dict | None = None) -> str:
    ctx_block = ""
    if context:
        from capstone_ai.core.context import format_context
        ctx_block = format_context(context) + "\n\n"
    base = (
        'You are an AI assistant specialised in tool usage.\n'
        'Return only one JSON object that starts with "{" and ends with "}".\n'
        'No extra text or comments after the final "}".\n'
        'Use ASCII double quotes for all keys and values.\n'
        f'Today Date: {TODAY}'
        f"SCHEMA:\n{json.dumps(schema['parameters'], ensure_ascii=False)}"
    )
    prefix = (prefix_hint + "\n\n") if prefix_hint else ""
    return ctx_block + prefix + base

def build_meeting_prompt(raw_transcript: str, meta: dict) -> str:
    chat_room_id = meta.get("chatRoomId", 1)
    project_id   = meta.get("projectId")
    time_range = meta.get("time_range","")

    header = []
    header.append(f"[회의 시간] {time_range}")
    if project_id is not None:
        header.append(f"[프로젝트 ID] {project_id}")
    header.append(f"[채팅방 ID] {chat_room_id}")
    header_str = "\n".join(header)

    return (
        "당신은 프로젝트를 돕는 전문 비서입니다. 존댓말로 간결하게 회의록을 작성해 주세요.\n"
        f"{header_str}\n"
        f"[회의 시간] {time_range}\n"
        "[작성 원칙]\n"
        "- 핵심 결론과 근거를 구조화합니다.\n"
        "- 항목 간 관계(논의 → 결정 → 액션아이템)를 명확히 합니다.\n"
        "- 액션아이템은 담당자/기한을 포함해 목록화합니다.\n"
        "- 불필요한 수사는 제외하고, 사실만 정리합니다.\n"
        "- 내부 식별자(projectId, chatRoomId, userId 등)나 숫자형 프로젝트 표기는 절대 언급하지 않습니다. ex) 프로젝트 1 회의록, 프로젝트 1 팀원들\n\n"
        "[원문 대화]\n"
        f"{raw_transcript}\n\n"
        "[출력 형식]\n"
        "제목: <한 줄> 내부 식별자(projectId, chatRoomId, userId 등)나 숫자형 프로젝트 표기는 절대 언급하지 않습니다.\n"
        "개요: <3~4문장> 내부 식별자(projectId, chatRoomId, userId 등)나 숫자형 프로젝트 표기는 절대 언급하지 않습니다.\n"
        "주요 논의:\n"
        " - 항목1\n - 항목2\n"
        "결정 사항:\n - 항목1\n - 항목2\n"
    )