import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import engine, Base, masked_database_url
import models  # noqa: F401 - ensures models are registered on Base before create_all
from routers import auth_routes, interview_routes, proctoring_routes, report_routes
from services import llm_service, stt_service, rag_service

load_dotenv(Path(__file__).resolve().parent / ".env")

app = FastAPI(title="Interview Mock AI API", version="1.0.0")


@app.exception_handler(llm_service.LLMError)
async def llm_error_handler(request: Request, exc: llm_service.LLMError):
    # Model problems (Ollama not running, no OpenAI credit, unreadable output...) come
    # back as a readable 503 the frontend shows, instead of an opaque 500.
    return JSONResponse(status_code=503, content={"detail": str(exc)})

origins = [os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Printed on every startup on purpose - if the DB connection fails right
    # after this line, whatever user/host is shown here is what to fix first.
    print(f"[startup] Model backend:   {llm_service.describe_backend()}")
    print(f"[startup] Speech-to-text:  {stt_service.describe_backend()}")
    print(f"[startup] Retrieval (RAG): {rag_service.describe()}")
    print(f"[startup] Connecting to database: {masked_database_url()}")
    Base.metadata.create_all(bind=engine)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "interview-mock-ai-backend"}


app.include_router(auth_routes.router)
app.include_router(interview_routes.router)
app.include_router(proctoring_routes.router)
app.include_router(report_routes.router)
