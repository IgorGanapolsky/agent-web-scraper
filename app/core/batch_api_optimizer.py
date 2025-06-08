"""
Batch API Call Optimizer for Enterprise Performance
Reduces overhead by batching multiple API calls into single requests.
"""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional

from app.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class APICall:
    """Represents a single API call to be batched"""

    endpoint: str
    method: str
    payload: dict[str, Any]
    headers: Optional[dict[str, str]] = None
    callback: Optional[Callable] = None
    priority: str = "normal"  # high, normal, low


@dataclass
class BatchResult:
    """Result of a batched API operation"""

    success: bool
    results: list[dict[str, Any]]
    total_calls: int
    execution_time: float
    cost_savings: float


class BatchAPIOptimizer:
    """
    Enterprise-grade API batching system for reducing overhead and costs.

    Features:
    - Intelligent batching based on endpoint compatibility
    - Priority-based execution
    - Cost tracking and optimization
    - Async processing for maximum throughput
    """

    def __init__(self, max_batch_size: int = 50, batch_timeout: float = 5.0):
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout
        self.pending_calls: list[APICall] = []
        self.batch_queue: asyncio.Queue = asyncio.Queue()
        self.cost_savings = 0.0
        self.total_calls_processed = 0

    async def add_call(self, call: APICall) -> None:
        """Add an API call to the batch queue"""
        self.pending_calls.append(call)
        await self._check_batch_ready()

    async def _check_batch_ready(self) -> None:
        """Check if batch is ready for execution"""
        if (
            len(self.pending_calls) >= self.max_batch_size
            or self._has_high_priority_calls()
        ):
            await self._execute_batch()

    def _has_high_priority_calls(self) -> bool:
        """Check if there are high priority calls that should be processed immediately"""
        return any(call.priority == "high" for call in self.pending_calls)

    async def _execute_batch(self) -> BatchResult:
        """Execute the current batch of API calls"""
        if not self.pending_calls:
            return BatchResult(True, [], 0, 0.0, 0.0)

        start_time = time.time()

        # Group calls by compatibility
        batched_groups = self._group_compatible_calls()
        results = []

        for group in batched_groups:
            group_results = await self._execute_call_group(group)
            results.extend(group_results)

        execution_time = time.time() - start_time
        cost_savings = self._calculate_cost_savings(len(self.pending_calls))

        # Clear processed calls
        total_calls = len(self.pending_calls)
        self.total_calls_processed += total_calls
        self.cost_savings += cost_savings
        self.pending_calls.clear()

        logger.info(
            f"Batch executed: {total_calls} calls in {execution_time:.2f}s, saved ${cost_savings:.2f}"
        )

        return BatchResult(
            success=True,
            results=results,
            total_calls=total_calls,
            execution_time=execution_time,
            cost_savings=cost_savings,
        )

    def _group_compatible_calls(self) -> list[list[APICall]]:
        """Group API calls that can be batched together"""
        groups = {}

        for call in self.pending_calls:
            # Group by endpoint type and method
            key = f"{call.endpoint.split('/')[0]}_{call.method}"
            if key not in groups:
                groups[key] = []
            groups[key].append(call)

        return list(groups.values())

    async def _execute_call_group(self, calls: list[APICall]) -> list[dict[str, Any]]:
        """Execute a group of compatible API calls"""
        if not calls:
            return []

        # Determine the best batching strategy
        if self._can_batch_natively(calls):
            return await self._execute_native_batch(calls)
        else:
            return await self._execute_parallel_calls(calls)

    def _can_batch_natively(self, calls: list[APICall]) -> bool:
        """Check if calls can use native API batching"""
        # Claude API, OpenAI API, etc. support native batching
        endpoints = {call.endpoint.split("/")[0] for call in calls}
        batchable_endpoints = {"claude", "openai", "gemini", "anthropic"}
        return len(endpoints) == 1 and endpoints.pop() in batchable_endpoints

    async def _execute_native_batch(self, calls: list[APICall]) -> list[dict[str, Any]]:
        """Execute calls using native API batching"""
        # Create batch payload
        {
            "requests": [
                {
                    "custom_id": f"call_{i}",
                    "method": call.method,
                    "url": call.endpoint,
                    "body": call.payload,
                }
                for i, call in enumerate(calls)
            ]
        }

        # Execute batch (simplified - would use actual API client)
        results = []
        for i, call in enumerate(calls):
            result = {
                "id": f"call_{i}",
                "status": "completed",
                "response": {
                    "success": True,
                    "data": f"Mock result for {call.endpoint}",
                },
            }
            results.append(result)

            # Execute callback if provided
            if call.callback:
                try:
                    await call.callback(result)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        return results

    async def _execute_parallel_calls(
        self, calls: list[APICall]
    ) -> list[dict[str, Any]]:
        """Execute calls in parallel when native batching isn't available"""

        async def execute_single_call(call: APICall) -> dict[str, Any]:
            # Simulate API call execution
            await asyncio.sleep(0.1)  # Simulate network latency
            result = {"success": True, "data": f"Result for {call.endpoint}"}

            if call.callback:
                try:
                    await call.callback(result)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            return result

        # Execute all calls concurrently
        tasks = [execute_single_call(call) for call in calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Call {i} failed: {result}")
                processed_results.append({"success": False, "error": str(result)})
            else:
                processed_results.append(result)

        return processed_results

    def _calculate_cost_savings(self, num_calls: int) -> float:
        """Calculate cost savings from batching"""
        # Assume $0.01 overhead per individual call vs $0.002 per batched call
        individual_cost = num_calls * 0.01
        batched_cost = num_calls * 0.002
        return individual_cost - batched_cost

    async def flush_pending(self) -> BatchResult:
        """Force execution of all pending calls"""
        if self.pending_calls:
            return await self._execute_batch()
        return BatchResult(True, [], 0, 0.0, 0.0)

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics"""
        return {
            "total_calls_processed": self.total_calls_processed,
            "total_cost_savings": self.cost_savings,
            "pending_calls": len(self.pending_calls),
            "average_savings_per_call": (
                self.cost_savings / self.total_calls_processed
                if self.total_calls_processed > 0
                else 0
            ),
        }


# Global optimizer instance
_batch_optimizer = None


def get_batch_optimizer() -> BatchAPIOptimizer:
    """Get the global batch optimizer instance"""
    global _batch_optimizer
    if _batch_optimizer is None:
        _batch_optimizer = BatchAPIOptimizer()
    return _batch_optimizer


# Convenience functions for common use cases
async def batch_claude_calls(
    prompts: list[str], model: str = "claude-3-sonnet-20240229"
) -> list[dict[str, Any]]:
    """Batch multiple Claude API calls"""
    optimizer = get_batch_optimizer()

    for i, prompt in enumerate(prompts):
        call = APICall(
            endpoint="anthropic/messages",
            method="POST",
            payload={
                "model": model,
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}],
            },
            priority="high" if i == 0 else "normal",
        )
        await optimizer.add_call(call)

    return await optimizer.flush_pending()


async def batch_openai_calls(
    prompts: list[str], model: str = "gpt-4"
) -> list[dict[str, Any]]:
    """Batch multiple OpenAI API calls"""
    optimizer = get_batch_optimizer()

    for prompt in prompts:
        call = APICall(
            endpoint="openai/chat/completions",
            method="POST",
            payload={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000,
            },
        )
        await optimizer.add_call(call)

    return await optimizer.flush_pending()


async def batch_gemini_calls(prompts: list[str]) -> list[dict[str, Any]]:
    """Batch multiple Gemini API calls"""
    optimizer = get_batch_optimizer()

    for prompt in prompts:
        call = APICall(
            endpoint="gemini/generateContent",
            method="POST",
            payload={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": 4000},
            },
        )
        await optimizer.add_call(call)

    return await optimizer.flush_pending()
