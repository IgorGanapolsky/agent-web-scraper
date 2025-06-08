"""
Parallel Task Orchestrator for Enterprise Performance
Implements multi-tool parallel execution as recommended by CTO.
"""

import asyncio
import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ParallelTask:
    """Represents a task that can be executed in parallel"""

    task_id: str
    task_type: str  # 'serpapi', 'rag', 'llm', 'analysis', 'data_fetch'
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: int = 1  # 1=highest, 5=lowest
    timeout: float = 30.0
    dependencies: list[str] = field(default_factory=list)
    context_data: Optional[dict[str, Any]] = None


@dataclass
class TaskResult:
    """Result of a parallel task execution"""

    task_id: str
    success: bool
    data: Any
    execution_time: float
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ParallelOrchestrator:
    """
    Enterprise-grade parallel task orchestrator.

    Features:
    - Simultaneous tool execution (SerpAPI + RAG + LLM)
    - Dependency management and task ordering
    - Context-aware result aggregation
    - Memory persistence across sessions
    - Real-time performance monitoring
    """

    def __init__(self, max_workers: int = 10, session_id: Optional[str] = None):
        self.max_workers = max_workers
        self.session_id = session_id or f"session_{int(time.time())}"
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.session_memory = {}
        self.task_registry = {}
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_execution_time": 0.0,
            "parallel_efficiency": 0.0,
        }

        # Load session memory if it exists
        self._load_session_memory()

    def _load_session_memory(self) -> None:
        """Load session memory from persistent storage"""
        memory_file = Path(f"data/session_memory_{self.session_id}.json")
        if memory_file.exists():
            try:
                with open(memory_file) as f:
                    self.session_memory = json.load(f)
                logger.info(f"Loaded session memory: {len(self.session_memory)} items")
            except Exception as e:
                logger.error(f"Failed to load session memory: {e}")

    def _save_session_memory(self) -> None:
        """Save session memory to persistent storage"""
        memory_file = Path(f"data/session_memory_{self.session_id}.json")
        memory_file.parent.mkdir(exist_ok=True)

        try:
            with open(memory_file, "w") as f:
                json.dump(self.session_memory, f, indent=2)
            logger.debug("Session memory saved successfully")
        except Exception as e:
            logger.error(f"Failed to save session memory: {e}")

    def store_context(self, key: str, data: Any) -> None:
        """Store data in session memory for context continuity"""
        self.session_memory[key] = {
            "data": data,
            "timestamp": time.time(),
            "session_id": self.session_id,
        }
        self._save_session_memory()

    def get_context(self, key: str) -> Optional[Any]:
        """Retrieve data from session memory"""
        if key in self.session_memory:
            return self.session_memory[key]["data"]
        return None

    async def execute_parallel_tasks(
        self, tasks: list[ParallelTask], aggregate_results: bool = True
    ) -> dict[str, Any]:
        """
        Execute multiple tasks in parallel with dependency management.

        Example usage:
        ```python
        tasks = [
            ParallelTask("fetch_market", "serpapi", fetch_serpapi_data, ("SaaS trends",)),
            ParallelTask("analyze_rag", "rag", process_with_rag, ("context query",)),
            ParallelTask("generate_insights", "llm", generate_insights, dependencies=["fetch_market", "analyze_rag"])
        ]

        results = await orchestrator.execute_parallel_tasks(tasks)
        ```
        """
        start_time = time.time()

        logger.info(f"Executing {len(tasks)} parallel tasks")

        # Sort tasks by priority and dependencies
        sorted_tasks = self._sort_tasks_by_dependencies(tasks)

        # Execute tasks in waves based on dependencies
        results = {}
        task_waves = self._create_execution_waves(sorted_tasks)

        for wave_num, wave_tasks in enumerate(task_waves):
            logger.info(f"Executing wave {wave_num + 1}: {len(wave_tasks)} tasks")
            wave_results = await self._execute_task_wave(wave_tasks, results)
            results.update(wave_results)

        execution_time = time.time() - start_time

        # Update performance metrics
        self._update_performance_metrics(tasks, results, execution_time)

        # Store results in session memory
        self.store_context(
            f"parallel_execution_{int(time.time())}",
            {
                "results": results,
                "execution_time": execution_time,
                "task_count": len(tasks),
            },
        )

        if aggregate_results:
            aggregated = self._aggregate_results(results, tasks)
            return aggregated

        return results

    def _sort_tasks_by_dependencies(
        self, tasks: list[ParallelTask]
    ) -> list[ParallelTask]:
        """Sort tasks based on dependencies and priority"""
        # Topological sort for dependency ordering
        task_map = {task.task_id: task for task in tasks}
        visited = set()
        sorted_tasks = []

        def visit(task_id: str):
            if task_id in visited:
                return
            visited.add(task_id)

            task = task_map[task_id]
            for dep in task.dependencies:
                if dep in task_map:
                    visit(dep)

            sorted_tasks.append(task)

        for task in tasks:
            visit(task.task_id)

        # Secondary sort by priority
        return sorted(sorted_tasks, key=lambda t: t.priority)

    def _create_execution_waves(
        self, tasks: list[ParallelTask]
    ) -> list[list[ParallelTask]]:
        """Create waves of tasks that can be executed in parallel"""
        waves = []
        remaining_tasks = tasks.copy()
        completed_tasks = set()

        while remaining_tasks:
            current_wave = []

            for task in remaining_tasks[:]:
                # Check if all dependencies are completed
                if all(dep in completed_tasks for dep in task.dependencies):
                    current_wave.append(task)
                    remaining_tasks.remove(task)

            if not current_wave and remaining_tasks:
                # Circular dependency or missing dependency - execute remaining tasks
                logger.warning(
                    "Potential circular dependency detected, executing remaining tasks"
                )
                current_wave = remaining_tasks[:]
                remaining_tasks.clear()

            if current_wave:
                waves.append(current_wave)
                completed_tasks.update(task.task_id for task in current_wave)

        return waves

    async def _execute_task_wave(
        self, tasks: list[ParallelTask], previous_results: dict[str, TaskResult]
    ) -> dict[str, TaskResult]:
        """Execute a wave of tasks in parallel"""

        async def execute_single_task(task: ParallelTask) -> TaskResult:
            start_time = time.time()

            try:
                # Inject previous results and context into task kwargs
                enhanced_kwargs = task.kwargs.copy()
                enhanced_kwargs["previous_results"] = previous_results
                enhanced_kwargs["session_context"] = self.session_memory

                # Execute task
                if asyncio.iscoroutinefunction(task.function):
                    result_data = await asyncio.wait_for(
                        task.function(*task.args, **enhanced_kwargs),
                        timeout=task.timeout,
                    )
                else:
                    # Run synchronous function in thread pool
                    result_data = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        lambda: task.function(*task.args, **enhanced_kwargs),
                    )

                execution_time = time.time() - start_time

                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    data=result_data,
                    execution_time=execution_time,
                    metadata={"task_type": task.task_type, "priority": task.priority},
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.error(f"Task {task.task_id} timed out after {task.timeout}s")
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    data=None,
                    execution_time=execution_time,
                    error="Task timeout",
                    metadata={"task_type": task.task_type, "priority": task.priority},
                )

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"Task {task.task_id} failed: {e}")
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    data=None,
                    execution_time=execution_time,
                    error=str(e),
                    metadata={"task_type": task.task_type, "priority": task.priority},
                )

        # Execute all tasks in the wave concurrently
        task_coroutines = [execute_single_task(task) for task in tasks]
        wave_results = await asyncio.gather(*task_coroutines)

        return {result.task_id: result for result in wave_results}

    def _aggregate_results(
        self, results: dict[str, TaskResult], original_tasks: list[ParallelTask]
    ) -> dict[str, Any]:
        """Aggregate and contextualize results from parallel execution"""

        successful_results = {
            task_id: result.data
            for task_id, result in results.items()
            if result.success
        }

        failed_tasks = [
            {"task_id": task_id, "error": result.error}
            for task_id, result in results.items()
            if not result.success
        ]

        total_execution_time = (
            max(result.execution_time for result in results.values()) if results else 0
        )

        # Calculate parallel efficiency
        sequential_time = sum(result.execution_time for result in results.values())
        parallel_efficiency = (
            (sequential_time / total_execution_time) if total_execution_time > 0 else 0
        )

        return {
            "success": len(failed_tasks) == 0,
            "results": successful_results,
            "failed_tasks": failed_tasks,
            "performance": {
                "total_execution_time": total_execution_time,
                "sequential_time_equivalent": sequential_time,
                "parallel_efficiency": parallel_efficiency,
                "tasks_completed": len(successful_results),
                "tasks_failed": len(failed_tasks),
            },
            "session_id": self.session_id,
            "timestamp": time.time(),
        }

    def _update_performance_metrics(
        self,
        tasks: list[ParallelTask],
        results: dict[str, TaskResult],
        execution_time: float,
    ) -> None:
        """Update performance metrics"""
        successful_count = sum(1 for r in results.values() if r.success)
        failed_count = len(results) - successful_count

        self.performance_metrics["total_tasks"] += len(tasks)
        self.performance_metrics["successful_tasks"] += successful_count
        self.performance_metrics["failed_tasks"] += failed_count

        # Update average execution time
        total_tasks = self.performance_metrics["total_tasks"]
        current_avg = self.performance_metrics["avg_execution_time"]
        self.performance_metrics["avg_execution_time"] = (
            current_avg * (total_tasks - len(tasks)) + execution_time
        ) / total_tasks

        # Calculate parallel efficiency
        sequential_time = sum(r.execution_time for r in results.values())
        if execution_time > 0:
            self.performance_metrics["parallel_efficiency"] = (
                sequential_time / execution_time
            )

    def get_performance_stats(self) -> dict[str, Any]:
        """Get current performance statistics"""
        return {
            **self.performance_metrics,
            "session_id": self.session_id,
            "active_workers": self.max_workers,
            "session_memory_size": len(self.session_memory),
        }

    async def cleanup(self) -> None:
        """Clean up resources"""
        self.executor.shutdown(wait=True)
        self._save_session_memory()


