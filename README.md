# Capstone AI Assistant (FastAPI)

백엔드 요청을 **자동 라우팅**하여 **일반 대화**, **도구 호출(HTTP/MCP)**, **회의록 작성 파이프라인**을 처리하는 챗봇 서버입니다.  
설계 중심은 **요청 → 라우터 → 실행기(Executor)** 흐름이며, **요청·도구·결과**의 관계가 명확합니다.

---

## ✨ 주요 기능

- **자동 라우팅(AutoRouter)**: 입력을 `CHAT` 또는 특정 `tool_name`(예: `change_role`, `todo_create`, `meeting_create`)로 판정
- **도구 호출(HTTP/MCP)**: 스키마 기반 파라미터 추출 → 검증 → **부족 시 Clarify** → 안전 실행
- **회의록 파이프라인**: (1) 기간 채팅 수집 → (2) LLM 요약(JSON 스키마/마스킹) → (3) 저장
- **메모리 분리**: 일반 대화 히스토리 ↔ 도구(Clarify용) 히스토리 분리
- **프라이버시 보호**: `projectId`, `chatRoomId` 등 **내부 식별자 비노출**

---
## 🧭 아키텍처 흐름

1. **POST `/ai/chat` 수신** → `ChatService.handle()`
2. **AutoRouter**: `CHAT` vs `tool_name` 결정
3. **도구 흐름**  
   - `build_schema_prompt()` → LLM이 **JSON 파라미터** 산출  
   - `validate_required()` → 부족 시 **Clarify** 질문  
   - 충분하면 **Dispatcher → Executor(HTTP/MCP)** 실행
4. **회의록 흐름** (`meeting_create`)  
   - `meeting_chat`(기간 채팅 수집) → **요약(JSON, 내부ID 마스킹)** → `meeting_save`(저장)
5. **AnswerSynthesizer**: 존댓말·관계·흐름 중심의 한국어 응답 생성(내부ID 제거)

---

## 🗂 디렉토리 구조

```
capstone_ai/
├─ app.py                     # FastAPI 진입점
├─ api/
│  └─ routes.py               # /ai/chat 라우트
├─ core/
│  ├─ llm.py                  # 모델 클라이언트(Transformers)
│  ├─ router.py               # AutoRouter
│  ├─ prompts.py              # 프롬프트 빌더(스키마/회의록 등)
│  ├─ answer.py               # AnswerSynthesizer(프라이버시 포함)
│  ├─ memory.py               # InMemoryHistory(대화/툴 메모리 분리)
│  └─ system_prompt.py        # 시스템 프롬프트
├─ mcp/
│  ├─ tools.py                # 도구 스키마 카탈로그
│  ├─ dispatch_table.py       # HTTP/MCP 실행 스펙(화이트리스트)
│  ├─ dispatch.py             # ToolDispatcher
│  ├─ executor.py             # CompositeExecutor(local/http/mcp)
│  ├─ adapter.py              # MCP 어댑터(옵션)
│  └─ clarify.py              # ClarifyManager
├─ service/
│  ├─ chat_service.py         # 오케스트레이션
│  └─ meeting_pipeline.py     # 회의록 파이프라인
├─ utils/
│  ├─ json_utils.py           # JSON 파싱
│  ├─ params.py               # 스키마 적용/타입 보정
│  ├─ validation.py           # 필수값 검증
│  ├─ datetime.py             # “8월 20일 …” → LocalDateTime
│  └─ redact.py               # 내부 식별자 마스킹
└─ config.py                  # 환경설정
```

---

## 📦 요구 사항

- Python 3.10+
- (선택) CUDA 환경
- 주요 라이브러리: `torch`, `transformers`, `fastapi`, `uvicorn`, `requests`

---

## ⚙️ 설정

`capstone_ai/config.py` 또는 환경변수로 설정:

- `MODEL_ID` (기본: `dnotitia/Llama-DNA-1.0-8B-Instruct`)
- `MCP_ENDPOINT` (MCP 사용 시)
- `APP_ENV` (`dev`/`prod`)
- `BACKEND_AUTH_TOKEN` (백엔드 HTTP 호출 시 필요하면 사용)

---


## 🔌 API

### POST `/ai/chat`

**요청(JSON)**

```json
{
  "project_id": "1",
  "chat_room_id": "1",
  "user_input": "ㅇㅇㅇ의 역할을 ㅇㅇ으로 변경.",
  "mode": "auto"
}
```

**응답(JSON)**

