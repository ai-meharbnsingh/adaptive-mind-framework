# 03_Demo_Interface/enhanced_api_key_manager_methods.py

"""
Enhanced API Key Manager Methods for Session 7 - Dual-Mode Support
Add these methods to your existing api_key_manager.py file

These methods provide:
1. Secure buyer API key storage
2. Session management
3. Security audit support
4. Enterprise-grade key handling

Created: August 18, 2025
Author: Adaptive Mind Framework Team
Version: 1.0
"""

import asyncio
import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ADD THESE METHODS TO YOUR EXISTING APIKeyManager CLASS:

async def store_buyer_keys_securely(self, session_id: str, api_keys: Dict[str, str]) -> str:
    """
    Securely store buyer API keys in memory with enterprise security measures
    Returns security audit ID for tracking
    """
    try:
        # Generate security audit ID
        audit_id = str(uuid.uuid4())

        # Create session metadata
        session_metadata = {
            "session_id": session_id,
            "audit_id": audit_id,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=self.key_lifetime_minutes),
            "key_count": len(api_keys),
            "providers": list(api_keys.keys()),
            "last_accessed": datetime.now(timezone.utc),
            "access_count": 0
        }

        # Store keys with encryption simulation (in production, use real encryption)
        encrypted_keys = {}
        for provider, key in api_keys.items():
            # Simulate encryption (in production, use proper AES-256 encryption)
            encrypted_key = self._encrypt_key(key)
            encrypted_keys[provider] = encrypted_key

        # Store in memory with metadata
        self._active_buyer_keys[session_id] = {
            "keys": encrypted_keys,
            "metadata": session_metadata,
            "security_hash": self._generate_security_hash(session_id, api_keys)
        }

        # Set up automatic expiration
        await self._schedule_key_expiration(session_id)

        logger.info(
            f"🔐 Buyer keys stored securely for session: {session_id} (Audit ID: {audit_id})")

        return audit_id

    except Exception as e:
        logger.error(f"Failed to store buyer keys: {str(e)}")
        raise


async def get_stored_keys(self, session_id: str) -> Optional[Dict[str, str]]:
    """
    Retrieve and decrypt stored buyer keys
    """
    try:
        if session_id not in self._active_buyer_keys:
            return None

        session_data = self._active_buyer_keys[session_id]

        # Check if keys have expired
        if datetime.now(timezone.utc) > session_data["metadata"]["expires_at"]:
            await self.cleanup_session(session_id)
            return None

        # Update access tracking
        session_data["metadata"]["last_accessed"] = datetime.now(timezone.utc)
        session_data["metadata"]["access_count"] += 1

        # Decrypt keys
        decrypted_keys = {}
        for provider, encrypted_key in session_data["keys"].items():
            decrypted_key = self._decrypt_key(encrypted_key)
            decrypted_keys[provider] = decrypted_key

        logger.info(f"🔓 Retrieved keys for session: {session_id}")

        return decrypted_keys

    except Exception as e:
        logger.error(f"Failed to retrieve stored keys: {str(e)}")
        return None


