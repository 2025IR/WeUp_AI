from datetime import date
from flask import request, jsonify, Flask
from prompt_builder import PromptBuilder
from transformers import BitsAndBytesConfig
import torch
from model_manager import ModelManager
from project_assistant import ProjectAssistant

app = Flask(__name__)

SYSTEM_TEXT = r"""
당신은 친절하고 신뢰할 수 있는 프로젝트 비서입니다.
사용자의 지시를 정확히 이해하고, 그 의도에 따라 적절한 행동을 능동적으로 수행해야 합니다.
사용자의 목적은 항상 “더 나은 프로젝트 진행”이므로, 그 목적에 부합하도록 지원하는 것이 당신의 가장 중요한 역할입니다.

다음 사항을 반드시 지켜주세요:
1. 말투는 항상 공손하고 따뜻하게, 사용자와 자연스럽고 부드러운 대화를 유지합니다.
2. 사용자의 질문이 프로젝트 진행, 개발, 일정, 협업 등과 관련된 경우, 효율적인 실행을 돕는 방식으로 안내합니다.
3. 사용자의 질문 또는 요청이 명확하지 않더라도 의도를 추론하여 다음 중 적절한 행동을 취합니다:
   - 직접 응답
   - 함수 또는 API 호출
   - 일상적인 대화 대응
4. 근거 없는 정보를 생성하지 않습니다. 정확한 정보에 기반해 답변하며, 확실하지 않은 경우 “정확한 정보를 찾을 수 없습니다”라고 정중히 안내합니다.
5. 질문이 외부 지식에 기반해야 하는 경우, 스스로 정보를 생성하는 것이 아니라, 검색이나 문서 기반 질의 응답 시스템을 통해 확인된 정보만 사용합니다.
6. 질문이 여러 개 있더라도 한 번에 하나만 응답합니다.
"""
today = f"""오늘의 날짜는 {date.today()}입니다.
            오늘 날짜를 기준으로 판단하세요."""
TOOLS_TEXT = r"""
다음은 사용 가능한 도구입니다:
1. regist_todo
- 설명: 회의 일정을 등록합니다.
- 입력 예시: {"project_id": 12, "title": "팀 미팅", "date": "2023-05-24"}

2. change_role
- 설명: 유저의 역할을 변경합니다.
- 입력 예시: {"project_id": 16, "name": "김철수", "role_name": "피티티"}
※ 반드시 위 도구 중 하나만 선택해서 사용해야 하며, 도구 목록에 없는 함수를 호출해서는 안 됩니다.
"""
TOOLS_TEXT = today + TOOLS_TEXT

AGENT_TEXT = r"""
예시의 내용이 아닌 구조를 참고합니다.
※ 출력 예시:
Thought: 회의 일정을 등록해야 합니다.
Action: regist_todo
Action Input: {"project_id": 12, "title": "팀 미팅", "date": "2023-05-24"}
Observation: 회의가 등록되었습니다.
Final Answer: 2023년 5월 24일 10시에 팀 미팅이 성공적으로 등록되었습니다.
자세한 내용은 다음 프롬프트를 기다립니다.
"""

# user_input = input("요청 사항을 입력해주세요\n")
# print("input type:",type(user_input))

prompt_builder = PromptBuilder(SYSTEM_TEXT, AGENT_TEXT, TOOLS_TEXT)
adapter_paths = {
    "agent": "capston_model/agent",
    "multi_turn": "capston_model/multi_turn"
}

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

model_manager = ModelManager(
    "MLP-KTLim/llama-3-Korean-Bllossom-8B",
    adapter_paths,
    quantization_config=bnb_config
)

@app.route("/chat/ai", methods=["POST"])
def req_model():
    user_input = request.json.get("user_input")
    assistant = ProjectAssistant(model_manager, prompt_builder)
    response = assistant.handle_input(user_input)
    return jsonify({"response":response})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)