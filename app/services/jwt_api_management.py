"""
JWT API Access Management with Rate Limiting
Enterprise-grade authentication and authorization with Supabase storage.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import asyncpg
import bcrypt
import jwt
import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from supabase import Client, create_client

from app.config.logging import get_logger

logger = get_logger(__name__)

# Initialize services
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))
security = HTTPBearer()

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


class APIKeyRequest(BaseModel):
    """API key creation request"""
    name: str = Field(..., description="API key name")
    permissions: list[str] = Field(..., description="Permission scopes")
    rate_limit: int = Field(default=1000, description="Requests per hour")
    expires_in_days: Optional[int] = Field(None, description="Expiration in days")


class TokenRequest(BaseModel):
    """JWT token request"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RateLimitConfig(BaseModel):
    """Rate limiting configuration"""
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000


class JWTAPIManager:
    """Enterprise JWT and API key management service"""

    def __init__(self):
        self.db_pool = None
        self.redis_client = None
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24

        # Permission levels
        self.permission_levels = {
            "viewer": ["read:basic"],
            "user": ["read:basic", "write:basic", "api:standard"],
            "admin": ["read:all", "write:all", "api:advanced", "manage:team"],
            "owner": ["read:all", "write:all", "api:unlimited", "manage:all", "billing:full"]
        }

        # Rate limits by subscription tier
        self.tier_limits = {
            "starter": RateLimitConfig(requests_per_minute=50, requests_per_hour=500, requests_per_day=5000),
            "professional": RateLimitConfig(requests_per_minute=200, requests_per_hour=2000, requests_per_day=20000),
            "enterprise": RateLimitConfig(requests_per_minute=1000, requests_per_hour=10000, requests_per_day=100000)
        }

    async def init_services(self):
        """Initialize database and Redis connections"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv("SUPABASE_DB_HOST"),
                database=os.getenv("SUPABASE_DB_NAME"),
                user=os.getenv("SUPABASE_DB_USER"),
                password=os.getenv("SUPABASE_DB_PASSWORD"),
                port=5432,
                min_size=5,
                max_size=20
            )

        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                os.getenv("REDIS_URL", "redis://localhost:6379"),
                decode_responses=True
            )

    async def create_api_key(self, user_id: str, request: APIKeyRequest) -> dict[str, Any]:
        """Create new API key with permissions and rate limits"""

        await self.init_services()

        try:
            # Generate secure API key
            import secrets
            api_key = f"ak_{secrets.token_urlsafe(32)}"
            api_key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

            # Calculate expiration
            expires_at = None
            if request.expires_in_days:
                expires_at = datetime.now() + timedelta(days=request.expires_in_days)

            # Store in database
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO api_keys (
                        user_id, name, key_hash, permissions, rate_limit,
                        expires_at, created_at, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, user_id, request.name, api_key_hash, json.dumps(request.permissions),
                    request.rate_limit, expires_at, datetime.now(), True)

            return {
                "success": True,
                "api_key": api_key,
                "name": request.name,
                "permissions": request.permissions,
                "rate_limit": request.rate_limit,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"API key creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def authenticate_jwt(self, token: str) -> dict[str, Any]:
        """Authenticate and validate JWT token"""

        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            # Check expiration
            if payload.get("exp", 0) < time.time():
                raise HTTPException(status_code=401, detail="Token expired")

            # Get user details
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")

            await self.init_services()

            async with self.db_pool.acquire() as conn:
                user_data = await conn.fetchrow("""
                    SELECT u.*, s.plan_id
                    FROM users u
                    LEFT JOIN subscriptions s ON u.stripe_customer_id = s.stripe_customer_id
                    WHERE u.id = $1 AND u.is_active = true
                """, user_id)

                if not user_data:
                    raise HTTPException(status_code=401, detail="User not found")

            return {
                "user_id": user_id,
                "email": user_data["email"],
                "role": user_data["role"],
                "plan_id": user_data["plan_id"],
                "permissions": self.permission_levels.get(user_data["role"], [])
            }

        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"JWT authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    async def authenticate_api_key(self, api_key: str) -> dict[str, Any]:
        """Authenticate and validate API key"""

        if not api_key.startswith("ak_"):
            raise HTTPException(status_code=401, detail="Invalid API key format")

        await self.init_services()

        try:
            async with self.db_pool.acquire() as conn:
                api_keys = await conn.fetch("""
                    SELECT ak.*, u.email, u.role, s.plan_id
                    FROM api_keys ak
                    JOIN users u ON ak.user_id = u.id
                    LEFT JOIN subscriptions s ON u.stripe_customer_id = s.stripe_customer_id
                    WHERE ak.is_active = true
                    AND (ak.expires_at IS NULL OR ak.expires_at > NOW())
                """)

                for key_data in api_keys:
                    if bcrypt.checkpw(api_key.encode(), key_data["key_hash"].encode()):
                        # Update last used
                        await conn.execute("""
                            UPDATE api_keys SET last_used_at = NOW() WHERE id = $1
                        """, key_data["id"])

                        return {
                            "user_id": key_data["user_id"],
                            "email": key_data["email"],
                            "role": key_data["role"],
                            "plan_id": key_data["plan_id"],
                            "api_key_id": key_data["id"],
                            "permissions": json.loads(key_data["permissions"]),
                            "rate_limit": key_data["rate_limit"]
                        }

                raise HTTPException(status_code=401, detail="Invalid API key")

        except Exception as e:
            logger.error(f"API key authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")

    async def check_rate_limit(self, user_id: str, plan_id: str = "starter") -> bool:
        """Check rate limiting for user"""

        await self.init_services()

        try:
            limits = self.tier_limits.get(plan_id, self.tier_limits["starter"])
            current_time = int(time.time())

            # Check minute limit
            minute_key = f"rate_limit:{user_id}:minute:{current_time // 60}"
            minute_count = await self.redis_client.get(minute_key)

            if minute_count and int(minute_count) >= limits.requests_per_minute:
                return False

            # Check hour limit
            hour_key = f"rate_limit:{user_id}:hour:{current_time // 3600}"
            hour_count = await self.redis_client.get(hour_key)

            if hour_count and int(hour_count) >= limits.requests_per_hour:
                return False

            # Check day limit
            day_key = f"rate_limit:{user_id}:day:{current_time // 86400}"
            day_count = await self.redis_client.get(day_key)

            if day_count and int(day_count) >= limits.requests_per_day:
                return False

            # Increment counters
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)
            await pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error

    async def generate_jwt_token(self, user_id: str, email: str, role: str) -> str:
        """Generate JWT token for user"""

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "iat": int(time.time()),
            "exp": int(time.time()) + (self.jwt_expiration_hours * 3600)
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def login_user(self, request: TokenRequest) -> dict[str, Any]:
        """Authenticate user and generate JWT token"""

        await self.init_services()

        try:
            async with self.db_pool.acquire() as conn:
                user_data = await conn.fetchrow("""
                    SELECT * FROM users WHERE email = $1 AND is_active = true
                """, request.email)

                if not user_data:
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                # Verify password
                if not bcrypt.checkpw(request.password.encode(), user_data["password_hash"].encode()):
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                # Generate JWT token
                token = await self.generate_jwt_token(
                    str(user_data["id"]),
                    user_data["email"],
                    user_data["role"]
                )

                # Update last login
                await conn.execute("""
                    UPDATE users SET last_login_at = NOW() WHERE id = $1
                """, user_data["id"])

                return {
                    "success": True,
                    "access_token": token,
                    "token_type": "bearer",
                    "expires_in": self.jwt_expiration_hours * 3600,
                    "user": {
                        "id": str(user_data["id"]),
                        "email": user_data["email"],
                        "role": user_data["role"]
                    }
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User login failed: {e}")
            raise HTTPException(status_code=500, detail="Login failed")


# Global service instance
_jwt_manager = None


def get_jwt_manager() -> JWTAPIManager:
    """Get global JWT manager instance"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTAPIManager()
    return _jwt_manager


