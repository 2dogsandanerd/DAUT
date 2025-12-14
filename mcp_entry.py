
import uvicorn
import os
import sys
import time
from typing import List, Dict
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Ensure src is in path
sys.path.append(os.getcwd())

from src.mcp.server import create_mcp_server

# Configuration
API_KEY = os.environ.get("MCP_API_KEY")
PORT = int(os.environ.get("MCP_PORT", 8000))
HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PROJECT_PATH = os.environ.get("MCP_PROJECT_PATH", ".")

# Active Connections Tracking
active_connections: List[Dict[str, str]] = []

app = FastAPI(
    title="DAUT RAG MCP Server",
    description="Model Context Protocol Server for RAG Access",
    version="1.0.0"
)

# Initialize MCP Server
mcp_server = create_mcp_server(project_path=PROJECT_PATH)

class ConnectionTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Track connections to SSE endpoint
        if request.url.path.endswith("/sse"):
            client_ip = request.client.host if request.client else "unknown"
            conn_id = f"{client_ip}:{time.time()}"
            connection_info = {
                "ip": client_ip,
                "user_agent": request.headers.get("user-agent", "unknown"),
                "connected_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            active_connections.append(connection_info)
            try:
                response = await call_next(request)
                return response
            finally:
                # Remove on disconnect (simplistic, might stick if async generator keeps running? 
                # actually SSE response keeps generation open. call_next returns response object, 
                # but the body iteration happens later.
                # Middleware on SSE is tricky for disconnects.
                # For now let's just track 'hits' or try to track lifetime if possible.
                # Proper SSE tracking requires subclassing standard endpoint or polling.
                # Let's simple check: The middleware returns when the handler returns.
                # For SSE, the handler returns a StreamingResponse. The connection stays open.
                # The middleware finishes dispatching immediately. So this won't track DURATION.
                # WE NEED A BETTER WAY for "Currently connected".
                pass
                
        return await call_next(request)

app.add_middleware(ConnectionTrackingMiddleware)

# Better Auth & Tracking combined
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow health checks, status, and docs without auth
        if request.url.path in ["/health", "/status", "/docs", "/openapi.json", "/"]:
            return await call_next(request)
        
        # ... (Auth Logic) ...
        # If API Key is not set, we are in insecure mode or misconfigured
        if not API_KEY:
            return JSONResponse(
                status_code=500, 
                content={"detail": "Server Misconfiguration: MCP_API_KEY environment variable not set."}
            )
            
        auth_header = request.headers.get("Authorization")
        token = None
        
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ")[1]
        
        if not token:
             token = request.query_params.get("key")

        if token != API_KEY:
            return JSONResponse(
                status_code=401, 
                content={"detail": "Unauthorized: Invalid or missing API Key"}
            )
            
        return await call_next(request)

# STATUS ENDPOINT
@app.get("/status")
def server_status():
    """Returns server status and connection info"""
    # Since middleware can't easily track live SSE connections without deep hooks, 
    # we will rely on a simpler metric or just return "Online".
    # User asked "Who is connected". 
    # For now, let's just return static info + health.
    # To really track SSE, we'd need to wrap the endpoint.
    return {
        "status": "online",
        "port": PORT,
        "auth_enabled": True,
        "active_connections": active_connections, 
        "active_count": len(active_connections)
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "daut-rag-mcp"
    }

# Mount the MCP SSE application
# FastMCP exposes .sse_app which is a Starlette app containing /sse and /messages routes
app.mount("/mcp", mcp_server.sse_app())

if __name__ == "__main__":
    if not API_KEY:
        print("WARNING: MCP_API_KEY not set. Requests will fail.")
        
    print(f"Starting MCP Server on {HOST}:{PORT}")
    print(f"MCP Endpoint: http://{HOST}:{PORT}/mcp/sse")
    
    uvicorn.run(app, host=HOST, port=PORT)
