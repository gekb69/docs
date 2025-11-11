#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Gateway
Handles external tool connections and authentication
"""

import asyncio
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(str(Path(__file__).parent))

from gateway.server import MCPGatewayServer
from gateway.auth_handler import MCPAuthHandler

class MCPGateway:
def __init__(self, host: str = "0.0.0.0", port: int = 8080):
self.host = host
self.port = port
self.auth_handler = MCPAuthHandler()
self.server = MCPGatewayServer(self.auth_handler, host, port)

logger.info(f"🔌 MCP Gateway starting on {host}:{port}")

def run(self):
"""Run the MCP gateway server"""
try:
asyncio.run(self.server.start())
except KeyboardInterrupt:
logger.info("🛑 MCP Gateway stopped")
except Exception as e:
logger.error(f"❌ MCP Gateway error: {e}", exc_info=True)

if __name__ == "__main__":
gateway = MCPGateway()
gateway.run()
