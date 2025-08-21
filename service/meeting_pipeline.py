from typing import Dict, Any
from capstone_ai.mcp.dispatch_table import DISPATCH_TABLE
from capstone_ai.mcp.executor import ExecSpec, CompositeExecutor
from capstone_ai.core.prompts import build_meeting_prompt
from capstone_ai.utils.datetime import parse_ko_range_to_localdt, parse_date_only_to_full_day


def _auto_title(start: str, end: str) -> str:
    """예: 회의록(YYYY-MM-DD HH:MM~HH:MM)"""
    sd = start.replace("T", " ")
    ed = end.replace("T", " ")
    return f"회의록({sd[:16]}~{ed[11:16]})"


def run_meeting_pipeline(
    executor: CompositeExecutor,
    llm,
    params: Dict[str, Any],
    utterance: str
) -> Dict[str, Any]:
    """
    params: {projectId, chatRoomId, startTime, endTime, title?}
    1) 시간 미기재 시 한국어 문장에서 (연도 규칙 포함) LocalDateTime 추론
    2) meeting_chat 호출 → transcript 확보
    3) LLM 요약 → title/contents 생성
    4) meeting_save 호출
    """
    st, et = params.get("startTime"), params.get("endTime")
    if not st or not et:
        pst, pet = parse_ko_range_to_localdt(utterance)
        if pst and pet:
            params["startTime"], params["endTime"] = pst, pet

    if not st or not et:
        d1, d2 = parse_date_only_to_full_day(utterance)   
        if d1 and d2:
            params.setdefault("startTime", d1)
            params.setdefault("endTime", d2)

    for k in ("projectId", "chatRoomId", "startTime", "endTime"):
        if not params.get(k):
            return {"tool": "meeting_create", "error": f"missing {k}"}

    spec_fetch = ExecSpec(**DISPATCH_TABLE["meeting_chat"]["exec"])
    fetch_in = {
        "chatRoomId": params["chatRoomId"],
        "startTime": params["startTime"],
        "endTime": params["endTime"],
    }
    fetched = executor.execute("meeting_chat", fetch_in, spec_fetch)
    if fetched.get("http_status", 200) >= 400:
        return {
            "tool": "meeting_create",
            "step": "fetch",
            "error": fetched,
            "summary": None,
            "save": None,
        }

    data = fetched.get("data")
    if isinstance(data, dict):
        raw = data.get("data") or data.get("message") or ""
    else:
        raw = data or ""
    raw = raw or ""

    MAX_CHARS = 12000
    if len(raw) > MAX_CHARS:
        raw = raw[-MAX_CHARS]

    time_range = f"{params['startTime'].replace('T', ' ')} ~ {params['endTime'].replace('T', ' ')}"
    prompt = build_meeting_prompt(raw, {"projectId": params["projectId"], "time_range": time_range})
    summary = llm.complete([{"role": "system", "content": prompt}], max_new_tokens=800, temperature=0.2)
    title = params.get("title") or _auto_title(params["startTime"], params["endTime"])
    contents = summary.strip()

    spec_save = ExecSpec(**DISPATCH_TABLE["meeting_save"]["exec"])
    save_in = {"projectId": params["projectId"], "title": title, "contents": contents}
    saved = executor.execute("meeting_save", save_in, spec_save)

    return {
        "tool": "meeting_create",
        "fetch": fetched,
        "summary": {               
            "title": title,
            "text": contents,
            "length": len(contents),
        },
        "save": saved,
    }


def run_minutes_pipeline(executor: CompositeExecutor, llm, params: Dict[str, Any], utterance: str) -> Dict[str, Any]:
    """Deprecated: meeting 파이프라인으로 위임."""
    return run_meeting_pipeline(executor, llm, params, utterance)
