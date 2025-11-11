#!/usr/bin/env python3
"""
Generate user security configuration
"""

import json
import os
from pathlib import Path
import sys

def generate_config(user_id: str = "default-user", protection_level: str = "paranoid"):
    """Generate security policy configuration"""

    config = {
    "user_id": user_id,
    "protection_level": protection_level,
    "resource_allocation": {
    "ram_gb": min(os.cpu_count() or 4, 8),
    "cpu_cores": min(os.cpu_count() or 4, 4),
    "memory_limit_mb": 2048,
    "gpu_memory_gb": 0
    },
    "recovery": {
    "trash_retention_days": 30,
    "permanent_delete": False,
    "backup_enabled": True
    },
    "acl_rules": {
    "resource_access": {
    "cpu": {"max_cores": 4, "require_confirmation": False},
    "memory": {"max_gb": 8, "require_confirmation": True, "emergency_threshold": 95},
    "disk": {"require_confirmation": True, "blocked_extensions": [".exe", ".sh"], "max_daily_operations": 1000},
    "network": {"allowed_domains": ["localhost", "api.openai.com"], "require_confirmation": True}
    },
    "file_operations": {
    "create": {"allowed": True, "require_confirmation": False, "max_daily_operations": 500},
    "delete": {"allowed": True, "require_confirmation": True, "max_daily_operations": 100},
    "modify": {"allowed": True, "require_confirmation": False},
    "read": {"allowed": True, "require_confirmation": False}
    },
    "confirmation_methods": {"ui_modal": True, "timeout_seconds": 60}
    },
    "alerts": {
    "email": os.getenv("ALERT_EMAIL", ""),
    "webhook": os.getenv("ALERT_WEBHOOK", ""),
    "enable_sound": True
    }
    }

    # Adjust based on protection level
    if protection_level == "minimal":
        config["acl_rules"]["resource_access"]["memory"]["require_confirmation"] = False
        config["acl_rules"]["resource_access"]["disk"]["require_confirmation"] = False
        config["acl_rules"]["file_operations"]["delete"]["require_confirmation"] = False
    elif protection_level == "strict":
        config["acl_rules"]["file_operations"]["create"]["require_confirmation"] = True

    # Create config directory
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    # Write policy
    policy_file = config_dir / "security-policy.json"
    with open(policy_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ Generated security policy: {policy_file}")
    print(f" User: {user_id}")
    print(f" Protection: {protection_level}")
    print(f"\n🚨 IMPORTANT: Review and adjust the policy before running!")

    return config

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate security config")
    parser.add_argument("--user", default="default-user", help="User ID")
    parser.add_argument("--level", default="paranoid", choices=["minimal", "strict", "paranoid"], help="Protection level")

    args = parser.parse_args()
    generate_config(args.user, args.level)