# Dependency for JWT authentication
async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    jwt_manager: JWTAPIManager = Depends(get_jwt_manager)
) -> dict[str, Any]:
    """Verify JWT token and return user info"""

    token = credentials.credentials
    user_info = await jwt_manager.authenticate_jwt(token)

    # Check rate limit
    rate_limit_ok = await jwt_manager.check_rate_limit(
        user_info["user_id"],
        user_info.get("plan_id", "starter")
    )

    if not rate_limit_ok:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return user_info


# Dependency for API key authentication
async def verify_api_key(
    request: Request,
    jwt_manager: JWTAPIManager = Depends(get_jwt_manager)
) -> dict[str, Any]:
    """Verify API key and return user info"""

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    user_info = await jwt_manager.authenticate_api_key(api_key)

    # Check rate limit
    rate_limit_ok = await jwt_manager.check_rate_limit(
        user_info["user_id"],
        user_info.get("plan_id", "starter")
    )

    if not rate_limit_ok:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    return user_info


# FastAPI endpoints
@router.post("/login")
async def login_endpoint(
    request: TokenRequest,
    jwt_manager: JWTAPIManager = Depends(get_jwt_manager)
) -> JSONResponse:
    """User login with JWT token generation"""

    result = await jwt_manager.login_user(request)
    return JSONResponse(content=result)


