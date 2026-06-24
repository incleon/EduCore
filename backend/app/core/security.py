"""
Security Module — JWT Authentication & Password Hashing
=========================================================

OOP Concepts Demonstrated:
--------------------------
1. STATIC METHODS: PasswordHasher methods don't need instance state
2. CLASS METHODS: JWTHandler.create_token() is a class method
3. ENCAPSULATION: Internal implementation hidden behind clean API
4. ABSTRACTION: Callers don't need to know bcrypt/jose internals

Why separate security module?
- Single Responsibility Principle (SRP)
- All security logic in one place
- Easy to swap implementations (e.g., bcrypt → argon2)
- Easy to test in isolation

Design Decisions:
- PasswordHasher uses static methods because it has no state
- JWTHandler uses class methods because it references class-level config
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PasswordHasher:
    """
    Handles password hashing and verification using bcrypt.

    OOP Concept: STATIC METHODS
    ────────────────────────────
    All methods are @staticmethod because:
    - They don't access instance state (self)
    - They don't access class state (cls)
    - They are pure utility functions grouped logically in a class
    - The class acts as a namespace, not a blueprint for objects

    Why bcrypt?
    - Adaptive: cost factor can be increased as hardware improves
    - Salted: each hash includes a unique random salt
    - Industry standard for password storage
    """

    # Class-level configuration — shared across all usages
    _context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """
        Hash a plain-text password using bcrypt.

        STATIC METHOD: No 'self' or 'cls' parameter.
        Called as: PasswordHasher.hash_password("mypassword")

        Args:
            plain_password: The plain-text password to hash

        Returns:
            The bcrypt hash string (includes salt + hash)
        """
        return PasswordHasher._context.hash(plain_password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against a bcrypt hash.

        STATIC METHOD: Stateless verification — same input always gives same output.

        Args:
            plain_password: The plain-text password to verify
            hashed_password: The stored bcrypt hash

        Returns:
            True if password matches, False otherwise
        """
        try:
            return PasswordHasher._context.verify(plain_password, hashed_password)
        except Exception:
            logger.warning("Password verification failed — possibly corrupted hash")
            return False


class JWTHandler:
    """
    Handles JWT token creation and validation.

    OOP Concept: CLASS METHODS
    ──────────────────────────
    Methods use @classmethod because:
    - They reference class-level attributes (_secret_key, _algorithm)
    - They don't need an instance but do need class context
    - They can be overridden by subclasses (e.g., for testing)

    OOP Concept: ENCAPSULATION
    ──────────────────────────
    - _secret_key and _algorithm are PROTECTED (single underscore)
    - External code uses create_token/decode_token without knowing internals
    - Implementation details (jose library, payload structure) are hidden

    JWT Flow:
    1. User logs in with email/password
    2. Server creates JWT with user_id + roles + permissions in payload
    3. Token is stored in HTTP-only cookie
    4. Each request extracts and validates the token
    5. Token expiry forces re-authentication
    """

    # Protected class attributes — accessible but conventionally private
    _secret_key: str = settings.SECRET_KEY
    _algorithm: str = settings.ALGORITHM
    _expire_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    @classmethod
    def create_access_token(
        cls,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a JWT access token.

        CLASS METHOD: Receives 'cls' as first argument.
        Called as: JWTHandler.create_access_token({"sub": "user@example.com"})

        Why class method?
        - Accesses cls._secret_key and cls._algorithm
        - Can be overridden in a TestJWTHandler subclass
        - Acts as a factory for token strings

        Args:
            data: Payload data (user_id, roles, permissions)
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=cls._expire_minutes
            )

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
        })

        encoded_jwt = jwt.encode(
            to_encode,
            cls._secret_key,
            algorithm=cls._algorithm,
        )

        logger.debug(f"JWT token created for subject: {data.get('sub', 'unknown')}")
        return encoded_jwt

    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token.

        CLASS METHOD: Uses class-level secret key and algorithm.

        Raises:
            UnauthorizedException: If token is invalid, expired, or malformed

        Returns:
            Decoded payload dictionary
        """
        try:
            payload = jwt.decode(
                token,
                cls._secret_key,
                algorithms=[cls._algorithm],
            )
            return payload

        except ExpiredSignatureError:
            logger.info("JWT token expired")
            raise UnauthorizedException(
                detail="Token has expired. Please log in again.",
                error_code="TOKEN_EXPIRED",
            )
        except JWTError as e:
            logger.warning(f"JWT decode error: {str(e)}")
            raise UnauthorizedException(
                detail="Invalid authentication token",
                error_code="INVALID_TOKEN",
            )

    @classmethod
    def create_refresh_token(
        cls,
        data: Dict[str, Any],
    ) -> str:
        """
        Create a refresh token with longer expiration.

        Demonstrates METHOD OVERLOADING (Pythonic style):
        - create_access_token() → short-lived
        - create_refresh_token() → long-lived
        Both create tokens but with different configurations.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days

        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
        })

        return jwt.encode(
            to_encode,
            cls._secret_key,
            algorithm=cls._algorithm,
        )


class CaptchaHandler:
    """Simple server-side captcha generation and verification."""

    _secret_key: str = settings.SECRET_KEY
    _algorithm: str = settings.ALGORITHM
    _expire_minutes: int = 5

    @classmethod
    def create_challenge(cls):
        import random
        import string

        # Generate an alphanumeric mixed-case token (6 chars)
        alphabet = string.ascii_letters + string.digits
        token_text = ''.join(random.choice(alphabet) for _ in range(6))

        payload = {
            "answer": token_text,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=cls._expire_minutes),
        }

        token = jwt.encode(payload, cls._secret_key, algorithm=cls._algorithm)
        # Return token_text (rendered as captcha) and signed token
        return token_text, token

    @classmethod
    def verify(cls, token: str, submitted_answer: str) -> bool:
        try:
            payload = jwt.decode(token, cls._secret_key, algorithms=[cls._algorithm])
            return str(submitted_answer or "").strip() == str(payload.get("answer", "")).strip()
        except Exception:
            return False
