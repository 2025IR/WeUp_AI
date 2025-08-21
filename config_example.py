from datetime import datetime
import os
from zoneinfo import ZoneInfo

_TZ = ZoneInfo(os.getenv("APP_TZ", "Asia/Seoul"))
MODEL_ID = "huggingface_model url"
CUTTING_KNOWLEDGE = "December 2023"
TODAY = datetime.now(_TZ) if _TZ else datetime.now()
GEN_MAX_TOKENS = 256
MCP_ENDPOINT = os.getenv("MCP_ENDPOINT", "server_url ex) http://000.000.000.000:1111")
MCP_AUTH_HEADER = os.getenv("MCP_AUTH_HEADER", "Authorization")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "tocken")

DEFAULT_HTTP_HEADERS = {MCP_AUTH_HEADER: MCP_AUTH_TOKEN} if MCP_AUTH_TOKEN else {}

ROLE_CHANGE_URL = "api_url"
TODO_CREATE_URL = "api_url"
MEETING_CHAT_URL = "api_url"
MEETING_SAVE_URL = "api_url"