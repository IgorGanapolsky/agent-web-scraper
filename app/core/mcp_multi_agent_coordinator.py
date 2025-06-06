#!/usr/bin/env python3
"""
MCP Multi-Agent Coordinator
Coordinates Claude, Gemini, and ChatGPT agents with shared job queues and status logs
"""

import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

import aiohttp
from pydantic import BaseModel

from app.config.logging import get_logger
from app.core.session_memory import get_session_memory_manager

logger = get_logger(__name__)


class AgentType(Enum):
    """Available AI agents"""
    CLAUDE = "claude"
    GEMINI = "gemini" 
    CHATGPT = "chatgpt"


class JobStatus(Enum):
    """Job status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AgentJob(BaseModel):
    """Individual job for AI agent execution"""
    
    id: str
    agent_type: AgentType
    job_type: str
    title: str
    description: str
    payload: Dict
    priority: JobPriority = JobPriority.MEDIUM
    status: JobStatus = JobStatus.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = []
    tags: List[str] = []


class MCPCoordinator:
    """Multi-agent coordinator using MCP servers"""
    
    def __init__(self):
        self.memory = get_session_memory_manager()
        self.job_queue_file = "data/memory/mcp_job_queue.json"
        self.status_log_file = "data/memory/mcp_status_log.json"
        
        # Agent configurations
        self.agents = {
            AgentType.CLAUDE: {
                "api_url": "https://api.anthropic.com/v1/messages",
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "capabilities": ["reasoning", "analysis", "code_generation", "content_creation"],
                "cost_per_token": 0.003,  # Sonnet 4 average
                "max_concurrent": 5
            },
            AgentType.GEMINI: {
                "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                "api_key": os.getenv("GEMINI_API_KEY"),
                "capabilities": ["multimodal", "analysis", "search", "reasoning"],
                "cost_per_token": 0.0005,  # Gemini Pro
                "max_concurrent": 3
            },
            AgentType.CHATGPT: {
                "api_url": "https://api.openai.com/v1/chat/completions",
                "api_key": os.getenv("OPENAI_API_KEY"),
                "capabilities": ["conversation", "code_generation", "analysis", "creative"],
                "cost_per_token": 0.002,  # GPT-4
                "max_concurrent": 4
            }
        }
        
        # Job queue and status tracking
        self.job_queue: List[AgentJob] = []
        self.active_jobs: Dict[str, AgentJob] = {}
        self.completed_jobs: List[AgentJob] = []
        
        # Load existing data
        self._load_job_queue()
        self._load_status_log()
        
        logger.info("MCP Multi-Agent Coordinator initialized")
    
    async def submit_job(self, agent_type: AgentType, job_type: str, title: str, 
                        description: str, payload: Dict, priority: JobPriority = JobPriority.MEDIUM,
                        dependencies: List[str] = None, tags: List[str] = None) -> str:
        """Submit a job to the agent queue"""
        
        job_id = f"{agent_type.value}_{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        job = AgentJob(
            id=job_id,
            agent_type=agent_type,
            job_type=job_type,
            title=title,
            description=description,
            payload=payload,
            priority=priority,
            created_at=datetime.now(),
            dependencies=dependencies or [],
            tags=tags or []
        )
        
        # Add to queue
        self.job_queue.append(job)
        
        # Sort queue by priority
        self.job_queue.sort(key=lambda x: x.priority.value, reverse=True)
        
        # Save queue
        self._save_job_queue()
        
        # Log job submission
        self._log_status(f"Job {job_id} submitted to {agent_type.value} queue")
        
        logger.info(f"Job submitted: {job_id} - {title}")
        
        return job_id
    
    async def execute_parallel_jobs(self, max_concurrent: int = 10) -> Dict:
        """Execute jobs in parallel across all agents"""
        
        logger.info(f"Starting parallel job execution with max {max_concurrent} concurrent jobs")
        
        start_time = datetime.now()
        results = {"completed": [], "failed": [], "execution_stats": {}}
        
        # Get ready jobs (no unmet dependencies)
        ready_jobs = self._get_ready_jobs()
        
        if not ready_jobs:
            logger.info("No jobs ready for execution")
            return results
        
        # Create execution tasks
        tasks = []
        for job in ready_jobs[:max_concurrent]:
            task = asyncio.create_task(self._execute_job(job), name=job.id)
            tasks.append(task)
        
        # Execute jobs concurrently
        job_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(job_results):
            job = ready_jobs[i]
            
            if isinstance(result, Exception):
                job.status = JobStatus.FAILED
                job.error = str(result)
                job.completed_at = datetime.now()
                results["failed"].append({"job_id": job.id, "error": str(result)})
                logger.error(f"Job {job.id} failed: {result}")
            else:
                job.status = JobStatus.COMPLETED
                job.result = result
                job.completed_at = datetime.now()
                results["completed"].append({"job_id": job.id, "result": result})
                logger.info(f"Job {job.id} completed successfully")
            
            # Move to completed jobs
            self.completed_jobs.append(job)
            if job in self.job_queue:
                self.job_queue.remove(job)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        results["execution_stats"] = {
            "total_jobs_executed": len(job_results),
            "execution_time_seconds": execution_time,
            "jobs_completed": len(results["completed"]),
            "jobs_failed": len(results["failed"]),
            "remaining_queue_size": len(self.job_queue)
        }
        
        # Save updated state
        self._save_job_queue()
        self._save_status_log()
        
        logger.info(f"Parallel execution completed: {len(results['completed'])} successful, {len(results['failed'])} failed")
        
        return results
    
    async def _execute_job(self, job: AgentJob) -> Dict:
        """Execute a single job"""
        
        job.status = JobStatus.IN_PROGRESS
        job.started_at = datetime.now()
        
        self._log_status(f"Executing job {job.id} with {job.agent_type.value}")
        
        try:
            # Route to appropriate agent
            if job.agent_type == AgentType.CLAUDE:
                result = await self._execute_claude_job(job)
            elif job.agent_type == AgentType.GEMINI:
                result = await self._execute_gemini_job(job)
            elif job.agent_type == AgentType.CHATGPT:
                result = await self._execute_chatgpt_job(job)
            else:
                raise ValueError(f"Unknown agent type: {job.agent_type}")
            
            self._log_status(f"Job {job.id} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error executing job {job.id}: {e}")
            
            # Retry logic
            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = JobStatus.PENDING
                self.job_queue.append(job)  # Re-queue for retry
                self._log_status(f"Job {job.id} queued for retry ({job.retry_count}/{job.max_retries})")
                return {"status": "retrying", "attempt": job.retry_count}
            else:
                self._log_status(f"Job {job.id} failed after {job.max_retries} retries")
                raise e
    
    async def _execute_claude_job(self, job: AgentJob) -> Dict:
        """Execute job using Claude"""
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.agents[AgentType.CLAUDE]["api_key"],
            "anthropic-version": "2023-06-01"
        }
        
        # Build prompt based on job type
        prompt = self._build_claude_prompt(job)
        
        payload = {
            "model": "claude-3-sonnet-20240229",  # Use Sonnet 4 for 80% of operations
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.agents[AgentType.CLAUDE]["api_url"],
                json=payload,
                headers=headers,
                timeout=300
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "agent": "claude",
                        "content": result.get("content", [{}])[0].get("text", ""),
                        "usage": result.get("usage", {}),
                        "job_type": job.job_type
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Claude API error {response.status}: {error_text}")
    
    async def _execute_gemini_job(self, job: AgentJob) -> Dict:
        """Execute job using Gemini"""
        
        # Build Gemini request
        prompt = self._build_gemini_prompt(job)
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 4000,
                "temperature": 0.7
            }
        }
        
        headers = {"Content-Type": "application/json"}
        
        url = f"{self.agents[AgentType.GEMINI]['api_url']}?key={self.agents[AgentType.GEMINI]['api_key']}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=300) as response:
                if response.status == 200:
                    result = await response.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return {
                            "agent": "gemini",
                            "content": content,
                            "usage": result.get("usageMetadata", {}),
                            "job_type": job.job_type
                        }
                    else:
                        raise Exception("No candidates returned from Gemini")
                else:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")
    
    async def _execute_chatgpt_job(self, job: AgentJob) -> Dict:
        """Execute job using ChatGPT"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.agents[AgentType.CHATGPT]['api_key']}"
        }
        
        prompt = self._build_chatgpt_prompt(job)
        
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.agents[AgentType.CHATGPT]["api_url"],
                json=payload,
                headers=headers,
                timeout=300
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "agent": "chatgpt",
                        "content": content,
                        "usage": result.get("usage", {}),
                        "job_type": job.job_type
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"ChatGPT API error {response.status}: {error_text}")
    
    def _build_claude_prompt(self, job: AgentJob) -> str:
        """Build Claude-specific prompt"""
        return f"""
Job Type: {job.job_type}
Title: {job.title}
Description: {job.description}

Context: {json.dumps(job.payload, indent=2)}

Please provide a comprehensive response focusing on actionable insights and specific recommendations. Use your analytical capabilities to deliver high-quality results.
"""
    
    def _build_gemini_prompt(self, job: AgentJob) -> str:
        """Build Gemini-specific prompt"""
        return f"""
Task: {job.title}

{job.description}

Data: {json.dumps(job.payload, indent=2)}

Please analyze this information and provide detailed insights with practical recommendations. Focus on multimodal analysis if applicable.
"""
    
    def _build_chatgpt_prompt(self, job: AgentJob) -> str:
        """Build ChatGPT-specific prompt"""
        return f"""
I need help with: {job.title}

{job.description}

Context information:
{json.dumps(job.payload, indent=2)}

Please provide a detailed analysis with creative solutions and practical next steps.
"""
    
    def _get_ready_jobs(self) -> List[AgentJob]:
        """Get jobs ready for execution (no unmet dependencies)"""
        ready_jobs = []
        
        for job in self.job_queue:
            if job.status == JobStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_met = all(
                    any(completed_job.id == dep_id for completed_job in self.completed_jobs)
                    for dep_id in job.dependencies
                )
                
                if dependencies_met:
                    ready_jobs.append(job)
        
        return ready_jobs
    
    def _log_status(self, message: str):
        """Log status message"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        
        # Add to memory
        self.memory.store_memory_node(
            category="mcp_status_log",
            content=log_entry,
            tags=["mcp", "status", "coordination"],
            importance_score=0.5
        )
        
        logger.info(message)
    
    def _load_job_queue(self):
        """Load job queue from file"""
        if os.path.exists(self.job_queue_file):
            try:
                with open(self.job_queue_file, 'r') as f:
                    queue_data = json.load(f)
                    self.job_queue = [AgentJob(**job_data) for job_data in queue_data]
                logger.info(f"Loaded {len(self.job_queue)} jobs from queue")
            except Exception as e:
                logger.error(f"Error loading job queue: {e}")
    
    def _save_job_queue(self):
        """Save job queue to file"""
        try:
            os.makedirs(os.path.dirname(self.job_queue_file), exist_ok=True)
            queue_data = [job.dict() for job in self.job_queue]
            with open(self.job_queue_file, 'w') as f:
                json.dump(queue_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving job queue: {e}")
    
    def _load_status_log(self):
        """Load status log from file"""
        if os.path.exists(self.status_log_file):
            try:
                with open(self.status_log_file, 'r') as f:
                    self.status_log = json.load(f)
                logger.info(f"Loaded status log with {len(self.status_log)} entries")
            except Exception as e:
                logger.error(f"Error loading status log: {e}")
                self.status_log = []
        else:
            self.status_log = []
    
    def _save_status_log(self):
        """Save status log to file"""
        try:
            os.makedirs(os.path.dirname(self.status_log_file), exist_ok=True)
            with open(self.status_log_file, 'w') as f:
                json.dump(self.status_log, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving status log: {e}")
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        return {
            "queue_size": len(self.job_queue),
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.completed_jobs),
            "jobs_by_agent": {
                agent.value: len([job for job in self.job_queue if job.agent_type == agent])
                for agent in AgentType
            },
            "jobs_by_status": {
                status.value: len([job for job in self.job_queue if job.status == status])
                for status in JobStatus
            }
        }


async def demo_mcp_coordination():
    """Demonstrate MCP multi-agent coordination"""
    
    coordinator = MCPCoordinator()
    
    print("🤖 MCP Multi-Agent Coordinator Demo")
    print("=" * 50)
    
    # Submit various jobs to different agents
    jobs = [
        # Claude jobs (reasoning and analysis)
        {
            "agent": AgentType.CLAUDE,
            "type": "market_analysis",
            "title": "SaaS Market Analysis",
            "description": "Analyze current SaaS market trends and opportunities",
            "payload": {"industry": "SaaS", "focus": "market_trends"},
            "priority": JobPriority.HIGH
        },
        {
            "agent": AgentType.CLAUDE,
            "type": "code_generation",
            "title": "API Endpoint Generation",
            "description": "Generate FastAPI endpoints for Stripe integration",
            "payload": {"framework": "FastAPI", "integration": "Stripe"},
            "priority": JobPriority.HIGH
        },
        
        # Gemini jobs (multimodal and search)
        {
            "agent": AgentType.GEMINI,
            "type": "competitive_research",
            "title": "Competitive Landscape Research",
            "description": "Research competitors in the market intelligence space",
            "payload": {"competitors": ["SimilarWeb", "Ahrefs", "SEMrush"]},
            "priority": JobPriority.MEDIUM
        },
        
        # ChatGPT jobs (creative and conversational)
        {
            "agent": AgentType.CHATGPT,
            "type": "content_creation",
            "title": "Marketing Content Creation",
            "description": "Create engaging marketing content for SaaS platform",
            "payload": {"type": "blog_posts", "target_audience": "SaaS founders"},
            "priority": JobPriority.MEDIUM
        }
    ]
    
    # Submit jobs
    job_ids = []
    for job_spec in jobs:
        job_id = await coordinator.submit_job(
            agent_type=job_spec["agent"],
            job_type=job_spec["type"],
            title=job_spec["title"],
            description=job_spec["description"],
            payload=job_spec["payload"],
            priority=job_spec["priority"]
        )
        job_ids.append(job_id)
        print(f"• Submitted: {job_spec['title']} to {job_spec['agent'].value}")
    
    print(f"\n📋 Queue Status:")
    status = coordinator.get_queue_status()
    print(json.dumps(status, indent=2))
    
    # Execute jobs in parallel
    print("\n🚀 Executing jobs in parallel...")
    results = await coordinator.execute_parallel_jobs()
    
    print(f"\n📈 Execution Results:")
    print(f"• Jobs completed: {results['execution_stats']['jobs_completed']}")
    print(f"• Jobs failed: {results['execution_stats']['jobs_failed']}")
    print(f"• Execution time: {results['execution_stats']['execution_time_seconds']:.2f}s")
    
    return coordinator


if __name__ == "__main__":
    asyncio.run(demo_mcp_coordination())
