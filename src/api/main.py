from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import FileResponse
from typing import Optional
import os
import logging
from fastapi.middleware.cors import CORSMiddleware
from src.agent.graph import create_compiled_graph
from src.agent.configuration import Configuration
from src.agent.state import ResearchStateInput, ResearchStateOutput
from fastapi.staticfiles import StaticFiles

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
@app.post("/run", response_model=ResearchStateOutput)
def generate_content(payload: InputPayload):
    try:
        # Run the LangGraph workflow
        result = graph.invoke(
            input=ResearchStateInput(
                topic=payload.topic,
                video_url=payload.video_url
            ),
            config={"configurable": Configuration().to_dict()}
        )

        return result
    except Exception as e:
        logger.exception("Failed to run MindCast pipeline.")
        raise HTTPException(status_code=500, detail=str(e))


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
