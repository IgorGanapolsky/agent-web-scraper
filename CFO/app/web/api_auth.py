"""API authentication and rate limiting middleware."""

import time
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.logging import get_logger
from app.models.api_key import APIKeyUsage
from app.services.api_key_service import APIKeyService, RateLimitExceeded

logger = get_logger(__name__)


class APIKeyAuth(HTTPBearer):
    """API key authentication handler."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.api_key_service = APIKeyService()

    async def __call__(self, request: Request) -> Optional[str]:
        """Validate API key from request."""
        # Try to get API key from header
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            if credentials.scheme != "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme",
                )

            api_key = credentials.credentials
        else:
            # Try to get from query parameter as fallback
            api_key = request.query_params.get("api_key")

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="API key required"
            )

        # Validate API key
        api_key_obj = self.api_key_service.validate_api_key(api_key)

        if not api_key_obj:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
            )

        # Check rate limits
        try:
            self.api_key_service.check_rate_limit(api_key_obj, str(request.url.path))
        except RateLimitExceeded as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
                headers={"Retry-After": "60"},  # Retry after 60 seconds
            )

        # Store API key info in request state for later use
        request.state.api_key = api_key_obj
        request.state.start_time = time.time()

        return api_key


# Dependency for protected routes
api_key_auth = APIKeyAuth()


async def track_api_usage(request: Request, response):
    """Track API usage after request completion."""
    if hasattr(request.state, "api_key") and hasattr(request.state, "start_time"):
        api_key = request.state.api_key
        response_time = (time.time() - request.state.start_time) * 1000  # Convert to ms

        # Create usage record
        usage = APIKeyUsage(
            api_key=api_key.key,
            customer_id=api_key.customer_id,
            endpoint=str(request.url.path),
            method=request.method,
            status_code=response.status_code,
            response_time_ms=response_time,
        )

        # Track tokens if available (would be set by the endpoint)
        if hasattr(response, "tokens_used"):
            usage.tokens_used = response.tokens_used

        # Track usage
        api_key_service = APIKeyService()
        api_key_service.track_usage(api_key, usage)