```json
{
  "project_id": "1",
  "route": "chat | http | mcp | clarify",
  "output": { },
  "missing": ["필드"]
}
```


## 🛠 내장 도구

### 1) `change_role` — 역할 변경/추가
- **필드**: `projectId: integer`, `userName: string`, `roleName: string`

```python
"change_role": {
  "exec": {
    "type": "http", "method": "POST",
    "url": "https://.../ai/role/assign",
    "mapping": {
      "projectId": "body.projectId",
      "userName":  "body.userName",
      "roleName":  "body.roleName"
    }
  }
}
```

### 2) `todo_create` — 할 일/업무 생성
- **필드**: `projectId: integer`, `todoName: string`, `startDate: YYYY-MM-DD`

```python
"todo_create": {
  "exec": {
    "type": "http", "method": "POST",
    "url": "https://.../ai/todo/create",
    "mapping": {
      "projectId": "body.projectId",
      "todoName":  "body.todoName",
      "startDate": "body.startDate"
    }
  }
}
```

### 3) `meeting_create` — 회의록 파이프라인
- **필드(최소)**: `projectId`, `chatRoomId`, `startTime`, `endTime`  
  (날짜만 있으면 자동 보정: `00:00 ~ 23:59`)
- **흐름**: `meeting_chat`(수집) → LLM 요약(JSON/마스킹) → `meeting_save`(저장)

```python
"meeting_chat": {
  "exec": {
    "type": "http", "method": "POST",
    "url": "https://.../ai/minutes/message",
    "mapping": {
      "chatRoomId": "body.chatRoomId",
      "startTime":  "body.startTime",
      "endTime":    "body.endTime"
    }
  }
},
"meeting_save": {
  "exec": {
    "type": "http", "method": "POST",
    "url": "https://.../ai/minutes/create",
    "mapping": {
      "projectId": "body.projectId",
      "title":     "body.title",
      "contents":  "body.contents"
    }
  }
}
```

---

## ➕ 도구 추가 방법

1. `mcp/tools.py`에 **스키마** 등록 (`name`, `description`, `parameters.required/properties`, `exec`)
2. `mcp/dispatch_table.py`에 **실행 스펙** 등록 (HTTP면 `method/url/mapping`)
3. (필요 시) 복합 흐름은 `service/xxx_pipeline.py` 작성 후 `chat_service.py`에 분기 추가
4. `/ai/chat`를 Postman/cURL로 테스트

---

## 🔐 프라이버시 & 보안

- 프롬프트/합성에서 **내부 식별자 비노출** 규칙 적용
- 요약(JSON) 파싱 후 `utils/redact.py`로 **필드별 마스킹**
- `dispatch_table` **화이트리스트** 외 도구 실행 금지
- 필요 시 `BACKEND_AUTH_TOKEN`을 **Authorization** 헤더로 자동 주입

---

## 🧪 로깅/디버깅

- `[PROMPT]` LLM 프롬프트
- `[HTTP EXEC]`, `[HTTP EXEC SENT]` HTTP 실행/보낸 바디 미리보기
- FastAPI/Uvicorn 스택 트레이스로 예외 확인

---

## 🩺 트러블슈팅

- **404 Not Found(HTTP 도구)**: `dispatch_table.url`/서버 라우트 점검
- **403 Forbidden**: 프로젝트 상태/권한/토큰 확인
- **400 Bad Request**: Body 키·타입·날짜 포맷 점검(JSON 더블쿼트)
- **모델 경고**: `temperature > 0` 또는 `do_sample=False` 설정
- **/ai/chat 404**: uvicorn 실행·포트·경로 확인

---

## ⚡️ 빠른 시작

```bash
# 1) 설치
pip install -r requirements.txt

# 2) 환경 변수(예)
export MODEL_ID="dnotitia/Llama-DNA-1.0-8B-Instruct"
export BACKEND_AUTH_TOKEN="...optional..."

# 3) 서버 실행
uvicorn capstone_ai.app:app --host 0.0.0.0 --port 9001

# 4) 테스트
curl -X POST "http://<ip>:9001/ai/chat"   -H "Content-Type: application/json"   -d '{"project_id":"1","chat_room_id":"1","user_input":"8월 20일 회의록 작성","mode":"auto"}'
```

---

## 🙌 크레딧

- 모델: `dnotitia/Llama-DNA-1.0-8B-Instruct` (Transformers)  
- 프레임워크: FastAPI / Uvicorn
