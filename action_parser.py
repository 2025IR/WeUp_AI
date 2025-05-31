import re
import json
from typing import Tuple, Dict, Union

class ActionParser:
    @staticmethod
    def parse(text: str) -> Tuple[Union[str, None], Union[dict, str, None], Union[str, None]]:
        action_m = re.search(r'Action:\s*(\w+)', text)
        action = action_m.group(1) if action_m else None
        input_m = re.search(r'Action Input:\s*(\{.*?\})(?=\s*(Observation:|Final Answer:))', text, re.DOTALL)
        if input_m:
            raw = input_m.group(1)
            try:
                action_input = json.loads(raw)
            except json.JSONDecodeError:
                action_input = raw
        else:
            action_input = None

        fa_m = re.search(r'Final Answer:\s*(.+)', text)
        final_answer = fa_m.group(1).strip() if fa_m else None
        return action, action_input, final_answer