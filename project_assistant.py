from model_manager import ModelManager
from prompt_builder import PromptBuilder
import logging
from tool import execute_action, regist_todo, change_role, parse_assistant_response
from typing import Union
from action_parser import ActionParser

AGENT_KEYWORDS = ["회의", "등록", "일정", "잡아줘", "미팅", "변경", "예약"]

class ProjectAssistant:
    def __init__(self, model_manager: ModelManager, prompt_builder: PromptBuilder):
        self.mm = model_manager
        self.pb = prompt_builder

    def handle_input(self, text_input: str):
        use_agent = any(k in text_input for k in AGENT_KEYWORDS)
        adapter = "agent" if use_agent else "multi_turn"
        model = self.mm.get_adapter(adapter)
        prompt = self.pb.build(text_input, use_agent)
        response = self._generate(prompt, model)

        if use_agent:
            text_input +="\nproject_id는 55입니다."
            action, params, final_resp = ActionParser.parse(response)
            self._execute(action, params)
            logging.info("agent")
            logging.info(response)
            action, action_input, final_answer = parse_assistant_response(response)
            logging.info("action")
            logging.info(action)
            logging.info("action_input")
            logging.info(action_input)
            logging.info("final_answer")
            logging.info(final_answer)
            mapping = execute_action(action,action_input)
            print(type(mapping))
            return mapping

        else:
            logging.info("normal")
            logging.info(response)
            print(type(response))
            return response

    def _generate(self, prompt: str, model) -> str:
        inputs = self.mm.tokenizer(prompt, return_tensors="pt").to(model.device)
        out_ids = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=True,
            temperature=0.8,
            top_p=0.8,
            eos_token_id=self.mm.tokenizer.eos_token_id
        )
        return self.mm.tokenizer.decode(out_ids[0], skip_special_tokens=True)

    @staticmethod
    def _execute(action: str, params: Union[dict, str, None]):
        if action == "regist_todo" and isinstance(params, dict):
            print("regist_todo 들어옴")
            print(regist_todo(params))
        elif action == "change_role" and isinstance(params, dict):
            print("change_role")
            print(change_role(**params))