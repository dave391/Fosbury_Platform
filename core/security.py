from cryptography.fernet import Fernet
from passlib.context import CryptContext
from typing import Optional
import time

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cipher = Fernet(settings.SECURITY_KEY)

SESSION_DURATION_SECONDS = settings.SESSION_DURATION_SECONDS


def encrypt_data(data: str) -> str:
    """Prende una stringa in chiaro e restituisce una stringa cifrata."""
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Prende una stringa cifrata e restituisce la stringa originale."""
    return cipher.decrypt(encrypted_data.encode()).decode()


def create_session_token(user_id: int) -> str:
    """
    Crea un token cifrato contenente user_id e timestamp di creazione.
    Formato: "user_id:timestamp"
    """
    timestamp = int(time.time())
    data = f"{user_id}:{timestamp}"
    return encrypt_data(data)


def decode_session_token(token: str) -> Optional[int]:
    """
    Decifra il token e restituisce l'user_id SOLO se il token è valido
    e non scaduto (15 minuti).
    """
    if not token:
        return None
    try:
        decrypted = decrypt_data(token)
        parts = decrypted.split(":")
        
        # Backward compatibility for old tokens (just user_id)
        if len(parts) == 1:
            return None  # Force logout for old tokens to be safe
            
        user_id_str, timestamp_str = parts
        user_id = int(user_id_str)
        timestamp = int(timestamp_str)
        
        # Check expiration
        if time.time() - timestamp > SESSION_DURATION_SECONDS:
            return None
            
        return user_id
    except Exception:
        return None


def get_password_hash(password: str) -> str:
    """Trasforma una password in chiaro in un hash sicuro."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Controlla se la password inserita corrisponde all'hash nel DB."""
    return pwd_context.verify(plain_password, hashed_password)
