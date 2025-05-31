from typing import Tuple, Optional, Dict, Any
import re
import json

def regist_todo(input_data):
    print(f"regist_todo 실행 -> input=project_id{input_data['project_id']}, title={input_data['title']}, date={input_data['date']}")
    return f"{input_data['date']}에 '{input_data['title']}' 일정이 등록되었습니다."

def change_role(input_data):
    print(f"change_role 실행 -> input=project_id{input_data['project_id']}, usr={input_data['usr']}, role={input_data['role']}")
    return f"{input_data['usr']}의 역할을 {input_data['role']}로 변경하였습니다."

action_map ={
    "regist_todo": regist_todo,
    "change_role": change_role
}

def execute_action(action:str, input_data: dict):
    print("input_data:",input_data)
    if action not in action_map:
        print("action:",action)
        raise ValueError(f"지원하지 않는 액션입니다: {action}")
    return action_map[action](input_data)

def parse_assistant_response(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[str]]:
    """
    전체 텍스트에서 가장 마지막 'user' 이후 등장한 'assistant' 응답 블록 내의
    Action, Action Input, Final Answer만 추출합니다.
    """
    user_split = re.split(r"user\s*\n", text)
    if len(user_split) < 2:
        return None, None, None
    last_user_block = user_split[-1]

    assistant_split = re.split(r"assistant\s*\n", last_user_block)
    if len(assistant_split) < 2:
        return None, None, None 
    assistant_block = assistant_split[-1]

    action_match = re.search(r"Action:\s*(\w+)", assistant_block)
    action = action_match.group(1) if action_match else None

    action_input_match = re.search(r"Action Input:\s*(\{.*?\})", assistant_block, re.DOTALL)
    try:
        action_input = json.loads(action_input_match.group(1)) if action_input_match else None
    except json.JSONDecodeError:
        action_input = None

    final_answer_match = re.search(r"Final Answer:\s*(.+)", assistant_block)
    final_answer = final_answer_match.group(1).strip() if final_answer_match else None

    return action, action_input, final_answer