# Global orchestrator instance
_parallel_orchestrator = None


def get_parallel_orchestrator(session_id: Optional[str] = None) -> ParallelOrchestrator:
    """Get the global parallel orchestrator instance"""
    global _parallel_orchestrator
    if _parallel_orchestrator is None:
        _parallel_orchestrator = ParallelOrchestrator(session_id=session_id)
    return _parallel_orchestrator


# Convenience functions for common enterprise patterns
async def execute_market_research_pipeline(
    query: str, sources: list[str] | None = None
) -> dict[str, Any]:
    """Execute complete market research pipeline in parallel"""

    orchestrator = get_parallel_orchestrator()

    # Mock implementations - replace with actual functions
    async def fetch_serpapi_data(search_query: str, **kwargs) -> dict[str, Any]:
        await asyncio.sleep(2)  # Simulate API call
        return {"serpapi_results": f"Market data for {search_query}", "count": 150}

    async def process_with_rag(query: str, **kwargs) -> dict[str, Any]:
        await asyncio.sleep(1.5)  # Simulate RAG processing
        return {"rag_context": f"Enhanced context for {query}", "relevance": 0.95}

    async def generate_insights(query: str, **kwargs) -> dict[str, Any]:
        previous = kwargs.get("previous_results", {})
        await asyncio.sleep(1)  # Simulate LLM processing
        return {"insights": f"AI insights for {query}", "sources": len(previous)}

    tasks = [
        ParallelTask(
            task_id="serpapi_fetch",
            task_type="serpapi",
            function=fetch_serpapi_data,
            args=(query,),
            priority=1,
        ),
        ParallelTask(
            task_id="rag_processing",
            task_type="rag",
            function=process_with_rag,
            args=(query,),
            priority=1,
        ),
        ParallelTask(
            task_id="insight_generation",
            task_type="llm",
            function=generate_insights,
            args=(query,),
            dependencies=["serpapi_fetch", "rag_processing"],
            priority=2,
        ),
    ]

    return await orchestrator.execute_parallel_tasks(tasks)


async def execute_enterprise_analysis_pipeline(
    prospect_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Execute enterprise prospect analysis in parallel"""

    orchestrator = get_parallel_orchestrator()

    # Create parallel tasks for each prospect
    tasks = []

    for i, prospect in enumerate(prospect_data):

        async def analyze_prospect(data: dict[str, Any], **kwargs) -> dict[str, Any]:
            await asyncio.sleep(0.5)  # Simulate analysis
            return {
                "company": data.get("company"),
                "fit_score": 8.5,
                "recommended_tier": "$1999",
                "analysis": f"High-value prospect in {data.get('industry', 'unknown')} sector",
            }

        tasks.append(
            ParallelTask(
                task_id=f"prospect_analysis_{i}",
                task_type="analysis",
                function=analyze_prospect,
                args=(prospect,),
                priority=1,
            )
        )

    return await orchestrator.execute_parallel_tasks(tasks)
