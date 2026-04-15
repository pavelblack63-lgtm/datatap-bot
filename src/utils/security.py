import hmac
import hashlib
import secrets
import string
from src.config import settings


def generate_tap_hash(user_id: int, timestamp: int, secret: str | None = None) -> str:
    secret_key = secret or settings.SECRET_KEY
    message = f"{user_id}:{timestamp}"
    return hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()


def verify_tap_hash(
    user_id: int, timestamp: int, client_hash: str, secret: str | None = None
) -> bool:
    expected = generate_tap_hash(user_id, timestamp, secret)
    return hmac.compare_digest(expected, client_hash)


def generate_referral_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "").replace("I", "").replace("1", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))
