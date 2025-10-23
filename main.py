from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.clause_analyzer import router
from api.conversation import router as conversation_router
import uvicorn 

app = FastAPI(
    title="Harmful Clause Detection API",
    description="An API to detect harmful clauses in documents using a language model.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(conversation_router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)