"""API endpoints for SaaS Growth Dispatch."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.config.logging import get_logger
from app.core.rag_engine import SaaSMarketIntelligenceRAG
from app.web.api_auth import api_key_auth

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["api"])

# Initialize RAG engine
rag_engine = SaaSMarketIntelligenceRAG()


class MarketAnalysisRequest(BaseModel):
    """Request model for market analysis."""

    query: str
    sources: Optional[list[str]] = None
    max_results: int = 10


class MarketAnalysisResponse(BaseModel):
    """Response model for market analysis."""

    query: str
    analysis: str
    opportunity_score: float
    confidence_score: float
    sources_used: list[str]
    timestamp: datetime


class NicheOpportunityRequest(BaseModel):
    """Request model for niche opportunity discovery."""

    industry: Optional[str] = None
    technology: Optional[str] = None
    market_size: Optional[str] = None
    limit: int = 5


class NicheOpportunity(BaseModel):
    """Niche opportunity model."""

    title: str
    description: str
    opportunity_score: float
    market_size: str
    competition_level: str
    key_pain_points: list[str]
    recommended_features: list[str]


class UsageStatsResponse(BaseModel):
    """Usage statistics response."""

    period: str
    total_requests: int
    total_cost: float
    remaining_quota: int
    by_endpoint: dict[str, dict]
    by_day: dict[str, dict]


@router.post("/analyze", response_model=MarketAnalysisResponse)
async def analyze_market(
    request: MarketAnalysisRequest, api_key: str = Depends(api_key_auth)
):
    """Analyze market opportunities based on query."""
    try:
        # Perform analysis
        analysis = await rag_engine.analyze_market_opportunity(
            request.query, sources=request.sources
        )

        return MarketAnalysisResponse(
            query=request.query,
            analysis=analysis["analysis"],
            opportunity_score=analysis["opportunity_score"],
            confidence_score=analysis["confidence_score"],
            sources_used=analysis["sources_used"],
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error in market analysis: {e!s}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.get("/niches", response_model=list[NicheOpportunity])
async def discover_niches(
    request: NicheOpportunityRequest = Depends(), api_key: str = Depends(api_key_auth)
):
    """Discover underserved niche opportunities."""
    try:
        # Build query based on filters
        query_parts = []
        if request.industry:
            query_parts.append(f"industry:{request.industry}")
        if request.technology:
            query_parts.append(f"technology:{request.technology}")
        if request.market_size:
            query_parts.append(f"market_size:{request.market_size}")

        query = " ".join(query_parts) if query_parts else "underserved SaaS niches"

        # Get niche opportunities
        results = await rag_engine.discover_niches(query, limit=request.limit)

        # Format response
        opportunities = []
        for result in results:
            opportunities.append(
                NicheOpportunity(
                    title=result["title"],
                    description=result["description"],
                    opportunity_score=result["opportunity_score"],
                    market_size=result["market_size"],
                    competition_level=result["competition_level"],
                    key_pain_points=result["pain_points"],
                    recommended_features=result["features"],
                )
            )

        return opportunities

    except Exception as e:
        logger.error(f"Error discovering niches: {e!s}")
        raise HTTPException(status_code=500, detail="Niche discovery failed")


@router.get("/pain-points")
async def get_pain_points(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    source: Optional[str] = Query(
        None, description="Filter by source (reddit, github, etc)"
    ),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(10, description="Maximum results"),
    api_key: str = Depends(api_key_auth),
):
    """Get trending pain points from various sources."""
    try:
        # Build query
        query = f"pain points {industry or 'SaaS'} last {days} days"

        # Get pain points
        results = await rag_engine.get_pain_points(
            query=query, source=source, limit=limit
        )

        return {
            "pain_points": results,
            "period_days": days,
            "total_found": len(results),
            "filters": {"industry": industry, "source": source},
        }

    except Exception as e:
        logger.error(f"Error getting pain points: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pain points")


@router.get("/trends")
async def get_market_trends(
    category: Optional[str] = Query(None, description="Trend category"),
    timeframe: str = Query("30d", description="Timeframe (7d, 30d, 90d)"),
    api_key: str = Depends(api_key_auth),
):
    """Get current market trends and insights."""
    try:
        # Map timeframe to days
        timeframe_map = {"7d": 7, "30d": 30, "90d": 90}
        days = timeframe_map.get(timeframe, 30)

        # Get trends
        trends = await rag_engine.get_market_trends(category=category, days=days)

        return {
            "trends": trends,
            "timeframe": timeframe,
            "category": category,
            "generated_at": datetime.now(),
        }

    except Exception as e:
        logger.error(f"Error getting trends: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trends")


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(api_key: str = Depends(api_key_auth)):
    """Get API usage statistics for the current billing period."""
    try:
        # Get API key from request context
        from fastapi import Request

        request: Request = None  # This would be injected by FastAPI

        if hasattr(request.state, "api_key"):
            api_key_obj = request.state.api_key

            # Get usage stats
            from app.services.api_key_service import APIKeyService

            api_key_service = APIKeyService()

            stats = api_key_service.get_usage_stats(api_key_obj.customer_id)

            # Calculate remaining quota
            limits = api_key_obj.get_rate_limits()
            remaining = limits["max_queries_per_month"] - stats["total_requests"]

            return UsageStatsResponse(
                period=stats["period"],
                total_requests=stats["total_requests"],
                total_cost=stats["total_cost"],
                remaining_quota=max(0, remaining),
                by_endpoint=stats["by_endpoint"],
                by_day=stats["by_day"],
            )

        raise HTTPException(status_code=400, detail="Could not retrieve usage stats")

    except Exception as e:
        logger.error(f"Error getting usage stats: {e!s}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve usage statistics"
        )


@router.post("/validate-niche")
async def validate_niche_idea(
    niche: str,
    target_audience: Optional[str] = None,
    api_key: str = Depends(api_key_auth),
):
    """Validate a niche idea with market data."""
    try:
        # Build validation query
        query = f"validate SaaS niche: {niche}"
        if target_audience:
            query += f" for {target_audience}"

        # Perform validation
        validation = await rag_engine.validate_niche(query)

        return {
            "niche": niche,
            "validation": validation,
            "recommendations": validation.get("recommendations", []),
            "risks": validation.get("risks", []),
            "timestamp": datetime.now(),
        }

    except Exception as e:
        logger.error(f"Error validating niche: {e!s}")
        raise HTTPException(status_code=500, detail="Validation failed")
