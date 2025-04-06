"""Key management utilities for the CLI."""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from typing import Optional, Tuple

class KeyPair:
    """Represents a public/private key pair."""
    
    def __init__(self, public_key: str, private_key: str):
        self.public_key = public_key
        self.private_key = private_key
    
    @classmethod
    def generate(cls, key_size: int = 2048) -> 'KeyPair':
        """Generate a new RSA keypair.
        
        Args:
            key_size: Size of the key in bits (default: 2048)
            
        Returns:
            KeyPair: The generated key pair
        """
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Convert to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        return cls(public_pem, private_pem)
    
    def is_valid(self) -> bool:
        """Check if both keys are valid PEM format and match each other.
        
        Returns:
            bool: True if both keys are valid and match
        """
        try:
            # Try to load private key
            private_key = serialization.load_pem_private_key(
                self.private_key.encode(),
                password=None
            )
            
            # Try to load public key
            public_key = serialization.load_pem_public_key(
                self.public_key.encode()
            )
            
            # Verify the public key matches the private key
            return public_key.public_numbers() == private_key.public_key().public_numbers()
        except Exception:
            return False

def load_or_generate_keys(env_vars: dict) -> KeyPair:
    """Load keys from environment variables or generate new ones if invalid.
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        KeyPair: The loaded or generated key pair
    """
    # Try to load existing keys
    if 'AUTHED_PRIVATE_KEY' in env_vars and 'AUTHED_PUBLIC_KEY' in env_vars:
        keypair = KeyPair(
            env_vars['AUTHED_PUBLIC_KEY'].strip('"\' '),
            env_vars['AUTHED_PRIVATE_KEY'].strip('"\' ')
        )
        if keypair.is_valid():
            return keypair
    
    # Generate new keys if not found or invalid
    return KeyPair.generate()

def validate_public_key(key: str) -> bool:
    """Validate if a string is a valid public key.
    
    Args:
        key: The public key string to validate
        
    Returns:
        bool: True if the key is valid
    """
    try:
        # Basic format check
        if not key.startswith('-----BEGIN PUBLIC KEY-----') or not key.endswith('-----END PUBLIC KEY-----'):
            return False
            
        # Try to load the key
        serialization.load_pem_public_key(key.encode())
        return True
    except Exception:
        return False 