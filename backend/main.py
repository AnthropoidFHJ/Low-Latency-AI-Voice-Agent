import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from pipeline import create_pipeline

load_dotenv()

app = FastAPI(title="Voice Agent Backend", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Voice Agent Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "api_key_loaded": bool(os.getenv('GEMINI_API_KEY'))}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    pipeline = create_pipeline()
    await pipeline.run(ws)

if __name__ == "__main__":
    import uvicorn
    print("Starting Voice Agent Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
