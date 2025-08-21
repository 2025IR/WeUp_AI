from typing import Dict

def format_context(ctx: dict, private: bool = True) -> str:
    header = "[CONTEXT - PRIVATE]" if private else "[CONTEXT]"
    lines = [header, "※ 이 정보는 내부용입니다. 사용자 응답에 공개/언급 금지 (IDs: projectId, chatRoomId 등)."]
    for k, v in ctx.items():
        lines.append(f"{k}: {v}")
    return "\n".join(lines)