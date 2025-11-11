#!/usr/bin/env python3
"""
AI Super Agent - Production Entry Point
FastAPI server with ACL, Resource Manager, and Multi-Agent Orchestration
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import signal
import sys
import psutil
from pathlib import Path
import logging
import uuid
import time
import os # ✅ مُضاف
import json # ✅ مُضاف

# Configure logging
logging.basicConfig(
level=logging.INFO,
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
handlers=[
logging.FileHandler("logs/master-agent.log"),
logging.StreamHandler()
]
)
logger = logging.getLogger(__name__)

# Import core modules
sys.path.append(str(Path(__file__).parent))

from master.sovereign import SovereignMaster
from core.resource_manager import ResourceManager
from core.acl_engine import ACLEngine, ACLDecision
from core.trash_manager import TrashManager
from core.alert_manager import AlertManager
from core.auth_middleware import JWTVerifier, JWTGenerator, APIKeyManager
from core.rate_limiter import setup_rate_limiting
from core.shutdown import GracefulShutdown
from agents.math_agent import MathAgent
from agents.code_agent import CodeAgent
from agents.research_agent import ResearchAgent

# Pydantic models
class TaskRequest(BaseModel):
task: str
priority: int = 5
timeout_ms: int = 5000
metadata: Dict[str, Any] = {}

class ConfirmationResponse(BaseModel):
operation_id: str
approved: bool

class ResourceUpdateRequest(BaseModel):
ram_gb: Optional[int] = None
cpu_cores: Optional[int] = None
memory_limit_mb: Optional[int] = None

class MasterApplication:
def __init__(self):
logger.info("🚀 Initializing AI Super Agent Core...")

# Security and resource management
self.policy_path = Path("config/security-policy.json")
if not self.policy_path.exists():
logger.error("❌ Security policy not found! Run: python scripts/generate_user_config.py")
sys.exit(1)

self.acl = ACLEngine(str(self.policy_path))
self.resource_manager = ResourceManager(str(self.policy_path))
self.alert_manager = AlertManager(self.acl.policy)

# Initialize auth
self.jwt_verifier = JWTVerifier()
self.jwt_generator = JWTGenerator()
self.api_key_manager = APIKeyManager()

# Initialize agents
self.agents = {
"math": MathAgent(),
"code": CodeAgent(),
"research": ResearchAgent(),
}

self.master = SovereignMaster(self.agents)

# Create FastAPI app
self.app = FastAPI(
title="AI Super Agent Core API",
description="Production-ready multi-agent system with ACL and resource management",
version="1.0.0",
docs_url="/api/v1/docs" if os.getenv("ENV") != "prod" else None,
redoc_url="/api/v1/redoc" if os.getenv("ENV") != "prod" else None
)

self._setup_middleware()
self._setup_routes()
self._setup_error_handlers()
self._setup_shutdown_handler()

logger.info("✅ Master Agent initialized successfully")
logger.info(f"💾 Resource limits: {self.resource_manager.export_limits()}")

def _setup_middleware(self):
self.app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)
setup_rate_limiting(self.app)

def _setup_error_handlers(self):
@self.app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
return JSONResponse(
status_code=exc.status_code,
content={"detail": exc.detail, "timestamp": time.time()}
)

@self.app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
logger.error(f"Unhandled error: {exc}", exc_info=True)
return JSONResponse(
status_code=500,
content={"detail": "Internal server error", "error_id": str(uuid.uuid4())}
)

def _setup_shutdown_handler(self):
self.shutdown_handler = GracefulShutdown(self.app)

def _setup_routes(self):
@self.app.get("/health")
async def health():
return {
"status": "healthy",
"agents": len(self.agents),
"resources": self.resource_manager.export_limits(),
"cpu_percent": psutil.cpu_percent(),
"memory_percent": psutil.virtual_memory().percent
}

@self.app.get("/metrics")
async def metrics():
return {
"cpu_percent": psutil.cpu_percent(interval=1),
"memory": psutil.virtual_memory()._asdict(),
"disk": psutil.disk_usage('/')._asdict(),
"agents": {k: v.get_status() for k, v in self.agents.items()}
}

@self.app.post("/api/v1/task")
async def submit_task(request: TaskRequest, background_tasks: BackgroundTasks, auth: dict = Depends(self.jwt_verifier.verify)):
try:
# ACL check
decision = self.acl.check_resource_access("cpu", 1.0)
if not decision.allowed:
raise HTTPException(403, detail=decision.reason)

if decision.requires_confirmation:
operation_id = self.acl.request_confirmation(decision)
confirmed = await asyncio.to_thread(
self.acl.wait_for_confirmation, operation_id, 60.0
)
if not confirmed:
raise HTTPException(403, detail="Operation denied by user")

# Check resources
estimated_memory = self._estimate_memory_usage(request.task)
if not self.resource_manager.should_load_tool(estimated_memory):
raise HTTPException(507, detail="Insufficient resources")

# Process task
result = await self.master.decide({
"description": request.task,
"priority": request.priority,
"metadata": request.metadata
})

background_tasks.add_task(self._audit_log, "task_completed", {
"task": request.task,
"result": result
})

return {
"task_id": str(uuid.uuid4()),
"status": "completed",
"decision": result,
"confidence": result.confidence
}

except Exception as e:
logger.error(f"Task failed: {e}")
self.alert_manager.send_alert("task_failed", {"error": str(e)})
raise HTTPException(500, detail=str(e))

@self.app.get("/api/v1/agents")
async def get_agents(auth: dict = Depends(self.jwt_verifier.verify)):
return {
"agents": [agent.get_status() for agent in self.agents.values()],
"count": len(self.agents)
}

@self.app.get("/api/v1/acl/pending")
async def get_pending_confirmations(auth: dict = Depends(self.jwt_verifier.verify)):
return {
"pending": [
{
"operation_id": op_id,
"reason": decision.reason
}
for op_id, decision in self.acl.get_pending_confirmations().items()
]
}

@self.app.post("/api/v1/acl/confirm")
async def confirm_operation(response: ConfirmationResponse, auth: dict = Depends(self.jwt_verifier.verify)):
self.acl.confirm_operation(response.operation_id, response.approved)
return {"status": "confirmed"}

@self.app.get("/api/v1/trash")
async def list_trash(auth: dict = Depends(self.jwt_verifier.verify)):
trash = TrashManager(str(self.policy_path))
return {"items": trash.list_trash()}

@self.app.post("/api/v1/resource/update")
async def update_resource(request: ResourceUpdateRequest, auth: dict = Depends(self.jwt_verifier.verify)):
try:
self.resource_manager.update_config(request.dict(exclude_unset=True))
return {"status": "updated", "new_limits": self.resource_manager.export_limits()}
except Exception as e:
raise HTTPException(500, detail=str(e))

# Auth endpoints
@self.app.get("/api/v1/auth/token")
async def generate_token(service: str, auth: dict = Depends(self.jwt_verifier.verify)):
token = self.jwt_generator.generate_service_token(service)
return {"token": token, "expires_in": 86400}

@self.app.post("/api/v1/auth/api-key")
async def create_api_key(service: str, auth: dict = Depends(self.jwt_verifier.verify)):
key = self.api_key_manager.create_key(service)
return {"api_key": key, "service": service, "note": "Save this key"}

@self.app.get("/api/v1/auth/verify")
async def verify_auth(request: Request, auth: dict = Depends(self.jwt_verifier.verify)):
return {
"authenticated": True,
"user": request.state.user,
"scopes": request.state.scopes
}

def _estimate_memory_usage(self, task: str) -> int:
"""Estimate memory needed in MB"""
if "image" in task.lower() or "video" in task.lower():
return 4096
elif "model" in task.lower() or "train" in task.lower():
return 8192
elif "research" in task.lower() or "search" in task.lower():
return 2048
else:
return 1024

def _audit_log(self, event: str, data: Dict[str, Any]):
"""Async audit logging"""
audit_file = Path("logs/audit.log")
audit_file.parent.mkdir(exist_ok=True)

with open(audit_file, 'a') as f:
f.write(json.dumps({
"timestamp": time.time(),
"event": event,
"data": data
}) + "\n")

def run(self, host: str = "0.0.0.0", port: int = 8000):
"""Run the production server"""
logger.info(f"🚀 Starting server on {host}:{port}")

uvicorn.run(
self.app,
host=host,
port=port,
workers=1,
log_level="info",
access_log=True,
loop="uvloop",
timeout_keep_alive=30,
ssl_certfile="docker/ssl/cert.pem" if os.getenv("ENV") == "prod" else None,
ssl_keyfile="docker/ssl/key.pem" if os.getenv("ENV") == "prod" else None
)

if __name__ == "__main__":
import json
app = MasterApplication()
app.run()
