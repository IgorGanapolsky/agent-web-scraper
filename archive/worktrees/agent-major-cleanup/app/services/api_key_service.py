"""API Key management service."""

from datetime import datetime, timedelta
from typing import Optional

import redis

from app.config.logging import get_logger
from app.models.api_key import APIKey, APIKeyUsage
from app.models.customer import Customer, Subscription

logger = get_logger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    pass


class APIKeyService:
    """Service for managing API keys and rate limiting."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize API key service."""
        self.redis = redis_client or self._init_redis()
        self.api_keys: dict[str, APIKey] = {}  # In-memory cache

    def _init_redis(self) -> redis.Redis:
        """Initialize Redis connection."""
        try:
            client = redis.Redis(host="localhost", port=6379, decode_responses=True)
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Using in-memory storage.")
            return None

    def create_api_key(self, customer: Customer, subscription: Subscription) -> APIKey:
        """Create a new API key for a customer."""
        api_key = APIKey(
            customer_id=customer.id,
            subscription_id=subscription.id,
            tier=subscription.tier,
            rate_limits=APIKey().get_rate_limits(),
        )

        # Store in Redis and memory
        self._store_api_key(api_key)

        logger.info(f"Created API key for customer {customer.id}")
        return api_key

    def _store_api_key(self, api_key: APIKey):
        """Store API key in Redis and memory."""
        # Store in memory
        self.api_keys[api_key.key] = api_key

        # Store in Redis with expiration
        if self.redis:
            key = f"api_key:{api_key.key}"
            self.redis.setex(
                key,
                timedelta(days=30),  # Refresh cache every 30 days
                api_key.json(),
            )

            # Store reverse lookup
            self.redis.set(f"customer_api_key:{api_key.customer_id}", api_key.key)

    def get_api_key(self, key: str) -> Optional[APIKey]:
        """Get API key details."""
        # Check memory first
        if key in self.api_keys:
            return self.api_keys[key]

        # Check Redis
        if self.redis:
            data = self.redis.get(f"api_key:{key}")
            if data:
                api_key = APIKey.parse_raw(data)
                self.api_keys[key] = api_key  # Cache in memory
                return api_key

        return None

    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate API key and return details if valid."""
        api_key = self.get_api_key(key)

        if not api_key:
            return None

        if not api_key.is_valid():
            return None

        # Update last used
        api_key.last_used = datetime.now()
        self._store_api_key(api_key)

        return api_key

    def check_rate_limit(self, api_key: APIKey, endpoint: str) -> bool:
        """Check if request is within rate limits."""
        if not self.redis:
            # If no Redis, allow all requests (not recommended for production)
            return True

        limits = api_key.get_rate_limits()
        now = datetime.now()

        # Check per-minute limit
        minute_key = f"rate_limit:{api_key.key}:minute:{now.strftime('%Y-%m-%d-%H-%M')}"
        minute_count = self.redis.incr(minute_key)
        self.redis.expire(minute_key, 60)

        if minute_count > limits["requests_per_minute"]:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {limits['requests_per_minute']} requests per minute"
            )

        # Check per-hour limit
        hour_key = f"rate_limit:{api_key.key}:hour:{now.strftime('%Y-%m-%d-%H')}"
        hour_count = self.redis.incr(hour_key)
        self.redis.expire(hour_key, 3600)

        if hour_count > limits["requests_per_hour"]:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {limits['requests_per_hour']} requests per hour"
            )

        # Check per-day limit
        day_key = f"rate_limit:{api_key.key}:day:{now.strftime('%Y-%m-%d')}"
        day_count = self.redis.incr(day_key)
        self.redis.expire(day_key, 86400)

        if day_count > limits["requests_per_day"]:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {limits['requests_per_day']} requests per day"
            )

        return True

    def track_usage(self, api_key: APIKey, usage: APIKeyUsage):
        """Track API usage for billing and analytics."""
        # Store usage record
        if self.redis:
            # Store in sorted set by timestamp
            usage_key = (
                f"usage:{api_key.customer_id}:{datetime.now().strftime('%Y-%m')}"
            )
            self.redis.zadd(usage_key, {usage.json(): usage.timestamp.timestamp()})

            # Update monthly counters
            month_key = (
                f"usage_count:{api_key.customer_id}:{datetime.now().strftime('%Y-%m')}"
            )
            self.redis.incr(month_key)

            # Update cost tracking
            cost_key = (
                f"usage_cost:{api_key.customer_id}:{datetime.now().strftime('%Y-%m')}"
            )
            self.redis.incrbyfloat(cost_key, usage.calculate_cost())

        logger.info(
            f"Tracked usage for {api_key.customer_id}: "
            f"{usage.endpoint} - {usage.status_code} - {usage.response_time_ms}ms"
        )

    def get_usage_stats(self, customer_id: str, period: str = "current_month") -> dict:
        """Get usage statistics for a customer."""
        if not self.redis:
            return {"requests": 0, "cost": 0.0, "by_endpoint": {}, "by_day": {}}

        now = datetime.now()
        month_key = now.strftime("%Y-%m")

        # Get total requests
        count_key = f"usage_count:{customer_id}:{month_key}"
        total_requests = int(self.redis.get(count_key) or 0)

        # Get total cost
        cost_key = f"usage_cost:{customer_id}:{month_key}"
        total_cost = float(self.redis.get(cost_key) or 0)

        # Get detailed usage (last 100 records)
        usage_key = f"usage:{customer_id}:{month_key}"
        usage_records = self.redis.zrevrange(usage_key, 0, 99, withscores=True)

        # Analyze by endpoint
        by_endpoint = {}
        by_day = {}

        for record, _score in usage_records:
            usage = APIKeyUsage.parse_raw(record)

            # By endpoint
            if usage.endpoint not in by_endpoint:
                by_endpoint[usage.endpoint] = {"count": 0, "cost": 0}
            by_endpoint[usage.endpoint]["count"] += 1
            by_endpoint[usage.endpoint]["cost"] += usage.calculate_cost()

            # By day
            day = usage.timestamp.strftime("%Y-%m-%d")
            if day not in by_day:
                by_day[day] = {"count": 0, "cost": 0}
            by_day[day]["count"] += 1
            by_day[day]["cost"] += usage.calculate_cost()

        return {
            "period": month_key,
            "total_requests": total_requests,
            "total_cost": round(total_cost, 4),
            "by_endpoint": by_endpoint,
            "by_day": by_day,
        }

    def rotate_api_key(self, customer_id: str) -> Optional[APIKey]:
        """Rotate API key for a customer."""
        # Get current key
        if self.redis:
            current_key_id = self.redis.get(f"customer_api_key:{customer_id}")
            if current_key_id:
                current_key = self.get_api_key(current_key_id)
                if current_key:
                    # Deactivate old key
                    current_key.is_active = False
                    self._store_api_key(current_key)

                    # Create new key
                    new_key = APIKey(
                        customer_id=current_key.customer_id,
                        subscription_id=current_key.subscription_id,
                        tier=current_key.tier,
                    )
                    self._store_api_key(new_key)

                    logger.info(f"Rotated API key for customer {customer_id}")
                    return new_key

        return None

    def deactivate_api_key(self, key: str):
        """Deactivate an API key."""
        api_key = self.get_api_key(key)
        if api_key:
            api_key.is_active = False
            self._store_api_key(api_key)
            logger.info(f"Deactivated API key for customer {api_key.customer_id}")

    def get_customer_api_keys(self, customer_id: str) -> list[APIKey]:
        """Get all API keys for a customer."""
        keys = []

        # In production, this would query a database
        # For now, check Redis for the current key
        if self.redis:
            key_id = self.redis.get(f"customer_api_key:{customer_id}")
            if key_id:
                api_key = self.get_api_key(key_id)
                if api_key:
                    keys.append(api_key)

        return keys
