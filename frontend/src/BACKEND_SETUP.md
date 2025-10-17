# Backend Integration Guide

## FastAPI CORS Setup

To allow your frontend to communicate with your FastAPI backend, you need to enable CORS (Cross-Origin Resource Sharing).

### 1. Install CORS Middleware

First, make sure you have `fastapi` installed with CORS support (it's included by default).

### 2. Update your FastAPI app

Add this to your `main.py` or wherever you initialize your FastAPI app:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router
import uvicorn 

app = FastAPI(
    title="Harmful Clause Detection API",
    description="An API to detect harmful clauses in documents using a language model.",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Harmful Clause Detection API. Use the /get_clauses endpoint to analyze documents."}

@app.on_event("startup")
async def startup_event():
    print("Starting up...")

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

### 3. API Endpoint Requirements

Your `/get_clauses` endpoint should accept:

**For File Upload:**
```python
from fastapi import File, UploadFile

@router.post("/get_clauses")
async def get_clauses(file: UploadFile = File(None), text: str = None):
    # Your logic here
    pass
```

**Expected Response Format:**

The frontend expects a JSON response in this format:

```json
{
  "clauses": [
    {
      "id": "1",
      "text": "The actual clause text from the document",
      "risk_level": "high",  // or "medium" or "low"
      "explanation": "Explanation of why this clause is harmful"
    },
    {
      "id": "2",
      "text": "Another clause text",
      "risk_level": "medium",
      "explanation": "Another explanation"
    }
  ]
}
```

**Alternative field names** (the frontend will adapt):
- `clause_text` instead of `text`
- `severity` instead of `risk_level`
- `reason` instead of `explanation`

### 4. Running Both Apps

**Terminal 1 - Backend:**
```bash
cd your-backend-folder
python main.py
# or
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd your-frontend-folder
npm run dev
# Frontend typically runs on http://localhost:5173
```

### 5. Update Frontend API URL

In `/App.tsx`, find this line:

```typescript
const API_BASE_URL = 'http://localhost:8000';
```

Change it to match your FastAPI server URL if different.

### 6. Testing

1. Start your FastAPI backend on port 8000
2. Start your frontend dev server
3. Upload a document or paste text
4. Click "Analyze Document"
5. Check the browser console (F12) for any errors

### Common Issues

**CORS Errors:**
- Make sure you added the CORS middleware to your FastAPI app
- Check that your frontend URL is in the `allow_origins` list

**404 Errors:**
- Verify your endpoint path is `/get_clauses`
- Check that the router is properly included in your app

**Connection Refused:**
- Make sure your FastAPI server is running on port 8000
- Check firewall settings

### Production Deployment

For production, update the CORS origins to your actual domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

And update the frontend `API_BASE_URL` to your production API URL.
