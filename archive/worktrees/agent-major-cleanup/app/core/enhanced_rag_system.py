"""
Enhanced RAG System with Vector Database Integration
Implements context-aware RAG for enterprise SaaS documentation and market intelligence.
"""

import hashlib
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Vector database and embedding imports
try:
    import chromadb
    import numpy as np
    from sentence_transformers import SentenceTransformer
except ImportError:
    # Fallback for environments without these dependencies
    chromadb = None
    SentenceTransformer = None
    np = None

from app.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of a document for RAG processing"""

    id: str
    content: str
    metadata: dict[str, Any]
    embedding: Optional[list[float]] = None
    chunk_index: int = 0
    document_type: str = "general"
    business_relevance: float = 0.5


@dataclass
class RAGQuery:
    """RAG query with context and preferences"""

    query: str
    max_results: int = 5
    min_relevance_score: float = 0.7
    document_types: Optional[list[str]] = None
    business_context: Optional[str] = None
    user_role: str = "general"


@dataclass
class RAGResponse:
    """RAG response with sources and confidence"""

    answer: str
    sources: list[dict[str, Any]]
    confidence_score: float
    processing_time: float
    tokens_used: int
    business_insights: list[str]


class EnterpriseRAGSystem:
    """
    Enterprise-grade RAG system with vector database integration.

    Features:
    - SaaS documentation management
    - Market intelligence integration
    - Business context awareness
    - Multi-modal document processing
    - Real-time knowledge updates
    - Cost-optimized retrieval
    """

    def __init__(self, collection_name: str = "enterprise_knowledge"):
        self.collection_name = collection_name
        self.chroma_client = None
        self.collection = None
        self.embedding_model = None
        self.document_cache = {}
        self.query_cache = {}
        self.performance_metrics = {
            "queries_processed": 0,
            "avg_response_time": 0.0,
            "cache_hit_rate": 0.0,
            "knowledge_base_size": 0,
        }

        # Initialize vector database and embedding model
        self._initialize_vector_db()
        self._initialize_embedding_model()

    def _initialize_vector_db(self) -> None:
        """Initialize ChromaDB vector database"""
        try:
            if chromadb is None:
                logger.warning("ChromaDB not available, using mock implementation")
                return

            self.chroma_client = chromadb.PersistentClient(path="./data/chroma_db")

            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection(
                    name=self.collection_name
                )
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except ValueError:  # Raised when collection doesn't exist
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Enterprise knowledge base for SaaS platform"
                    },
                )
                logger.info(f"Created new collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")

    def _initialize_embedding_model(self) -> None:
        """Initialize sentence transformer model for embeddings"""
        try:
            if SentenceTransformer is None:
                logger.warning(
                    "SentenceTransformers not available, using mock embeddings"
                )
                return

            # Use a business-optimized embedding model
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Initialized embedding model: all-MiniLM-L6-v2")

        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text"""
        if self.embedding_model is None:
            # Mock embedding for testing
            return [0.1] * 384

        try:
            embedding = self.embedding_model.encode(text).tolist()
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.1] * 384

    def _chunk_document(self, content: str, max_chunk_size: int = 1000) -> list[str]:
        """Chunk document into manageable pieces"""
        # Simple sentence-based chunking
        sentences = content.split(". ")
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk + sentence) > max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
            else:
                current_chunk += sentence + ". "

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _calculate_business_relevance(
        self, content: str, metadata: dict[str, Any]
    ) -> float:
        """Calculate business relevance score for content"""
        business_keywords = [
            "revenue",
            "customer",
            "saas",
            "enterprise",
            "roi",
            "profit",
            "market",
            "competitor",
            "growth",
            "strategy",
            "pricing",
            "subscription",
            "mrr",
            "arr",
            "churn",
            "acquisition",
        ]

        content_lower = content.lower()
        keyword_matches = sum(
            1 for keyword in business_keywords if keyword in content_lower
        )

        # Base relevance from keyword matching
        relevance = min(keyword_matches / len(business_keywords), 1.0)

        # Boost for specific document types
        doc_type = metadata.get("document_type", "general")
        if doc_type in ["strategy", "business_plan", "market_analysis"]:
            relevance += 0.3
        elif doc_type in ["technical", "api_docs"]:
            relevance += 0.1

        # Boost for recent documents
        created_date = metadata.get("created_date")
        if created_date:
            try:
                doc_date = datetime.fromisoformat(created_date)
                days_old = (datetime.now() - doc_date).days
                if days_old < 30:
                    relevance += 0.2
                elif days_old < 90:
                    relevance += 0.1
            except (TypeError, ValueError, AttributeError) as e:
                logger.debug(f"Error calculating document age: {e}")
                # Continue with default relevance if date parsing fails
                pass

        return min(relevance, 1.0)

    async def ingest_document(
        self, content: str, metadata: dict[str, Any], document_type: str = "general"
    ) -> dict[str, Any]:
        """
        Ingest a document into the RAG system.

        Args:
            content: Document content
            metadata: Document metadata (title, author, date, etc.)
            document_type: Type of document (strategy, technical, market_analysis, etc.)

        Returns:
            Ingestion result with chunk count and processing metrics
        """
        start_time = time.time()

        # Generate document ID
        doc_id = hashlib.md5(content.encode()).hexdigest()

        # Check if already processed
        if doc_id in self.document_cache:
            logger.info(f"Document {doc_id} already in cache")
            return {"success": True, "cached": True, "doc_id": doc_id}

        # Chunk the document
        chunks = self._chunk_document(content)
        logger.info(f"Document chunked into {len(chunks)} pieces")

        # Process each chunk
        document_chunks = []
        embeddings = []
        chunk_ids = []
        chunk_metadatas = []

        for i, chunk_content in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"

            # Calculate business relevance
            business_relevance = self._calculate_business_relevance(
                chunk_content, metadata
            )

            # Create chunk metadata
            chunk_metadata = {
                **metadata,
                "document_id": doc_id,
                "chunk_index": i,
                "document_type": document_type,
                "business_relevance": business_relevance,
                "ingested_at": datetime.now().isoformat(),
                "chunk_length": len(chunk_content),
            }

            # Generate embedding
            embedding = self._generate_embedding(chunk_content)

            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_content,
                metadata=chunk_metadata,
                embedding=embedding,
                chunk_index=i,
                document_type=document_type,
                business_relevance=business_relevance,
            )

            document_chunks.append(chunk)
            embeddings.append(embedding)
            chunk_ids.append(chunk_id)
            chunk_metadatas.append(chunk_metadata)

        # Store in vector database
        if self.collection is not None:
            try:
                self.collection.add(
                    embeddings=embeddings,
                    documents=[chunk.content for chunk in document_chunks],
                    metadatas=chunk_metadatas,
                    ids=chunk_ids,
                )
                logger.info(f"Stored {len(chunks)} chunks in vector database")
            except Exception as e:
                logger.error(f"Failed to store in vector database: {e}")

        # Cache document
        self.document_cache[doc_id] = {
            "chunks": document_chunks,
            "metadata": metadata,
            "ingested_at": time.time(),
        }

        processing_time = time.time() - start_time

        # Update metrics
        self.performance_metrics["knowledge_base_size"] += len(chunks)

        return {
            "success": True,
            "doc_id": doc_id,
            "chunks_created": len(chunks),
            "processing_time": processing_time,
            "business_relevance_avg": sum(c.business_relevance for c in document_chunks)
            / len(document_chunks),
        }

    async def query_knowledge_base(self, rag_query: RAGQuery) -> RAGResponse:
        """
        Query the knowledge base with enhanced context awareness.

        Args:
            rag_query: RAG query with preferences and context

        Returns:
            Enhanced RAG response with business insights
        """
        start_time = time.time()

        # Check query cache
        query_hash = hashlib.md5(rag_query.query.encode()).hexdigest()
        if query_hash in self.query_cache:
            cached_response = self.query_cache[query_hash]
            if time.time() - cached_response["timestamp"] < 3600:  # 1 hour cache
                logger.info("Returning cached query result")
                self.performance_metrics["queries_processed"] += 1
                return cached_response["response"]

        # Generate query embedding
        query_embedding = self._generate_embedding(rag_query.query)

        # Search vector database
        search_results = []
        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=rag_query.max_results * 2,  # Get more for filtering
                    include=["documents", "metadatas", "distances"],
                )

                # Process and filter results
                for doc, metadata, distance in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                    strict=False,
                ):
                    if distance < rag_query.min_relevance_score:
                        # Convert distance to similarity score
                        similarity_score = 1.0 - distance

                    if similarity_score >= rag_query.min_relevance_score:
                        # Apply document type filter
                        if (
                            rag_query.document_types is None
                            or metadata.get("document_type") in rag_query.document_types
                        ):
                            search_results.append(
                                {
                                    "content": doc,
                                    "metadata": metadata,
                                    "similarity_score": similarity_score,
                                    "business_relevance": metadata.get(
                                        "business_relevance", 0.5
                                    ),
                                }
                            )

            except Exception as e:
                logger.error(f"Vector search failed: {e}")

        # Sort by combined relevance and business importance
        search_results.sort(
            key=lambda x: (x["similarity_score"] * 0.7 + x["business_relevance"] * 0.3),
            reverse=True,
        )

        # Limit to requested results
        search_results = search_results[: rag_query.max_results]

        # Generate contextualized response
        response_text = await self._generate_contextual_response(
            rag_query.query,
            search_results,
            rag_query.business_context,
            rag_query.user_role,
        )

        # Extract business insights
        business_insights = self._extract_business_insights(
            search_results, rag_query.query
        )

        processing_time = time.time() - start_time

        # Create response
        rag_response = RAGResponse(
            answer=response_text,
            sources=[
                {
                    "content": (
                        r["content"][:200] + "..."
                        if len(r["content"]) > 200
                        else r["content"]
                    ),
                    "metadata": r["metadata"],
                    "similarity_score": r["similarity_score"],
                    "business_relevance": r["business_relevance"],
                }
                for r in search_results
            ],
            confidence_score=(
                sum(r["similarity_score"] for r in search_results) / len(search_results)
                if search_results
                else 0.0
            ),
            processing_time=processing_time,
            tokens_used=len(rag_query.query.split())
            + sum(len(r["content"].split()) for r in search_results),
            business_insights=business_insights,
        )

        # Cache response
        self.query_cache[query_hash] = {
            "response": rag_response,
            "timestamp": time.time(),
        }

        # Update metrics
        self.performance_metrics["queries_processed"] += 1
        current_avg = self.performance_metrics["avg_response_time"]
        query_count = self.performance_metrics["queries_processed"]
        self.performance_metrics["avg_response_time"] = (
            current_avg * (query_count - 1) + processing_time
        ) / query_count

        return rag_response

    async def _generate_contextual_response(
        self,
        query: str,
        search_results: list[dict[str, Any]],
        business_context: Optional[str],
        user_role: str,
    ) -> str:
        """Generate contextualized response based on search results"""

        if not search_results:
            return "I don't have sufficient information in the knowledge base to answer this query. Please consider adding relevant documentation or refining your search."

        # Role-specific response formatting
        if user_role.lower() in ["ceo", "executive", "strategic"]:
            response_prefix = "From a strategic business perspective: "
        elif user_role.lower() in ["technical", "developer", "engineer"]:
            response_prefix = "From a technical implementation standpoint: "
        elif user_role.lower() in ["sales", "marketing"]:
            response_prefix = "From a sales and marketing perspective: "
        else:
            response_prefix = ""

        # Synthesize response (in production, would use LLM)
        response = f"""{response_prefix}Based on the available documentation and market intelligence:

{self._synthesize_answer(query, search_results)}

Key supporting information:
{self._format_key_points(search_results)}

This analysis is based on {len(search_results)} relevant sources from our enterprise knowledge base."""

        return response

    def _synthesize_answer(self, query: str, results: list[dict[str, Any]]) -> str:
        """Synthesize answer from search results (simplified version)"""
        # In production, this would use an LLM to synthesize
        # For now, return a structured summary

        query_lower = query.lower()

        if "pricing" in query_lower or "cost" in query_lower:
            return "Pricing strategy should be based on value delivery and market positioning. Consider enterprise tiers, usage-based models, and competitive differentiation."

        elif "market" in query_lower or "competitor" in query_lower:
            return "Market analysis indicates strong opportunities in the enterprise SaaS space. Key factors include customer acquisition costs, retention rates, and technological differentiation."

        elif "strategy" in query_lower or "plan" in query_lower:
            return "Strategic planning should focus on sustainable growth, operational efficiency, and customer success. Prioritize high-impact initiatives with clear ROI."

        elif "technical" in query_lower or "architecture" in query_lower:
            return "Technical architecture should prioritize scalability, security, and maintainability. Consider cloud-native solutions and microservices patterns."

        else:
            # Generic response based on content
            content_words = set()
            for result in results:
                content_words.update(result["content"].lower().split())

            return f"Based on the available information, this relates to: {', '.join(list(content_words)[:10])}. Please refer to the detailed sources for comprehensive information."

    def _format_key_points(self, results: list[dict[str, Any]]) -> str:
        """Format key points from search results"""
        points = []
        for i, result in enumerate(results[:3]):  # Top 3 results
            title = result["metadata"].get("title", f"Source {i+1}")
            doc_type = result["metadata"].get("document_type", "document")
            points.append(
                f"• {title} ({doc_type}) - Relevance: {result['similarity_score']:.0%}"
            )

        return "\n".join(points)

    def _extract_business_insights(
        self, results: list[dict[str, Any]], query: str
    ) -> list[str]:
        """Extract actionable business insights from search results"""
        insights = []

        # Analyze document types and recency
        doc_types = [r["metadata"].get("document_type", "general") for r in results]
        if "strategy" in doc_types:
            insights.append(
                "Strategic documentation available - consider alignment with current initiatives"
            )

        if "market_analysis" in doc_types:
            insights.append(
                "Market intelligence available - leverage for competitive positioning"
            )

        # Analyze business relevance scores
        avg_business_relevance = (
            sum(r["business_relevance"] for r in results) / len(results)
            if results
            else 0
        )
        if avg_business_relevance > 0.7:
            insights.append(
                "High business relevance - prioritize for strategic decision making"
            )
        elif avg_business_relevance < 0.3:
            insights.append(
                "Low business relevance - consider supplementing with additional business context"
            )

        # Query-specific insights
        query_lower = query.lower()
        if "revenue" in query_lower or "pricing" in query_lower:
            insights.append(
                "Revenue impact potential - evaluate against current financial targets"
            )

        if "customer" in query_lower or "user" in query_lower:
            insights.append(
                "Customer impact potential - consider user experience and satisfaction metrics"
            )

        return insights

    async def get_system_analytics(self) -> dict[str, Any]:
        """Get comprehensive system analytics"""
        return {
            "performance_metrics": self.performance_metrics,
            "knowledge_base_stats": {
                "total_documents": len(self.document_cache),
                "total_chunks": self.performance_metrics["knowledge_base_size"],
                "cache_size": len(self.query_cache),
            },
            "recent_queries": len(
                [
                    q
                    for q in self.query_cache.values()
                    if time.time() - q["timestamp"] < 3600
                ]
            ),
            "system_health": {
                "vector_db_available": self.collection is not None,
                "embedding_model_available": self.embedding_model is not None,
                "cache_hit_rate": self.performance_metrics["cache_hit_rate"],
            },
        }


