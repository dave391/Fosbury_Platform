from cryptography.fernet import Fernet
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cipher = Fernet(settings.SECURITY_KEY)


def encrypt_data(data: str) -> str:
    """Prende una stringa in chiaro e restituisce una stringa cifrata."""
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Prende una stringa cifrata e restituisce la stringa originale."""
    return cipher.decrypt(encrypted_data.encode()).decode()


def get_password_hash(password: str) -> str:
    """Trasforma una password in chiaro in un hash sicuro."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Controlla se la password inserita corrisponde all'hash nel DB."""
    return pwd_context.verify(plain_password, hashed_password)
