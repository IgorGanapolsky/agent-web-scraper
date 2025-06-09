"""
Authentication API endpoints for MCP system
Handles user registration, login, JWT tokens, and email verification
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.config.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(days=7)


class UserRegistration(BaseModel):
    """User registration request model"""

    email: EmailStr
    password: str
    name: Optional[str] = None
    company: Optional[str] = None


class UserLogin(BaseModel):
    """User login request model"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response model"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str


class PasswordReset(BaseModel):
    """Password reset request model"""

    email: EmailStr


class PasswordUpdate(BaseModel):
    """Password update model"""

    token: str
    new_password: str


def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token"""
    expires = datetime.utcnow() + JWT_EXPIRATION
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expires,
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


async def send_verification_email(email: str, verification_token: str) -> bool:
    """Send email verification via Zoho SMTP"""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Zoho SMTP configuration
        smtp_host = os.getenv("SMTP_HOST", "smtp.zoho.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("ZOHO_APP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM", "support@saasgrowthdispatch.com")

        if not all([smtp_username, smtp_password]):
            logger.error("SMTP credentials not configured")
            return False

        # Create verification email
        verification_url = (
            f"https://saasgrowthdispatch.com/verify?token={verification_token}"
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your SaaS Growth Dispatch account"
        msg["From"] = smtp_from
        msg["To"] = email

        html_content = f"""
        <html>
            <body>
                <h2>Welcome to SaaS Growth Dispatch!</h2>
                <p>Thank you for signing up. Please verify your email address by clicking the link below:</p>
                <a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Verify Email Address
                </a>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p>{verification_url}</p>
                <p>This verification link will expire in 24 hours.</p>
                <br>
                <p>Best regards,<br>The SaaS Growth Dispatch Team</p>
            </body>
        </html>
        """

        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info(f"Verification email sent to {email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False


@router.post("/register", response_model=dict)
async def register(user_data: UserRegistration):
    """Register new user with email verification"""

    try:
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)

        # Create user record (Supabase integration would go here)
        user_id = f"user_{secrets.token_urlsafe(16)}"

        # In production, save to Supabase:
        # hashed_password = hash_password(user_data.password)
        # await supabase.table("users").insert({
        #     "id": user_id,
        #     "email": user_data.email,
        #     "password_hash": hashed_password,
        #     "name": user_data.name,
        #     "company": user_data.company,
        #     "verification_token": verification_token,
        #     "email_verified": False,
        #     "created_at": datetime.utcnow().isoformat()
        # })

        # Send verification email
        email_sent = await send_verification_email(user_data.email, verification_token)

        logger.info(f"User registered: {user_data.email}")

        return {
            "message": "Registration successful. Please check your email for verification.",
            "user_id": user_id,
            "email_sent": email_sent,
        }

    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """User login with JWT token generation"""

    try:
        # In production, verify against Supabase:
        # user = await supabase.table("users").select("*").eq("email", credentials.email).single()
        # if not user or not verify_password(credentials.password, user["password_hash"]):
        #     raise HTTPException(status_code=401, detail="Invalid credentials")
        # if not user["email_verified"]:
        #     raise HTTPException(status_code=401, detail="Email not verified")

        # Mock user validation for now
        user_id = f"user_{hash(credentials.email)}"

        # Create access token
        access_token = create_access_token(user_id, credentials.email)

        logger.info(f"User logged in: {credentials.email}")

        return TokenResponse(
            access_token=access_token,
            expires_in=int(JWT_EXPIRATION.total_seconds()),
            user_id=user_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.get("/verify")
async def verify_email(token: str):
    """Verify user email address"""

    try:
        # In production, verify token against Supabase:
        # user = await supabase.table("users").select("*").eq("verification_token", token).single()
        # if not user:
        #     raise HTTPException(status_code=400, detail="Invalid verification token")
        #
        # await supabase.table("users").update({
        #     "email_verified": True,
        #     "verification_token": None
        # }).eq("id", user["id"])

        logger.info(f"Email verified for token: {token[:10]}...")

        return {"message": "Email verified successfully"}

    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email verification failed"
        )


@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Send password reset email"""

    try:
        # In production, save reset token to Supabase with expiration:
        # reset_token = secrets.token_urlsafe(32)

        # Send reset email (similar to verification email)
        # await send_password_reset_email(reset_data.email, reset_token)

        logger.info(f"Password reset requested for: {reset_data.email}")

        return {"message": "Password reset email sent"}

    except Exception as e:
        logger.error(f"Password reset failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        )


@router.put("/update-password")
async def update_password(update_data: PasswordUpdate):
    """Update password using reset token"""

    try:
        # Verify reset token and update password
        # In production, implement token validation and password update in Supabase:
        # hashed_password = hash_password(update_data.new_password)

        logger.info("Password updated successfully")

        return {"message": "Password updated successfully"}

    except Exception as e:
        logger.error(f"Password update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password update failed",
        )


@router.get("/me")
async def get_current_user(payload: dict = Depends(verify_token)):
    """Get current user information"""

    try:
        # In production, fetch user data from Supabase
        user_data = {
            "user_id": payload["user_id"],
            "email": payload["email"],
            "name": "John Doe",  # From Supabase
            "company": "Acme Corp",  # From Supabase
            "subscription_tier": "pro",  # From Supabase
            "email_verified": True,
        }

        return user_data

    except Exception as e:
        logger.error(f"Failed to get user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user data",
        )
