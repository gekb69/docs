import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPGatewayServer:
"""MCP Protocol Server for tool integration"""

def __init__(self, auth_handler, host: str = "0.0.0.0", port: int = 8080):
self.host = host
self.port = port
self.auth_handler = auth_handler
self.tools: Dict[str, Dict] = {}
self.connections = {}

# Load available tools
self._load_tools()

def _load_tools(self):
"""Scan and register available tools"""
tools_dir = Path("/opt/super-agent/tools-bundle")
if not tools_dir.exists():
logger.warning(f"Tools directory not found: {tools_dir}")
return

for tool_path in tools_dir.rglob("*.py"):
if tool_path.name == "tool.py":
tool_name = tool_path.parent.name
self.tools[tool_name] = {
"path": tool_path,
"status": "available",
"loaded": False
}
logger.info(f"📦 Registered tool: {tool_name}")

async def start(self):
"""Start TCP server"""
server = await asyncio.start_server(
self._handle_client,
self.host,
self.port
)

logger.info(f"✅ MCP Gateway listening on {self.host}:{self.port}")

async with server:
await server.serve_forever()

async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
"""Handle incoming MCP client connection"""
peername = writer.get_extra_info('peername')
logger.info(f"🔌 New connection from {peername}")

try:
# Authenticate first
auth_data = await reader.readuntil(b'\n')
if not self.auth_handler.authenticate(auth_data):
writer.write(b"ERR: Authentication failed\n")
await writer.drain()
writer.close()
return

writer.write(b"OK: Authenticated\n")
await writer.drain()

# Process commands
while True:
data = await reader.readuntil(b'\n')
if not data:
break

command = data.decode().strip()
response = await self._process_command(command)
writer.write(f"{response}\n".encode())
await writer.drain()

except asyncio.IncompleteReadError:
logger.info(f"🔌 Connection closed by {peername}")
except Exception as e:
logger.error(f"❌ Error handling client {peername}: {e}")
finally:
writer.close()
await writer.wait_closed()

async def _process_command(self, command: str) -> str:
"""Process MCP command"""
parts = command.split()
if not parts:
return "ERR: Empty command"

cmd = parts[0].upper()

if cmd == "LIST_TOOLS":
return json.dumps({
"tools": list(self.tools.keys()),
"count": len(self.tools)
})

elif cmd == "LOAD" and len(parts) == 2:
tool_name = parts[1]
return await self._load_tool(tool_name)

elif cmd == "EXECUTE" and len(parts) >= 3:
tool_name = parts[1]
args = json.loads(" ".join(parts[2:]))
return await self._execute_tool(tool_name, args)

elif cmd == "STATUS":
return json.dumps({
"connections": len(self.connections),
"tools": {
name: {
"status": tool["status"],
"loaded": tool["loaded"]
}
for name, tool in self.tools.items()
}
})

else:
return f"ERR: Unknown command {cmd}"

async def _load_tool(self, tool_name: str) -> str:
"""Load a tool dynamically"""
if tool_name not in self.tools:
return f"ERR: Tool {tool_name} not found"

tool = self.tools[tool_name]
try:
# Simulate tool loading
tool["loaded"] = True
tool["status"] = "ready"
logger.info(f"✅ Tool loaded: {tool_name}")
return f"OK: Tool {tool_name} loaded"
except Exception as e:
tool["status"] = f"error: {e}"
return f"ERR: Failed to load {tool_name}: {e}"

async def _execute_tool(self, tool_name: str, args: Dict) -> str:
"""Execute a loaded tool"""
if tool_name not in self.tools:
return f"ERR: Tool {tool_name} not found"

tool = self.tools[tool_name]
if not tool["loaded"]:
return f"ERR: Tool {tool_name} not loaded"

try:
# Simulate execution
result = {
"tool": tool_name,
"status": "success",
"output": f"Executed with args: {args}",
"timestamp": datetime.utcnow().isoformat()
}
logger.info(f"⚙️ Tool executed: {tool_name}")
return json.dumps(result)
except Exception as e:
logger.error(f"❌ Tool execution error: {e}")
return f"ERR: Execution failed: {e}"
