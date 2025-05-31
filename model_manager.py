from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

class ModelManager:
    def __init__(self, base_model_name: str, adapter_paths: dict, device_map={"": 0}, quantization_config=None):
        self.base = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            device_map=device_map,
            quantization_config=quantization_config
        )
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.adapter_paths = adapter_paths

    def get_adapter(self, name: str, trainable: bool = False):
        return PeftModel.from_pretrained(
            self.base,
            self.adapter_paths[name],
            adapter_name=name,
            is_trainable=trainable,
            local_files_only=True
        )