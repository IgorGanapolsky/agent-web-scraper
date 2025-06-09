#!/usr/bin/env python3
"""
Agentic RAG Engine for SaaS Market Intelligence
Multi-source, intelligent retrieval and analysis system
"""

import asyncio
import os
from typing import Any, Optional

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.agent import ReActAgent
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool, RetrieverTool
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from app.core.vector_store import VectorStoreManager
from app.utils.analytics import performance_monitor


class SaaSMarketIntelligenceRAG:
    """Advanced agentic retrieval system for SaaS market intelligence"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the agentic RAG system"""

        # Configure LlamaIndex settings
        Settings.llm = OpenAI(
            model="gpt-4-turbo-preview",
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
            temperature=0.1,
        )
        Settings.embed_model = OpenAIEmbedding(
            model="text-embedding-3-large",
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
        )

        # Initialize vector store manager
        self.vector_store_manager = VectorStoreManager()

        # Storage for indices and tools
        self.indices: dict[str, VectorStoreIndex] = {}
        self.query_engines: dict[str, Any] = {}
        self.retrieval_tools: list[QueryEngineTool] = []

        # Agent and routing components
        self.router_query_engine: Optional[RouterQueryEngine] = None
        self.react_agent: Optional[ReActAgent] = None

        print("🚀 SaaS Market Intelligence RAG Engine initialized")

    async def initialize_knowledge_base(self) -> None:
        """Initialize all knowledge bases and indices"""

        print("🔧 Initializing agentic knowledge bases...")

        # Initialize specialized indices for different data sources
        await self._setup_reddit_index()
        await self._setup_market_trends_index()
        await self._setup_github_insights_index()
        await self._setup_competitor_analysis_index()
        await self._setup_historical_reports_index()

        # Build routing and agent systems
        await self._setup_router_query_engine()
        await self._setup_react_agent()

        print("✅ Agentic knowledge base initialization complete")

    async def _setup_reddit_index(self) -> None:
        """Set up Reddit pain points and discussions index"""

        index_name = "reddit_pain_points"

        # Load existing or create new index
        if await self.vector_store_manager.index_exists(index_name):
            self.indices[index_name] = await self.vector_store_manager.load_index(
                index_name
            )
        else:
            # Create from Reddit data
            reddit_docs = await self._load_reddit_documents()
            self.indices[index_name] = await self.vector_store_manager.create_index(
                index_name, reddit_docs
            )

        # Create query engine with specialized prompt
        self.query_engines[index_name] = self.indices[index_name].as_query_engine(
            similarity_top_k=5,
            response_mode="tree_summarize",
            system_prompt="""
            You are an expert at analyzing SaaS founder pain points from Reddit discussions.
            Focus on identifying:
            1. Specific technical pain points and frustrations
            2. Business challenges and operational struggles
            3. Tool gaps and workflow inefficiencies
            4. Pricing concerns and budget constraints
            5. Integration and scalability issues

            Provide actionable insights with context about company size, industry, and urgency.
            """,
        )

        print(f"✅ Reddit pain points index ready: {index_name}")

    async def _setup_market_trends_index(self) -> None:
        """Set up market trends and SEO data index"""

        index_name = "market_trends"

        if await self.vector_store_manager.index_exists(index_name):
            self.indices[index_name] = await self.vector_store_manager.load_index(
                index_name
            )
        else:
            # Create from SerpAPI and market data
            market_docs = await self._load_market_trend_documents()
            self.indices[index_name] = await self.vector_store_manager.create_index(
                index_name, market_docs
            )

        self.query_engines[index_name] = self.indices[index_name].as_query_engine(
            similarity_top_k=8,
            response_mode="compact",
            system_prompt="""
            You are an expert at analyzing market trends and search behavior for SaaS opportunities.
            Focus on:
            1. Search volume trends and keyword growth
            2. Market size estimation and opportunity scoring
            3. Competitive landscape analysis
            4. Geographic and demographic patterns
            5. Seasonal and temporal trends

            Provide quantitative insights with confidence levels and growth projections.
            """,
        )

        print(f"✅ Market trends index ready: {index_name}")

    async def _setup_github_insights_index(self) -> None:
        """Set up GitHub technical insights and developer needs index"""

        index_name = "github_insights"

        if await self.vector_store_manager.index_exists(index_name):
            self.indices[index_name] = await self.vector_store_manager.load_index(
                index_name
            )
        else:
            # Create from GitHub data
            github_docs = await self._load_github_documents()
            self.indices[index_name] = await self.vector_store_manager.create_index(
                index_name, github_docs
            )

        self.query_engines[index_name] = self.indices[index_name].as_query_engine(
            similarity_top_k=6,
            response_mode="tree_summarize",
            system_prompt="""
            You are an expert at analyzing technical founder needs from GitHub activity.
            Focus on:
            1. Technology stack preferences and adoption patterns
            2. Open source project gaps and opportunities
            3. Developer tool frustrations and workflow issues
            4. Technical architecture challenges
            5. Integration and API requirements

            Provide technical feasibility assessments and implementation complexity estimates.
            """,
        )

        print(f"✅ GitHub insights index ready: {index_name}")

    async def _setup_competitor_analysis_index(self) -> None:
        """Set up competitor analysis and pricing data index"""

        index_name = "competitor_analysis"

        if await self.vector_store_manager.index_exists(index_name):
            self.indices[index_name] = await self.vector_store_manager.load_index(
                index_name
            )
        else:
            # Create from competitor data
            competitor_docs = await self._load_competitor_documents()
            self.indices[index_name] = await self.vector_store_manager.create_index(
                index_name, competitor_docs
            )

        self.query_engines[index_name] = self.indices[index_name].as_query_engine(
            similarity_top_k=10,
            response_mode="compact",
            system_prompt="""
            You are an expert at competitive analysis for SaaS markets.
            Focus on:
            1. Pricing strategies and revenue models
            2. Feature gaps and differentiation opportunities
            3. Market positioning and messaging analysis
            4. Customer feedback and satisfaction levels
            5. Go-to-market strategies and channels

            Provide competitive intelligence with actionable positioning recommendations.
            """,
        )

        print(f"✅ Competitor analysis index ready: {index_name}")

    async def _setup_historical_reports_index(self) -> None:
        """Set up historical reports and insights index"""

        index_name = "historical_reports"

        if await self.vector_store_manager.index_exists(index_name):
            self.indices[index_name] = await self.vector_store_manager.load_index(
                index_name
            )
        else:
            # Create from existing reports
            report_docs = await self._load_historical_reports()
            self.indices[index_name] = await self.vector_store_manager.create_index(
                index_name, report_docs
            )

        self.query_engines[index_name] = self.indices[index_name].as_query_engine(
            similarity_top_k=5,
            response_mode="tree_summarize",
            system_prompt="""
            You are an expert at synthesizing historical market intelligence patterns.
            Focus on:
            1. Trend evolution and pattern recognition
            2. Successful opportunity identification examples
            3. Market timing and opportunity lifecycle analysis
            4. Previous insight validation and outcomes
            5. Methodological improvements and lessons learned

            Provide contextual insights that improve future analysis quality.
            """,
        )

        print(f"✅ Historical reports index ready: {index_name}")

    async def _setup_router_query_engine(self) -> None:
        """Set up intelligent routing query engine"""

        # Create query engine tools for routing
        tools = [
            QueryEngineTool.from_defaults(
                query_engine=self.query_engines["reddit_pain_points"],
                description="Expert at finding SaaS founder pain points, frustrations, and specific problems from Reddit discussions. Use for understanding customer problems and needs.",
            ),
            QueryEngineTool.from_defaults(
                query_engine=self.query_engines["market_trends"],
                description="Expert at market sizing, search trends, SEO data, and quantitative opportunity analysis. Use for market research and demand validation.",
            ),
            QueryEngineTool.from_defaults(
                query_engine=self.query_engines["github_insights"],
                description="Expert at technical requirements, developer tools, and technical feasibility analysis from GitHub activity. Use for understanding implementation complexity.",
            ),
            QueryEngineTool.from_defaults(
                query_engine=self.query_engines["competitor_analysis"],
                description="Expert at competitive landscape, pricing strategies, and market positioning analysis. Use for competitive intelligence and positioning.",
            ),
            QueryEngineTool.from_defaults(
                query_engine=self.query_engines["historical_reports"],
                description="Expert at historical patterns, trend analysis, and previous market intelligence insights. Use for context and pattern recognition.",
            ),
        ]

        # Create router with LLM-based selection
        self.router_query_engine = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=tools,
            verbose=True,
        )

        print("✅ Intelligent routing query engine configured")

    async def _setup_react_agent(self) -> None:
        """Set up ReAct agent for complex multi-step reasoning"""

        # Create retriever tools for the agent
        retriever_tools = []

        for index_name, index in self.indices.items():
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=3,
            )

            retriever_tool = RetrieverTool.from_defaults(
                retriever=retriever,
                description=f"Retrieve relevant information from {index_name} knowledge base",
            )
            retriever_tools.append(retriever_tool)

        # Add query engine tools
        query_tools = [
            QueryEngineTool.from_defaults(
                query_engine=self.router_query_engine,
                description="Intelligent multi-source query routing for comprehensive market analysis",
            )
        ]

        # Create ReAct agent with memory
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

        self.react_agent = ReActAgent.from_tools(
            tools=retriever_tools + query_tools,
            memory=memory,
            verbose=True,
            system_prompt="""
            You are an expert SaaS market intelligence agent with access to multiple specialized knowledge bases.

            Your capabilities:
            1. Multi-source intelligence gathering and synthesis
            2. Pattern recognition across different data types
            3. Opportunity scoring and prioritization
            4. Technical feasibility assessment
            5. Competitive positioning analysis

            When analyzing opportunities:
            1. Gather information from multiple relevant sources
            2. Validate findings across different data types
            3. Provide confidence levels and supporting evidence
            4. Consider technical feasibility and market timing
            5. Suggest actionable next steps

            Always think step-by-step and explain your reasoning process.
            """,
        )

        print("✅ ReAct agent configured with multi-source capabilities")

    @performance_monitor
    async def analyze_market_opportunity(
        self, query: str, use_agent: bool = True, sources: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Analyze market opportunity using agentic retrieval"""

        print(f"🔍 Analyzing market opportunity: {query}")

        if use_agent and self.react_agent:
            # Use ReAct agent for complex multi-step analysis
            response = await self._agent_analysis(query)
        else:
            # Use router query engine for direct analysis
            response = await self._router_analysis(query, sources)

        # Extract and structure the analysis
        analysis = {
            "query": query,
            "analysis_type": "agent" if use_agent else "router",
            "response": str(response),
            "confidence_score": self._calculate_confidence_score(response),
            "sources_used": self._extract_sources_used(response),
            "recommendations": self._extract_recommendations(response),
            "opportunity_score": self._calculate_opportunity_score(response),
        }

        print("✅ Market opportunity analysis complete")
        return analysis

    async def _agent_analysis(self, query: str) -> Any:
        """Perform analysis using ReAct agent"""
        return await self.react_agent.achat(query)

    async def _router_analysis(
        self, query: str, sources: Optional[list[str]] = None
    ) -> Any:
        """Perform analysis using router query engine"""
        if sources:
            # Filter to specific sources if requested
            filtered_query = f"Focus on sources: {', '.join(sources)}. Query: {query}"
            return await self.router_query_engine.aquery(filtered_query)
        else:
            return await self.router_query_engine.aquery(query)

    def _calculate_confidence_score(self, response: Any) -> float:
        """Calculate confidence score based on response quality"""
        # Placeholder - implement based on response analysis
        return 0.85

    def _extract_sources_used(self, response: Any) -> list[str]:
        """Extract which sources were used in the analysis"""
        # Placeholder - implement based on response metadata
        return ["reddit_pain_points", "market_trends"]

    def _extract_recommendations(self, response: Any) -> list[str]:
        """Extract actionable recommendations from response"""
        # Placeholder - implement based on response parsing
        return [
            "Validate with direct customer interviews",
            "Analyze pricing sensitivity",
        ]

    def _calculate_opportunity_score(self, response: Any) -> float:
        """Calculate numerical opportunity score"""
        # Placeholder - implement based on response analysis
        return 7.8

    async def _load_reddit_documents(self) -> list[Any]:
        """Load Reddit documents for indexing"""
        # Placeholder - implement document loading
        return []

    async def _load_market_trend_documents(self) -> list[Any]:
        """Load market trend documents for indexing"""
        # Placeholder - implement document loading
        return []

    async def _load_github_documents(self) -> list[Any]:
        """Load GitHub documents for indexing"""
        # Placeholder - implement document loading
        return []

    async def _load_competitor_documents(self) -> list[Any]:
        """Load competitor analysis documents for indexing"""
        # Placeholder - implement document loading
        return []

    async def _load_historical_reports(self) -> list[Any]:
        """Load historical reports for indexing"""
        # Placeholder - implement document loading
        return []

    async def add_documents_to_index(
        self, index_name: str, documents: list[Any]
    ) -> None:
        """Add new documents to an existing index"""

        if index_name not in self.indices:
            raise ValueError(f"Index {index_name} does not exist")

        # Add documents to vector store
        await self.vector_store_manager.add_documents(index_name, documents)

        # Refresh index
        self.indices[index_name] = await self.vector_store_manager.load_index(
            index_name
        )

        print(f"✅ Added {len(documents)} documents to {index_name}")

    async def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status"""

        status = {
            "indices_loaded": len(self.indices),
            "query_engines_ready": len(self.query_engines),
            "router_configured": self.router_query_engine is not None,
            "agent_ready": self.react_agent is not None,
            "indices": {},
        }

        for name, index in self.indices.items():
            status["indices"][name] = {
                "document_count": len(index.docstore.docs),
                "ready": True,
            }

        return status


async def main():
    """Test the agentic RAG system"""

    print("🚀 Testing SaaS Market Intelligence RAG Engine")

    # Initialize the system
    rag_engine = SaaSMarketIntelligenceRAG()
    await rag_engine.initialize_knowledge_base()

    # Test analysis
    test_query = "Find underserved SaaS opportunities for Python developers in the automation space"
    analysis = await rag_engine.analyze_market_opportunity(test_query)

    print("\n📊 Analysis Results:")
    print(f"Query: {analysis['query']}")
    print(f"Confidence: {analysis['confidence_score']}")
    print(f"Opportunity Score: {analysis['opportunity_score']}")
    print(f"Sources Used: {', '.join(analysis['sources_used'])}")

    # Get system status
    status = await rag_engine.get_system_status()
    print(f"\n🔧 System Status: {status}")


if __name__ == "__main__":
    asyncio.run(main())
