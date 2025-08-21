# KST 기준 날짜/시간 유틸

import re
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

DATE_PATTERNS = [
    re.compile(r'(?:(\d{4})\s*년\s*)?(\d{1,2})\s*월\s*(\d{1,2})\s*일'),
    re.compile(r'(?:(\d{4})[./-])?(\d{1,2})[./-](\d{1,2})'),
]

def _fmt_local(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def parse_ko_range_to_localdt(text: str):
    # “8/29 13시~17시” 같은 범위를 YYYY-MM-DDTHH:MM:SS 쌍으로 파싱 (간단 버전)
    m = re.search(r'(\d{1,2})[./-](\d{1,2}).*?(\d{1,2})\s*시\s*~\s*(\d{1,2})\s*시', text)
    if not m: return (None, None)
    now = datetime.now(KST)
    mm, dd, h1, h2 = map(int, m.groups())
    y = now.year
    s = datetime(y, mm, dd, h1, 0, 0, tzinfo=KST)
    e = datetime(y, mm, dd, h2, 0, 0, tzinfo=KST)
    return (_fmt_local(s), _fmt_local(e))

def parse_date_only_to_full_day(text: str, base: datetime | None = None):
    if base is None: base = datetime.now(KST)
    # 시간 표현이 있으면 여기서 처리하지 않음
    if re.search(r'(시|부터|까지|~|:)', text): return (None, None)
    for pat in DATE_PATTERNS:
        m = pat.search(text)
        if m:
            year = int(m.group(1)) if m.group(1) else base.year
            month = int(m.group(2)); day = int(m.group(3))
            s = datetime(year, month, day, 0, 0, 0, tzinfo=KST)
            e = datetime(year, month, day, 23, 59, 59, tzinfo=KST)
            return (_fmt_local(s), _fmt_local(e))
    return (None, None)

def infer_full_day_if_date_only_ko(params: dict, text: str, base: datetime | None = None) -> dict:
    if params.get("startTime") and params.get("endTime"): return params
    s, e = parse_date_only_to_full_day(text, base)
    if s and e:
        params.setdefault("startTime", s)
        params.setdefault("endTime", e)
    return params
