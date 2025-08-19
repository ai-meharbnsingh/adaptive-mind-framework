# 03_Demo_Interface/api_key_manager.py

"""
API Key Manager for Adaptive Mind Framework Demo
SESSION 7 - Enhanced Demo Backend Integration (further refined in Session 8)

This module handles the secure (in-memory) validation and temporary storage
of buyer API keys during the demonstration, emphasizing enterprise-grade security
by not persisting sensitive credentials.

Created: August 16, 2025 (Initial)
Updated: August 18, 2025 (Session 8 Refinement)
Author: Adaptive Mind Framework Team
Version: 1.1
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone  # For simulated expiration

# Standardized path setup (relative to current file)
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
FRAMEWORK_CORE_PATH = PROJECT_ROOT / "01_Framework_Core" / "antifragile_framework"
DATABASE_LAYER_PATH = PROJECT_ROOT / "05_Database_Layer"
TELEMETRY_PATH = PROJECT_ROOT / "01_Framework_Core" / "telemetry"

import sys

sys.path.insert(0, str(FRAMEWORK_CORE_PATH))
sys.path.insert(0, str(DATABASE_LAYER_PATH))
sys.path.insert(0, str(TELEMETRY_PATH))
sys.path.insert(0, str(CURRENT_DIR))  # For sibling modules within 03_Demo_Interface

# Enterprise logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Manages API keys for the demo. For a sales demo, this emphasizes
    in-memory handling for security and ephemeral usage.
    """

    def __init__(self):
        # In a real system, this would be a secure, encrypted store.
        # For the demo, it explicitly highlights ephemeral, in-memory use.
        self._active_buyer_keys: Dict[str, Dict[str, Any]] = {}
        self._key_expiration_tasks: Dict[str, asyncio.Task] = {}
        self.key_lifetime_minutes = 60  # Keys expire after 60 minutes for security demo
        self._security_events = []
        self._access_patterns = {}
        self._failed_attempts = {}
        logger.info("APIKeyManager initialized: Buyer API keys will be handled in-memory only for demo duration.")




    async def validate_key_format(self, api_keys: Dict[str, str]) -> bool:
        """
        Validates the format of provided API keys.
        This is a demo-level validation, not full cryptographic validation.
        """
        logger.info("Validating API key formats...")
        is_valid = True
        for provider, key in api_keys.items():
            if not key:  # Allow empty keys for providers not being used
                continue

            # Simplified regex for common API key formats
            if provider == "openai":
                if not re.match(r"sk-[a-zA-Z0-9]{32,}", key):  # Basic check
                    logger.warning(f"Invalid OpenAI API key format for demo: {key[:8]}...")
                    is_valid = False
            elif provider == "anthropic":
                if not re.match(r"sk-ant-api03-[a-zA-Z0-9_]{32,}", key):  # Basic check
                    logger.warning(f"Invalid Anthropic API key format for demo: {key[:8]}...")
                    is_valid = False
            elif provider == "google":  # Assuming Gemini key
                if not re.match(r"AIza[a-zA-Z0-9_-]{35}", key):  # Basic check for Google AI keys
                    logger.warning(f"Invalid Google Gemini API key format for demo: {key[:8]}...")
                    is_valid = False
            else:
                logger.warning(f"Unsupported provider for key validation: {provider}")
                is_valid = False  # Treat as invalid if provider is unknown

        if is_valid:
            logger.info("API key formats validated successfully (demo level).")
        else:
            logger.error("One or more API key formats are invalid.")
        return is_valid

    async def secure_store_buyer_keys(self, session_id: str, api_keys: Dict[str, str]) -> Dict[str, str]:
        """
        Securely "stores" buyer API keys in memory for the duration of the demo session.
        Emphasizes the ephemeral nature of key storage.
        """
        cleaned_keys = {p: k.strip() for p, k in api_keys.items() if k and k.strip()}

        if not cleaned_keys:
            logger.warning(f"No valid API keys provided for session {session_id}.")
            return {}

        self._active_buyer_keys[session_id] = {
            "keys": cleaned_keys,
            "timestamp": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=self.key_lifetime_minutes),
            "client_ip": "DEMO_IP"  # Placeholder
        }

        # Schedule cleanup task for these keys
        if session_id in self._key_expiration_tasks and not self._key_expiration_tasks[session_id].done():
            self._key_expiration_tasks[session_id].cancel()  # Cancel previous task if exists

        self._key_expiration_tasks[session_id] = asyncio.create_task(
            self._schedule_key_cleanup(session_id, self.key_lifetime_minutes)
        )

        logger.info(f"Buyer API keys for session {session_id[:8]}... securely loaded into memory. "
                    f"Will expire in {self.key_lifetime_minutes} minutes.")
        return cleaned_keys

    def get_buyer_keys(self, session_id: str) -> Optional[Dict[str, str]]:
        """
        Retrieves buyer API keys for a given session from memory, if active.
        """
        key_data = self._active_buyer_keys.get(session_id)
        if key_data and key_data["expires_at"] > datetime.now(timezone.utc):
            return key_data["keys"]
        else:
            if key_data:  # If keys expired
                logger.info(f"Buyer API keys for session {session_id[:8]}... have expired and been removed.")
                self.remove_buyer_keys(session_id)
            return None

    def remove_buyer_keys(self, session_id: str):
        """
        Removes buyer API keys for a given session from memory.
        """
        if session_id in self._active_buyer_keys:
            del self._active_buyer_keys[session_id]
            logger.info(f"Buyer API keys for session {session_id[:8]}... explicitly removed from memory.")
            if session_id in self._key_expiration_tasks:
                self._key_expiration_tasks[session_id].cancel()
                del self._key_expiration_tasks[session_id]

    async def _schedule_key_cleanup(self, session_id: str, delay_minutes: int):
        """
        Internal task to remove keys after a specified delay.
        """
        try:
            await asyncio.sleep(delay_minutes * 60)
            if session_id in self._active_buyer_keys:
                logger.warning(f"Buyer API keys for session {session_id[:8]}... automatically expired and removed.")
                self.remove_buyer_keys(session_id)
        except asyncio.CancelledError:
            logger.info(f"Key cleanup task for session {session_id[:8]}... cancelled.")
        except Exception as e:
            logger.error(f"Error during scheduled key cleanup for session {session_id[:8]}...: {e}", exc_info=True)

    async def shutdown(self):
        """
        Gracefully shuts down the APIKeyManager, clearing all in-memory keys
        and cancelling any pending cleanup tasks.
        """
        logger.info("Shutting down APIKeyManager. Clearing all in-memory buyer API keys.")
        for task in self._key_expiration_tasks.values():
            if not task.done():
                task.cancel()
        await asyncio.gather(*[task for task in self._key_expiration_tasks.values() if not task.done()],
                             return_exceptions=True)
        self._active_buyer_keys.clear()
        self._key_expiration_tasks.clear()
        logger.info("APIKeyManager shutdown complete. All keys cleared.")

    async def store_buyer_keys_securely(self, session_id: str, api_keys: Dict[str, str]) -> str:
        """NEW METHOD: Securely store buyer API keys"""
        # Copy full implementation from enhanced_api_key_manager_methods.py

    async def get_stored_keys(self, session_id: str) -> Optional[Dict[str, str]]:
        """NEW METHOD: Retrieve stored keys"""
        # Copy full implementation

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """NEW METHOD: Get session metadata"""
        # Copy full implementation

    async def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """NEW METHOD: Secure session cleanup"""
        # Copy full implementation

    # ADD all other new methods from the enhanced file...

    def _encrypt_key(self, key: str) -> str:
        """NEW PRIVATE METHOD: Key encryption"""
        # Copy full implementation

    def _decrypt_key(self, encrypted_key: str) -> str:
        """NEW PRIVATE METHOD: Key decryption"""
        # Copy full implementation