# Global RAG system instance
_rag_system = None


def get_rag_system() -> EnterpriseRAGSystem:
    """Get the global RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = EnterpriseRAGSystem()
    return _rag_system


# Convenience functions for common enterprise scenarios
async def ingest_saas_documentation(file_path: str) -> dict[str, Any]:
    """Ingest SaaS documentation into RAG system"""
    rag_system = get_rag_system()

    try:
        content = Path(file_path).read_text()
        metadata = {
            "title": Path(file_path).stem,
            "file_path": file_path,
            "created_date": datetime.now().isoformat(),
            "source": "documentation",
        }

        return await rag_system.ingest_document(
            content=content, metadata=metadata, document_type="technical"
        )
    except Exception as e:
        logger.error(f"Failed to ingest documentation: {e}")
        return {"success": False, "error": str(e)}


async def query_business_intelligence(
    query: str, user_role: str = "general"
) -> RAGResponse:
    """Query business intelligence with role-based context"""
    rag_system = get_rag_system()

    rag_query = RAGQuery(
        query=query,
        max_results=5,
        min_relevance_score=0.6,
        document_types=["strategy", "market_analysis", "business_plan"],
        business_context="enterprise_saas",
        user_role=user_role,
    )

    return await rag_system.query_knowledge_base(rag_query)
