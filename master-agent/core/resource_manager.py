import psutil
import os
import json
from pathlib import Path
from typing import Dict, Any
import resource
import torch
import logging
from .acl_engine import ACLEngine # ✅ مُضاف

logger = logging.getLogger(__name__)

class ResourceManager:
def __init__(self, config_path: str = "config/security-policy.json"):
self.config_path = Path(config_path)
self.config = self._load_config()
self.acl = ACLEngine(str(self.config_path))
self._check_and_apply_limits()

def _load_config(self) -> Dict[str, Any]:
with open(self.config_path, 'r') as f:
return json.load(f)

def _check_and_apply_limits(self):
alloc = self.config['resource_allocation']

# ACL check first
mem_decision = self.acl.check_resource_access("memory", alloc['ram_gb'])
if not mem_decision.allowed:
raise PermissionError(f"Memory allocation denied: {mem_decision.reason}")

cpu_decision = self.acl.check_resource_access("cpu", alloc['cpu_cores'])
if not cpu_decision.allowed:
raise PermissionError(f"CPU allocation denied: {cpu_decision.reason}")

self._apply_system_limits()

def _apply_system_limits(self):
alloc = self.config['resource_allocation']

# Memory limit
memory_bytes = alloc['ram_gb'] * 1024 * 1024 * 1024
try:
resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
except ValueError as e:
logger.warning(f"Could not set memory limit: {e}")

# CPU affinity
cpu_cores = alloc['cpu_cores']
all_cores = list(range(len(os.sched_getaffinity(0))))
try:
os.sched_setaffinity(0, all_cores[:cpu_cores])
except OSError as e:
logger.warning(f"Could not set CPU affinity: {e}")

# GPU memory if available
if torch.cuda.is_available() and alloc.get('gpu_memory_gb', 0) > 0:
try:
gpu_mem_bytes = alloc['gpu_memory_gb'] * 1024 * 1024 * 1024
for i in range(torch.cuda.device_count()):
torch.cuda.set_per_process_memory_fraction(
gpu_mem_bytes / torch.cuda.get_device_properties(i).total_memory, i
)
except Exception as e:
logger.warning(f"Could not set GPU limit: {e}")

logger.info(f"✅ Resource limits applied: {alloc}")

def get_available_memory(self) -> int:
return psutil.virtual_memory().available // (1024 * 1024)

def should_load_tool(self, tool_size_mb: int) -> bool:
available = self.get_available_memory()
limit = self.config['resource_allocation']['memory_limit_mb']

if tool_size_mb > limit:
logger.warning(f"Tool size {tool_size_mb}MB exceeds limit {limit}MB")
return False

if tool_size_mb > available:
logger.warning(f"Not enough memory: need {tool_size_mb}MB, available {available}MB")
return False

decision = self.acl.check_resource_access("memory", tool_size_mb / 1024)
return decision.allowed

def update_config(self, new_config: Dict[str, Any]):
"""Hot update resource limits"""
self.config['resource_allocation'].update(new_config)

with open(self.config_path, 'w') as f:
json.dump(self.config, f, indent=2)

self._apply_system_limits()
logger.info(f"✅ Config hot-updated: {new_config}")

def export_limits(self) -> Dict[str, Any]:
return {
"config": self.config['resource_allocation'],
"actual": {
"ram_gb": psutil.virtual_memory().total // (1024**3),
"cpu_cores": len(os.sched_getaffinity(0)),
"memory_available_mb": self.get_available_memory()
}
}