if __name__ == "__main__":
    import uuid
    import json  # For print formatting


    async def main():
        print("Starting APIKeyManager demo...")
        manager = APIKeyManager()

        session_id_1 = str(uuid.uuid4())
        session_id_2 = str(uuid.uuid4())

        # Test valid keys
        valid_keys = {
            "openai": "sk-testabcdef1234567890abcdef1234567890abcdef",
            "anthropic": "sk-ant-api03-abcdefghijklmno1234567890abcdefghijklmno",
            "google": "AIzaSyB-abcdefghijklmnopqrstuvwxyz0123456789"
        }
        print("\n--- Validating and Storing Session 1 Keys ---")
        is_valid = await manager.validate_key_format(valid_keys)
        if is_valid:
            await manager.secure_store_buyer_keys(session_id_1, valid_keys)
            retrieved_keys = manager.get_buyer_keys(session_id_1)
            print(f"Retrieved keys for session {session_id_1[:8]}...: {json.dumps(retrieved_keys, indent=2)}")
        else:
            print("Key validation failed for session 1.")

        # Test invalid keys
        invalid_keys = {
            "openai": "invalid-key",
            "anthropic": "sk-wrong-format",
            "unknown_provider": "some_key"
        }
        print("\n--- Validating and Storing Session 2 (Invalid) Keys ---")
        is_invalid = await manager.validate_key_format(invalid_keys)
        if not is_invalid:
            print("Key validation correctly failed for session 2.")
            await manager.secure_store_buyer_keys(session_id_2, invalid_keys)  # Should only store valid ones, if any
            retrieved_invalid_keys = manager.get_buyer_keys(session_id_2)
            print(
                f"Retrieved keys for session {session_id_2[:8]}... (should be empty or very few): {json.dumps(retrieved_invalid_keys, indent=2)}")

        # Test key removal
        print("\n--- Removing Session 1 Keys ---")
        manager.remove_buyer_keys(session_id_1)
        retrieved_after_remove = manager.get_buyer_keys(session_id_1)
        print(
            f"Retrieved keys for session {session_id_1[:8]}... after removal: {retrieved_after_remove}")  # Should be None

        # Simulate expiration (temporarily set short lifetime for demo)
        print("\n--- Simulating Key Expiration (Session 2) ---")
        manager.key_lifetime_minutes = 0.05  # 3 seconds for demo
        await manager.secure_store_buyer_keys(session_id_2, {"openai": "sk-another-valid-key-to-expire"})
        print(f"Session 2 keys stored, will expire in {manager.key_lifetime_minutes} minutes.")
        await asyncio.sleep(manager.key_lifetime_minutes * 60 + 1)  # Wait a bit more than expiration
        expired_keys = manager.get_buyer_keys(session_id_2)
        print(f"Retrieved keys for session {session_id_2[:8]}... after expiration: {expired_keys}")  # Should be None

        print("\n--- Shutting down APIKeyManager ---")
        await manager.shutdown()
        print("APIKeyManager demo completed.")


    asyncio.run(main())