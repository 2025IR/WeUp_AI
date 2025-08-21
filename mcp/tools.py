TOOLS = [
    {
        "name": "change_role",
        "description": "팀원의 역할을 변경하거나 추가",
        "parameters": {
            "type": "dict",
            "required": ["projectId", "userName", "roleName"],
            "properties": {
                "projectId": {"type": "integer", "description": "프로젝트 ID"},
                "userName":   {"type": "string",  "description": "팀원 이름"},
                "roleName":   {"type": "string",  "description": "변경할 역할 이름"}
            }
        },
        "exec": { "type": "mcp", "name": "change_role" }
    },
    {
        "name": "todo_create",
        "description": "회의/미팅/약속 등 '일정'을 생성합니다. 예: '오늘 회의 잡아줘', '내일 3시 미팅 예약'. 회의 내용 정리(회의록)는 meeting_create를 사용하세요.",
        "parameters": {
            "type": "dict",
            "required": ["projectId", "todoName", "startDate"],
            "properties": {
                "projectId": {"type": "integer", "description": "프로젝트 ID. 반드시 채우세요. 현재 대화/세션 컨텍스트의 projectId"},
                "todoName":   {"type": "string",  "description": "일정 제목(예: '프로젝트 킥오프 미팅')"},
                "startDate":   {"type": "date",  "description": "시작 날짜(YYYY-MM-DD)"}
            }
        },
        "exec": { "type": "mcp", "name": "todo_create" }
    },
    {
        "name": "meeting_create",
        "description": "대화/회의 로그를 바탕으로 '회의록'을 작성·요약합니다. 예: '어제 회의 내용 회의록으로 정리해줘.','10시부터 11시까지 요약'.일정 생성(회의/미팅 예약)은 todo_create를 사용하세요.",
        "parameters": {
            "type": "dict",
            "required": ["projectId", "chatRoomId", "startTime", "endTime"],
            "properties": {
                "projectId": {"type": "integer", "description": "프로젝트 ID. 반드시 채우세요. 현재 대화/세션 컨텍스트의 projectId"},
                "chatRoomId": {"type": "integer", "description": "채팅방 ID. 반드시 채우세요. 현재 컨텍스트의 chatRoomId"},
                "startTime":  {"type": "string",  "description": "시작 시각(YYYY-MM-DDTHH:MM:SS)"},
                "endTime":    {"type": "string",  "description": "종료 시각(YYYY-MM-DDTHH:MM:SS)"},
                "title":      {"type": "string",  "description": "회의록 제목(선택, 미지정 시 자동 생성)"}
            }
        }
    },
]