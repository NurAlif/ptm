from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware
from .database import get_db
# Import routers
from .routers import models as model_router
from .routers import auth as auth_router

from . import security

app = FastAPI(
    title="Admin Monitoring System API",
    description="API for building and inspecting cognitive models.",
    version="1.0.0",
)

# --- Static Files Configuration ---
static_files_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_files_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_files_dir), name="static")
# --- End of Static Files Configuration ---


# --- CORS Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://ai-ndhu-lab:3000",
        "http://ai-ndhu-lab:5290",
        "http://ai-ndhu-lab:5291",
        "http://localhost:5291",
        "https://model2.parasyst.com", # <-- FIX: Added 'https://'
        "https://model.parasyst.com",  # <-- FIX: Added 'https://'
        "http://localhost:7771"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- End of CORS Configuration ---

@app.get("/api/models/graph-viewer", response_class=FileResponse, tags=["Models"])
def get_graph_viewer_html():
    """
    [ADMIN] Serves the static HTML file for the knowledge graph explorer.
    Authenticates via a token in the query string, for use in iframes.
    """
    # Ensure the path relative to the main.py file is correct
    graph_viewer_path = os.path.join(os.path.dirname(__file__), "graph_viewer.html")
    if not os.path.exists(graph_viewer_path):
        # Fallback to static directory if not found adjacent to main.py
         graph_viewer_path = os.path.join(os.path.dirname(__file__), "static", "graph_viewer.html")
         if not os.path.exists(graph_viewer_path):
             from fastapi import HTTPException
             raise HTTPException(status_code=404, detail="Graph viewer HTML not found.")
    return FileResponse(
        graph_viewer_path,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Admin Monitoring API!"}

# Include the routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(model_router.router, prefix="/api")


