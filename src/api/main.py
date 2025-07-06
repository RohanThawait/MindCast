from fastapi import FastAPI, HTTPException, Query,Request
from pydantic import BaseModel
from fastapi.responses import FileResponse,JSONResponse
from typing import Optional
import os
import logging
from fastapi.middleware.cors import CORSMiddleware
from src.agent.graph import create_compiled_graph
from src.agent.state import ResearchStateInput
from fastapi.staticfiles import StaticFiles
import traceback

# Initialize FastAPI app
app = FastAPI(
    title="MindCast AI",
    description="Generate podcast + research reports from a topic and optional video",
    version="1.0.0"
)

os.makedirs("podcasts", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# CORS (optional for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev — change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(os.getcwd(), "podcasts")), name="static")
app.mount("/reports", StaticFiles(directory=os.path.join(os.getcwd(), "reports")), name="reports")



graph = create_compiled_graph()
logger = logging.getLogger(__name__)


# --------------------------
# ✅ Input schema for POST
# --------------------------
class InputPayload(BaseModel):
    topic: str
    video_url: Optional[str] = None


# --------------------------
# ✅ Health Check
# --------------------------
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "MindCast backend is running."}


# --------------------------
# ✅ Main Inference Endpoint
# --------------------------
# src/agent/main.py

@app.post("/run")
async def run_mindcast(payload: ResearchStateInput, request: Request):
    try:
        result = graph.invoke(payload)
        
        return {
            "report": result.get("report"),
            "podcast_script": result.get("podcast_script"),
            "podcast_filename": result.get("podcast_filename"),
        }

    except Exception as e:
        error_str = str(e)

        # Gemini quota-specific check
        if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            return JSONResponse(
                status_code=200,  # Keep 200 to avoid Streamlit exception
                content={"error": "Gemini API quota exceeded. Please wait 1 minute and try again."}
            )
        # Generic error
        traceback.print_exc()
        return JSONResponse(
            status_code=200,
            content={"error": f"Internal error: {error_str}"}
        )



# --------------------------
# ✅ Serve Files (Optional)
# --------------------------
@app.get("/download/{filename}")
def download_file(filename: str):
    """Download podcast or report from /reports or /podcasts folder."""
    # Check both folders
    for folder in ["reports", "podcasts"]:
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")
