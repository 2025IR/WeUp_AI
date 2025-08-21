from fastapi import FastAPI
from capstone_ai.api.routes import router as chat_router
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="DNA Chatbot (Auto-route + Clarify + Multi-turn)")
app.include_router(chat_router, prefix="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)