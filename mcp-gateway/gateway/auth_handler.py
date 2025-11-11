import os
import hmac
import hashlib
import logging
from typing import Dict, Optional
import base64

logger = logging.getLogger(__name__)

class MCPAuthHandler:
"""Handles MCP authentication using HMAC"""

def __init__(self, secret_key: Optional[str] = None):
self.secret_key = secret_key or os.getenv("MCP_SECRET_KEY")
if not self.secret_key:
raise RuntimeError("MCP_SECRET_KEY not set!")

def authenticate(self, auth_data: bytes) -> bool:
"""Authenticate incoming connection"""
try:
# Format: HMAC
auth_str = auth_data.decode().strip()
if not auth_str.startswith("HMAC "):
logger.warning("Invalid auth format")
return False

parts = auth_str.split()
if len(parts) != 3:
logger.warning("Invalid auth parts")
return False

signature_b64 = parts[1]
timestamp = parts[2]

# Verify timestamp (prevent replay attacks)
import time
if abs(time.time() - int(timestamp)) > 60:
logger.warning("Auth timestamp expired")
return False

# Verify HMAC
message = f"{timestamp}".encode()
expected_hmac = hmac.new(
self.secret_key.encode(),
message,
hashlib.sha256
).digest()

expected_b64 = base64.b64encode(expected_hmac).decode()

if hmac.compare_digest(signature_b64, expected_b64):
logger.info("✅ MCP authentication successful")
return True
else:
logger.warning("❌ MCP authentication failed")
return False

except Exception as e:
logger.error(f"Auth error: {e}")
return False

def generate_auth_header(self) -> str:
"""Generate auth header for client"""
import time
timestamp = str(int(time.time()))
message = timestamp.encode()

signature = hmac.new(
self.secret_key.encode(),
message,
hashlib.sha256
).digest()

signature_b64 = base64.b64encode(signature).decode()
return f"HMAC {signature_b64} {timestamp}"
