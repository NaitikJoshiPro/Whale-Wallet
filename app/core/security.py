"""
Security Utilities

Core security functions for encryption, hashing, and secrets management.
"""

import hashlib
import hmac
import secrets
from base64 import b64decode, b64encode
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_duress_pin_hash(pin: str, salt: bytes | None = None) -> tuple[str, str]:
    """
    Hash a duress PIN with PBKDF2.
    
    Returns tuple of (hash, salt) for storage.
    Never store the plaintext PIN.
    """
    if salt is None:
        salt = secrets.token_bytes(32)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000  # OWASP recommended minimum
    )
    
    key = kdf.derive(pin.encode())
    
    return b64encode(key).decode(), b64encode(salt).decode()


def verify_duress_pin(
    pin: str,
    stored_hash: str,
    stored_salt: str
) -> bool:
    """Verify a duress PIN against stored hash."""
    salt = b64decode(stored_salt)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000
    )
    
    try:
        computed_hash = b64encode(kdf.derive(pin.encode())).decode()
        return hmac.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False


class EncryptionService:
    """
    Encryption service for sensitive data at rest.
    
    Uses Fernet (AES-128-CBC) for symmetric encryption.
    Keys are derived from the master encryption key.
    """
    
    def __init__(self, master_key: str | None = None):
        """Initialize with master key from settings."""
        if master_key is None:
            settings = get_settings()
            master_key = settings.encryption_key.get_secret_value()
        
        # Derive a Fernet key from the master key
        self._key = self._derive_key(master_key.encode())
        self._fernet = Fernet(self._key)
    
    def _derive_key(self, master_key: bytes) -> bytes:
        """Derive a Fernet-compatible key from master key."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"whale-wallet-encryption-v1",  # Fixed salt is OK for key derivation
            iterations=100_000
        )
        derived = kdf.derive(master_key)
        return b64encode(derived)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        ciphertext = self._fernet.encrypt(plaintext.encode())
        return b64encode(ciphertext).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext and return plaintext."""
        encrypted = b64decode(ciphertext)
        plaintext = self._fernet.decrypt(encrypted)
        return plaintext.decode()
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary as JSON."""
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, ciphertext: str) -> dict:
        """Decrypt a dictionary from encrypted JSON."""
        import json
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str)


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time.
    
    Prevents timing attacks on sensitive comparisons.
    """
    return hmac.compare_digest(a.encode(), b.encode())


def generate_shard_id() -> str:
    """Generate a unique identifier for an MPC shard."""
    return f"shard-{secrets.token_hex(16)}"


def derive_address_from_pubkey(pubkey: bytes, chain: str) -> str:
    """
    Derive a blockchain address from a public key.
    
    This is a placeholder - actual implementation depends
    on the specific chain's address derivation.
    """
    if chain == "ethereum":
        # Keccak-256 hash, take last 20 bytes
        from hashlib import sha3_256
        hash_bytes = sha3_256(pubkey).digest()
        return "0x" + hash_bytes[-20:].hex()
    
    elif chain == "bitcoin":
        # SHA256 -> RIPEMD160 -> Base58Check
        import hashlib
        sha = hashlib.sha256(pubkey).digest()
        ripemd = hashlib.new('ripemd160', sha).digest()
        return ripemd.hex()  # Simplified - real impl needs Base58Check
    
    elif chain == "solana":
        # Ed25519 pubkey is the address
        return b64encode(pubkey[:32]).decode()
    
    else:
        raise ValueError(f"Unsupported chain: {chain}")
