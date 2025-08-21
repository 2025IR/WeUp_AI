from typing import List, Dict
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from capstone_ai.config import MODEL_ID, GEN_MAX_TOKENS
import json, logging
log = logging.getLogger("dna.llm")

class LLMClient:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map="auto")

    def complete(self, messages: List[Dict[str, str]], max_new_tokens: int = GEN_MAX_TOKENS, temperature: float = 0.7, do_sample: bool = True) -> str:
        try:
            log.info("[PROMPT] %s", json.dumps(messages, ensure_ascii=False)[:4000])
        except Exception:
            pass
        input_ids = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(self.model.device)
        with torch.no_grad():
            gen_kwargs = {"input_ids": input_ids, "max_new_tokens": max_new_tokens}
            if do_sample:
                t = float(temperature)
                if t <= 0:
                    t = 1e-5
                gen_kwargs.update({"do_sample": True, "temperature": t})
            else:
                gen_kwargs.update({"do_sample": False})
            out = self.model.generate(**gen_kwargs)
        gen_ids = out[0][input_ids.shape[-1]:]
        return self.tokenizer.decode(gen_ids, skip_special_tokens=True).strip()