from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.auth import router as auth_router

app = FastAPI(title="Course Content Q&A Tutor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"message": "Course Content Q&A Tutor API is running"}