async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session metadata and status information
    """
    try:
        if session_id not in self._active_buyer_keys:
            return None

        session_data = self._active_buyer_keys[session_id]
        metadata = session_data["metadata"].copy()

        # Convert datetime objects to ISO strings for JSON serialization
        metadata["created_at"] = metadata["created_at"].isoformat()
        metadata["expires_at"] = metadata["expires_at"].isoformat()
        metadata["last_accessed"] = metadata["last_accessed"].isoformat()

        # Add current status
        metadata["is_expired"] = datetime.now(
            timezone.utc) > session_data["metadata"]["expires_at"]
        metadata["time_remaining_minutes"] = max(0,
                                                 (session_data["metadata"]["expires_at"] - datetime.now(
                                                     timezone.utc)).total_seconds() / 60
                                                 )

        return metadata

    except Exception as e:
        logger.error(f"Failed to get session info: {str(e)}")
        return None


async def cleanup_session(self, session_id: str) -> Dict[str, Any]:
    """
    Securely cleanup session and remove all stored keys
    """
    try:
        result = {
            "success": False,
            "keys_removed": 0,
            "session_existed": False
        }

        if session_id in self._active_buyer_keys:
            session_data = self._active_buyer_keys[session_id]
            keys_count = len(session_data["keys"])

            # Cancel expiration task if it exists
            if session_id in self._key_expiration_tasks:
                task = self._key_expiration_tasks[session_id]
                if not task.done():
                    task.cancel()
                del self._key_expiration_tasks[session_id]

            # Securely wipe keys from memory
            for provider in session_data["keys"]:
                session_data["keys"][provider] = "WIPED"

            # Remove session
            del self._active_buyer_keys[session_id]

            result.update({
                "success": True,
                "keys_removed": keys_count,
                "session_existed": True
            })

            logger.info(f"🗑️ Session cleaned up successfully: {session_id}")

        return result

    except Exception as e:
        logger.error(f"Failed to cleanup session: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "keys_removed": 0,
            "session_existed": False
        }


async def validate_key_format(self, api_keys: Dict[str, str]) -> bool:
    """
    Enhanced format validation for API keys
    """
    try:
        validation_rules = {
            'openai': {
                'prefix': 'sk-',
                'min_length': 20,
                'max_length': 100
            },
            'anthropic': {
                'prefix': 'sk-ant-',
                'min_length': 20,
                'max_length': 100
            },
            'google': {
                'prefix': 'AIza',
                'min_length': 20,
                'max_length': 100
            }
        }

        for provider, key in api_keys.items():
            if provider not in validation_rules:
                logger.warning(f"Unknown provider: {provider}")
                continue

            rules = validation_rules[provider]

            # Check prefix
            if not key.startswith(rules['prefix']):
                logger.warning(
                    f"Invalid prefix for {provider}: expected '{rules['prefix']}'")
                return False

            # Check length
            if len(key) < rules['min_length'] or len(key) > rules['max_length']:
                logger.warning(
                    f"Invalid length for {provider}: {len(key)} (expected {rules['min_length']}-{rules['max_length']})")
                return False

            # Check for obvious test/placeholder keys
            placeholder_patterns = ['test', 'demo',
                                    'placeholder', 'example', 'fake']
            key_lower = key.lower()
            if any(pattern in key_lower for pattern in placeholder_patterns):
                logger.warning(f"Placeholder key detected for {provider}")
                return False

        return True

    except Exception as e:
        logger.error(f"Key format validation failed: {str(e)}")
        return False


async def _schedule_key_expiration(self, session_id: str):
    """
    Schedule automatic key expiration and cleanup
    """
    try:
        async def expire_keys():
            await asyncio.sleep(self.key_lifetime_minutes * 60)
            if session_id in self._active_buyer_keys:
                logger.info(f"⏰ Auto-expiring keys for session: {session_id}")
                await self.cleanup_session(session_id)

        # Create and store the expiration task
        task = asyncio.create_task(expire_keys())
        self._key_expiration_tasks[session_id] = task

        logger.info(
            f"⏰ Scheduled key expiration for session: {session_id} ({self.key_lifetime_minutes} minutes)")

    except Exception as e:
        logger.error(f"Failed to schedule key expiration: {str(e)}")


def _encrypt_key(self, key: str) -> str:
    """
    Simulate key encryption (in production, use proper AES-256 encryption)
    """
    # For demo purposes, we'll use base64 encoding with a salt
    # In production, use proper encryption like AES-256
    import base64

    salt = secrets.token_bytes(16)
    key_bytes = key.encode('utf-8')

    # Simple XOR with salt for demo (NOT secure for production)
    encrypted_bytes = bytes(a ^ b for a, b in zip(
        key_bytes, salt * (len(key_bytes) // len(salt) + 1)))

    # Combine salt and encrypted data
    combined = salt + encrypted_bytes
    encoded = base64.b64encode(combined).decode('utf-8')

    return encoded


def _decrypt_key(self, encrypted_key: str) -> str:
    """
    Simulate key decryption (in production, use proper AES-256 decryption)
    """
    import base64

    try:
        # Decode from base64
        combined = base64.b64decode(encrypted_key.encode('utf-8'))

        # Extract salt and encrypted data
        salt = combined[:16]
        encrypted_bytes = combined[16:]

        # Simple XOR with salt for demo (NOT secure for production)
        decrypted_bytes = bytes(a ^ b for a, b in zip(
            encrypted_bytes, salt * (len(encrypted_bytes) // len(salt) + 1)))

        return decrypted_bytes.decode('utf-8')

    except Exception as e:
        logger.error(f"Failed to decrypt key: {str(e)}")
        return ""


def _generate_security_hash(self, session_id: str, api_keys: Dict[str, str]) -> str:
    """
    Generate security hash for integrity verification
    """
    try:
        # Create a hash of session_id + key fingerprints for integrity checking
        hash_input = session_id

        for provider, key in sorted(api_keys.items()):
            # Use first 8 and last 4 characters for fingerprint
            fingerprint = key[:8] + "..." + key[-4:] if len(key) > 12 else key
            hash_input += f"{provider}:{fingerprint}"

        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    except Exception as e:
        logger.error(f"Failed to generate security hash: {str(e)}")
        return ""


async def get_security_audit_report(self) -> Dict[str, Any]:
    """
    Generate security audit report for current sessions
    """
    try:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_sessions": len(self._active_buyer_keys),
            "security_status": "operational",
            "sessions": []
        }

        for session_id, session_data in self._active_buyer_keys.items():
            metadata = session_data["metadata"]

            session_report = {
                "session_id": session_id,
                "audit_id": metadata["audit_id"],
                "created_at": metadata["created_at"].isoformat(),
                "expires_at": metadata["expires_at"].isoformat(),
                "last_accessed": metadata["last_accessed"].isoformat(),
                "access_count": metadata["access_count"],
                "key_count": metadata["key_count"],
                "providers": metadata["providers"],
                "is_expired": datetime.now(timezone.utc) > metadata["expires_at"],
                "security_hash_valid": bool(session_data.get("security_hash"))
            }

            report["sessions"].append(session_report)

        return report

    except Exception as e:
        logger.error(f"Failed to generate security audit report: {str(e)}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_sessions": 0,
            "security_status": "error",
            "error": str(e),
            "sessions": []
        }


async def cleanup_expired_sessions(self) -> Dict[str, Any]:
    """
    Cleanup all expired sessions
    """
    try:
        expired_sessions = []
        current_time = datetime.now(timezone.utc)

        for session_id, session_data in list(self._active_buyer_keys.items()):
            if current_time > session_data["metadata"]["expires_at"]:
                expired_sessions.append(session_id)
                await self.cleanup_session(session_id)

        logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")

        return {
            "success": True,
            "expired_sessions_cleaned": len(expired_sessions),
            "session_ids": expired_sessions
        }

    except Exception as e:
        logger.error(f"Failed to cleanup expired sessions: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "expired_sessions_cleaned": 0
        }


async def extend_session_lifetime(self, session_id: str, additional_minutes: int = 30) -> bool:
    """
    Extend the lifetime of a session (for legitimate extended evaluations)
    """
    try:
        if session_id not in self._active_buyer_keys:
            return False

        session_data = self._active_buyer_keys[session_id]

        # Extend expiration time
        current_expires = session_data["metadata"]["expires_at"]
        new_expires = current_expires + timedelta(minutes=additional_minutes)
        session_data["metadata"]["expires_at"] = new_expires

        # Cancel old expiration task and create new one
        if session_id in self._key_expiration_tasks:
            task = self._key_expiration_tasks[session_id]
            if not task.done():
                task.cancel()

        # Schedule new expiration
        await self._schedule_key_expiration(session_id)

        logger.info(
            f"⏰ Extended session lifetime: {session_id} (+{additional_minutes} minutes)")

        return True

    except Exception as e:
        logger.error(f"Failed to extend session lifetime: {str(e)}")
        return False


# Enhanced initialization method (add to __init__)
def __init__(self):
    # Existing initialization
    self._active_buyer_keys: Dict[str, Dict[str, Any]] = {}
    self._key_expiration_tasks: Dict[str, asyncio.Task] = {}
    self.key_lifetime_minutes = 60

    # Enhanced security features
    self._security_events = []
    self._access_patterns = {}
    self._failed_attempts = {}

    logger.info(
        "🔐 Enhanced APIKeyManager initialized with enterprise security features")


async def log_security_event(self, event_type: str, session_id: str, details: Dict[str, Any]):
    """
    Log security events for audit trail
    """
    try:
        security_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "session_id": session_id,
            "details": details,
            "event_id": str(uuid.uuid4())
        }

        # Store in memory (in production, send to SIEM/audit system)
        self._security_events.append(security_event)

        # Keep only last 1000 events to prevent memory issues
        if len(self._security_events) > 1000:
            self._security_events = self._security_events[-1000:]

        logger.info(
            f"🔒 Security event logged: {event_type} for session {session_id}")

    except Exception as e:
        logger.error(f"Failed to log security event: {str(e)}")


# Usage example for integration
"""
# Add this to your demo_backend.py initialization:

async def initialize_enhanced_api_key_manager():
    '''Initialize the enhanced API key manager with all security features'''

    # Create enhanced API key manager
    api_key_manager = APIKeyManager()

    # Add periodic cleanup task
    async def periodic_cleanup():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            await api_key_manager.cleanup_expired_sessions()

    # Start cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    return api_key_manager, cleanup_task

# In your lifespan function:
async def lifespan(app: FastAPI):
    # ... existing code ...

    # Initialize enhanced API key manager
    api_key_manager, cleanup_task = await initialize_enhanced_api_key_manager()
    app.state.api_key_manager = api_key_manager
    app.state.cleanup_task = cleanup_task

    yield

    # Cleanup on shutdown
    cleanup_task.cancel()
    await api_key_manager.cleanup_expired_sessions()
"""
