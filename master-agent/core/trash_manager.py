import shutil
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, List
import hashlib # ✅ مُضاف
import logging

logger = logging.getLogger(__name__)

class TrashManager:
def __init__(self, config_path: str = "config/security-policy.json"):
self.config_path = Path(config_path)
with open(self.config_path, 'r') as f:
self.config = json.load(f)

self.trash_dir = Path.home() / ".super-agent" / "trash"
self.trash_dir.mkdir(parents=True, exist_ok=True)
self.retention_days = self.config['recovery'].get('trash_retention_days', 30)

logger.info(f"🗑️ Trash Manager: {self.trash_dir}")
logger.info(f"📅 Retention: {self.retention_days} days")

def delete_to_trash(self, path: Path, permanent: bool = False) -> Dict[str, Any]:
if permanent and not self.config['recovery'].get('permanent_delete', False):
raise PermissionError("Permanent deletion is disabled by security policy")

if not path.exists():
raise FileNotFoundError(f"Path not found: {path}")

trash_id = hashlib.sha256(f"{path}_{time.time()}".encode()).hexdigest()[:16]
trash_subdir = self.trash_dir / trash_id
trash_subdir.mkdir(parents=True)

# Move to trash
dest = trash_subdir / path.name
if path.is_file():
shutil.move(str(path), str(dest))
else:
shutil.move(str(path), str(trash_subdir))

# Metadata
metadata = {
"trash_id": trash_id,
"original_path": str(path),
"deleted_at": time.time(),
"file_size": self._get_size(dest if path.is_file() else trash_subdir / path.name),
"permanent": permanent,
"recoverable": not permanent
}

with open(trash_subdir / "metadata.json", 'w') as f:
json.dump(metadata, f, indent=2)

self._add_to_index(metadata)
logger.info(f"📦 Moved to trash: {path} -> {trash_id}")

return metadata

def restore(self, trash_id: str) -> Path:
trash_subdir = self.trash_dir / trash_id

if not trash_subdir.exists():
raise FileNotFoundError(f"Trash item {trash_id} not found")

with open(trash_subdir / "metadata.json", 'r') as f:
metadata = json.load(f)

if not metadata.get('recoverable', False):
raise PermissionError("This item is not recoverable")

# Find the file/directory
items = [p for p in trash_subdir.iterdir() if p.name != "metadata.json" and p.name != "index.json"]
if not items:
raise FileNotFoundError("No items found in trash")

restore_path = items[0]
original_path = Path(metadata['original_path'])

# Handle conflicts
if original_path.exists():
suffix = f"_restored_{int(time.time())}"
original_path = original_path.parent / f"{original_path.stem}{suffix}{original_path.suffix}"

# Restore
shutil.move(str(restore_path), str(original_path))

# Update metadata
metadata['restored_at'] = time.time()
metadata['restored_to'] = str(original_path)

with open(trash_subdir / "metadata.json", 'w') as f:
json.dump(metadata, f, indent=2)

logger.info(f"✅ Restored: {original_path}")
return original_path

def list_trash(self) -> List[Dict[str, Any]]:
items = []
for trash_id in os.listdir(self.trash_dir):
try:
trash_subdir = self.trash_dir / trash_id
if trash_subdir.is_dir():
with open(trash_subdir / "metadata.json", 'r') as f:
items.append(json.load(f))
except Exception as e:
logger.warning(f"Error reading trash item {trash_id}: {e}")

return sorted(items, key=lambda x: x['deleted_at'], reverse=True)

def empty_trash(self, older_than_days: int = None):
if older_than_days is None:
older_than_days = self.retention_days

cutoff_time = time.time() - (older_than_days * 86400)
deleted_count = 0

for item in self.list_trash():
if item['deleted_at'] < cutoff_time:
try:
shutil.rmtree(self.trash_dir / item['trash_id'])
deleted_count += 1
except Exception as e:
logger.error(f"Failed to delete {item['trash_id']}: {e}")

logger.info(f"🧹 Emptied {deleted_count} old trash items")

def _get_size(self, path: Path) -> int:
if path.is_file():
return path.stat().st_size

total = 0
for item in path.rglob('*'):
if item.is_file():
total += item.stat().st_size

return total

def _add_to_index(self, metadata: Dict[str, Any]):
index_path = self.trash_dir / "index.json"

index = []
if index_path.exists():
with open(index_path, 'r') as f:
index = json.load(f)

index.append(metadata)

with open(index_path, 'w') as f:
json.dump(index, f, indent=2)
