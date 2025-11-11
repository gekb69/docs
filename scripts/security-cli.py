#!/usr/bin/env python3
"""
Security CLI for confirming operations
"""

import sys
from pathlib import Path
import argparse
import json
import time

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent / "master-agent"))

from core.acl_engine import ACLEngine

def list_pending():
"""List pending confirmations"""
acl = ACLEngine()
pending = acl.get_pending_confirmations()

if not pending:
print("✅ No pending confirmations")
return

print(f"📋 {len(pending)} pending confirmations:\n")
for op_id, decision in pending.items():
print(f"ID: {op_id}")
print(f"Reason: {decision.reason}")
print(f"Requires confirmation: {decision.requires_confirmation}")
print(f"Allowed: {decision.allowed}")
print("-" * 50)

def confirm(operation_id: str, approve: bool):
"""Confirm or deny an operation"""
acl = ACLEngine()

try:
acl.confirm_operation(operation_id, approve)
action = "approved" if approve else "denied"
print(f"✅ Operation {operation_id} {action}")
except Exception as e:
print(f"❌ Error: {e}")

def watch():
"""Watch for pending confirmations"""
print("👀 Watching for pending confirmations (Ctrl+C to stop)...")
acl = ACLEngine()

try:
while True:
pending = acl.get_pending_confirmations()
if pending:
print(f"\n🚨 {len(pending)} new pending confirmations!")
list_pending()
time.sleep(2)
except KeyboardInterrupt:
print("\n👋 Stopped")

def main():
parser = argparse.ArgumentParser(description="Security CLI for Super Agent")
subparsers = parser.add_subparsers(dest="command", help="Available commands")

# List command
list_parser = subparsers.add_parser("list", help="List pending confirmations")

# Confirm command
confirm_parser = subparsers.add_parser("confirm", help="Confirm an operation")
confirm_parser.add_argument("operation_id", help="Operation ID")
confirm_parser.add_argument("action", choices=["yes", "no"], help="Approve or deny")

# Watch command
watch_parser = subparsers.add_parser("watch", help="Watch for pending confirmations")

args = parser.parse_args()

if args.command == "list":
list_pending()
elif args.command == "confirm":
confirm(args.operation_id, args.action == "yes")
elif args.command == "watch":
watch()
else:
parser.print_help()

if __name__ == "__main__":
main()