@router.post("/api-keys")
async def create_api_key_endpoint(
    request: APIKeyRequest,
    user_info: dict[str, Any] = Depends(verify_jwt_token),
    jwt_manager: JWTAPIManager = Depends(get_jwt_manager)
) -> JSONResponse:
    """Create new API key"""

    result = await jwt_manager.create_api_key(user_info["user_id"], request)
    return JSONResponse(content=result)


@router.get("/verify")
async def verify_token_endpoint(
    user_info: dict[str, Any] = Depends(verify_jwt_token)
) -> JSONResponse:
    """Verify JWT token"""

    return JSONResponse(content={
        "success": True,
        "user": user_info,
        "message": "Token valid"
    })


@router.get("/verify-api-key")
async def verify_api_key_endpoint(
    user_info: dict[str, Any] = Depends(verify_api_key)
) -> JSONResponse:
    """Verify API key"""

    return JSONResponse(content={
        "success": True,
        "user": user_info,
        "message": "API key valid"
    })


@router.get("/rate-limit-status")
async def rate_limit_status_endpoint(
    user_info: dict[str, Any] = Depends(verify_jwt_token),
    jwt_manager: JWTAPIManager = Depends(get_jwt_manager)
) -> JSONResponse:
    """Get current rate limit status"""

    plan_id = user_info.get("plan_id", "starter")
    limits = jwt_manager.tier_limits.get(plan_id)

    # Get current usage from Redis
    await jwt_manager.init_services()
    current_time = int(time.time())

    minute_count = await jwt_manager.redis_client.get(f"rate_limit:{user_info['user_id']}:minute:{current_time // 60}") or 0
    hour_count = await jwt_manager.redis_client.get(f"rate_limit:{user_info['user_id']}:hour:{current_time // 3600}") or 0
    day_count = await jwt_manager.redis_client.get(f"rate_limit:{user_info['user_id']}:day:{current_time // 86400}") or 0

    return JSONResponse(content={
        "success": True,
        "plan": plan_id,
        "limits": {
            "requests_per_minute": limits.requests_per_minute,
            "requests_per_hour": limits.requests_per_hour,
            "requests_per_day": limits.requests_per_day
        },
        "current_usage": {
            "minute": int(minute_count),
            "hour": int(hour_count),
            "day": int(day_count)
        },
        "remaining": {
            "minute": max(0, limits.requests_per_minute - int(minute_count)),
            "hour": max(0, limits.requests_per_hour - int(hour_count)),
            "day": max(0, limits.requests_per_day - int(day_count))
        }
    })
