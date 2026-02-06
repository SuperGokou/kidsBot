"""
KidBot FastAPI Backend

Main entry point for the FastAPI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import load_config
from .core.dependencies import init_dependencies, get_llm_client, get_memory_manager
from .core.response_parser import parse_response
from .api import api_router
from .api.parent import load_parent_profile, get_parent_profile_data
from .services.interactions import load_interactions
from .models import StatusResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    print("[Backend] Starting KidBot API...")
    
    # Load configuration
    config = load_config()
    
    # Initialize all dependencies
    init_dependencies(config)
    
    # Load persisted data
    load_parent_profile()
    load_interactions()
    
    print("[Backend] KidBot API ready!")
    yield
    print("[Backend] Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="KidBot API",
    description="Backend API for KidBot - AI Companion for Kids",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for React frontend
import os
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
# Add production frontend URL if set
if FRONTEND_URL:
    CORS_ORIGINS.append(FRONTEND_URL)
# Allow all Render.com subdomains
CORS_ORIGINS.append("https://*.onrender.com")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


# =============================================================================
# Root Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "KidBot API", "version": "1.0.0"}


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status and registration info."""
    from .core.dependencies import get_config
    
    config = get_config() or {}
    robot_config = config.get("robot", {})
    parent_profile = get_parent_profile_data()
    
    # Check if owner is registered (voice print exists)
    from .config import DATA_DIR
    voice_print_file = DATA_DIR / "voice_prints" / "owner_embedding.npy"
    is_registered = voice_print_file.exists()
    
    return StatusResponse(
        status="ready" if is_registered else "setup_required",
        owner_registered=is_registered,
        robot_name=robot_config.get("name", "VV"),
        personality=robot_config.get("personality", "friendly"),
        parent_registered=parent_profile is not None
    )


# =============================================================================
# WebSocket for Real-time Communication
# =============================================================================

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    Supports streaming responses and bidirectional communication.
    """
    llm_client = get_llm_client()
    memory_manager = get_memory_manager()
    
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            message = data.get("message", "")
            mode = data.get("mode", "chat")
            
            if not message:
                continue
            
            # Get context
            context_chunks = memory_manager.query_memory(message) if memory_manager else []
            
            # Stream response
            await websocket.send_json({"type": "start"})
            
            full_response = ""
            for chunk in llm_client.get_response_stream(message, context_chunks, mode):
                full_response += chunk
                await websocket.send_json({"type": "chunk", "content": chunk})
            
            # Parse commands
            commands, clean_response = parse_response(full_response)
            
            await websocket.send_json({
                "type": "done",
                "response": clean_response,
                "mode": commands.get("mode"),
                "action": commands.get("action")
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
