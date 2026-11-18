from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import os

from search_engine import engine
from dataset_loader import get_sample_dataset, parse_upload_file

app = FastAPI(title="AI-HNSW-Search")
MAX_UPLOAD_ROWS = int(os.getenv("MAX_UPLOAD_ROWS", "0") or 0)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    k: int = Field(default=20, ge=1, le=100)

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith((".json", ".csv")):
        return {"error": "Invalid file format. Please upload a JSON or CSV file."}
    
    contents = await file.read()
    
    try:
        texts = parse_upload_file(contents, file.filename)

        if not texts:
            return {"error": "No valid text found in file."}
        
        original_count = len(texts)
        if MAX_UPLOAD_ROWS > 0 and original_count > MAX_UPLOAD_ROWS:
            texts = texts[:MAX_UPLOAD_ROWS]

        count = engine.replace(texts)
        message = f"Successfully loaded {count} documents from {file.filename}"
        if MAX_UPLOAD_ROWS > 0 and original_count > MAX_UPLOAD_ROWS:
            message += f" (limited to first {MAX_UPLOAD_ROWS} rows for faster local processing)"
        return {"message": message}
        
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

@app.post("/sample_data")
def load_sample_data():
    sample_data = get_sample_dataset()
    count = engine.replace(sample_data)
    return {"message": f"Successfully loaded {count} sample documents."}

@app.post("/search")
def search(request: SearchRequest):
    if not request.query.strip():
        return {"error": "Empty query"}
        
    results = engine.search(request.query.strip(), request.k)
    return results

@app.get("/stats")
def get_stats():
    return engine.stats()

@app.get("/history")
def get_history():
    return {"history": engine.history}

if __name__ == "__main__":
    # Run from the `backend/` folder as documented in the README.
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
