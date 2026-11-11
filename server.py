import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain.chat_models import init_chat_model
from pydantic import BaseModel

logging.getLogger("google_genai").setLevel(logging.ERROR)
load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
  raise RuntimeError("GEMINI_API_KEY not found in .env file!")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = init_chat_model(
    "gemini-3.5-flash-lite",
    model_provider="google_genai",
    temperature=0,
)


class PromptRequest(BaseModel):
  prompt: str


# 1. Serve index.html when visiting http://127.0.0.1:8000
@app.get("/")
def serve_home():
  return FileResponse("index.html")


# 2. Handle the chat POST request
@app.post("/ask")
def ask_gemini(request: PromptRequest):
  print("Received prompt:", request.prompt)
  try:
    response = model.invoke(request.prompt)
    reply_text = (
        response.content
        if isinstance(response.content, str)
        else "".join(
            block.get("text", "")
            for block in response.content
            if isinstance(block, dict)
        )
    )
    return {"reply": reply_text}
  except Exception as e:
    print("ERROR IN /ask:", repr(e))
    raise HTTPException(status_code=500, detail=str(e))


# 3. Serve style.css and script.js from the same folder
app.mount("/", StaticFiles(directory="."), name="static")