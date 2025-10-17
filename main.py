from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Harmful Clause Detection API. Use the /get_clauses endpoint to analyze documents."}

app.include_router(router)
app.include_router(conversation_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)