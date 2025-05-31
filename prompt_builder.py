class PromptBuilder:
    BOS = "<|begin_of_text|>"
    HDR = "<|start_header_id|>"
    ENDH = "<|end_header_id|>"
    EOT = "<|eot_id|>"

    def __init__(self, system_text: str, agent_text: str, context_schema: str, context=""):
        self.system_text = system_text
        self.agent_text = agent_text
        self.context_schema = context_schema
        self.context = context

    def build(self, user_msg: str, use_agent: bool, chat_history: str = "") -> str:
        system_block = self.system_text + (self.agent_text if use_agent else "")
        parts = [
            f"{self.BOS}{self.HDR}system{self.ENDH}\n{system_block}{self.EOT}",
        ]
        if use_agent:
            parts.append(f"{self.HDR}context{self.ENDH}\n{self.context_schema}{self.EOT}")
        else:
            parts.append(f"{self.HDR}context{self.ENDH}\n{self.context}{self.EOT}")
        parts.append(f"{self.HDR}chat_history{self.ENDH}\n{chat_history}{self.EOT}")
        parts.append(f"{self.HDR}user{self.ENDH}\n{user_msg}{self.EOT}")
        parts.append(f"{self.HDR}assistant{self.ENDH}\n")
        return "\n".join(parts)