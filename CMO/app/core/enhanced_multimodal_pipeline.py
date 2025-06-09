#!/usr/bin/env python3
"""
Enhanced Multi-Modal Pipeline for SaaS Market Intelligence
Integrates ColPali + Rally AI + Existing RAG for Enterprise-Grade Analysis
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import json

# Core system imports
from app.core.rag_engine import SaaSMarketIntelligenceRAG
from app.core.colpali_multimodal import SaaSMarketIntelligenceMultiModal, ColPaliMultiModalProcessor
from app.core.rally_ai_orchestrator import RallyAIOrchestrator, TaskPriority

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MultiModalAnalysisRequest:
    """Request for comprehensive multi-modal analysis"""
    query: str
    document_paths: List[Union[str, Path]] = None
    analysis_type: str = "comprehensive"  # comprehensive, competitive, technical, revenue
    priority: TaskPriority = TaskPriority.HIGH
    target_revenue_impact: float = 300.0
    include_visual_analysis: bool = True
    include_agent_coordination: bool = True


@dataclass
class EnhancedAnalysisResult:
    """Enhanced analysis result with multi-modal insights"""
    query: str
    text_analysis: Dict[str, Any]
    visual_analysis: Dict[str, Any] = None
    coordinated_insights: Dict[str, Any] = None
    confidence_score: float = 0.0
    revenue_impact: Dict[str, Any] = None
    recommendations: List[str] = None
    sources: List[str] = None


class EnhancedMultiModalPipeline:
    """
    Enterprise-grade multi-modal pipeline combining:
    - Existing LlamaIndex RAG (text-based intelligence)
    - ColPali multi-modal processing (visual document understanding)
    - Rally AI orchestration (agent coordination)
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        enable_colpali: bool = True,
        enable_rally_ai: bool = True
    ):
        """Initialize enhanced multi-modal pipeline"""
        
        # Core RAG engine
        self.rag_engine = SaaSMarketIntelligenceRAG(openai_api_key)
        
        # Multi-modal processing
        self.multimodal_engine = None
        if enable_colpali:
            try:
                self.multimodal_engine = SaaSMarketIntelligenceMultiModal(self.rag_engine)
                logger.info("✅ ColPali multi-modal engine initialized")
            except Exception as e:
                logger.warning(f"⚠️ ColPali initialization failed: {e}")
        
        # Rally AI orchestration
        self.rally_orchestrator = None
        if enable_rally_ai:
            self.rally_orchestrator = RallyAIOrchestrator(
                self.rag_engine,
                self.multimodal_engine
            )
            logger.info("✅ Rally AI orchestrator initialized")
        
        # Pipeline state
        self.pipeline_stats = {
            "total_analyses": 0,
            "multimodal_analyses": 0,
            "coordinated_analyses": 0,
            "average_confidence": 0.0,
            "total_revenue_impact": 0.0
        }
        
        logger.info("🚀 Enhanced Multi-Modal Pipeline initialized")
    
    async def initialize_system(self) -> None:
        """Initialize all system components"""
        
        logger.info("🔧 Initializing enhanced pipeline components...")
        
        # Initialize RAG knowledge base
        await self.rag_engine.initialize_knowledge_base()
        
        # Set up multi-modal integration
        if self.multimodal_engine:
            # Create multi-modal index in RAG system
            try:
                await self.multimodal_engine.integrate_with_existing_rag("multimodal_intelligence")
                logger.info("✅ Multi-modal integration complete")
            except Exception as e:
                logger.warning(f"⚠️ Multi-modal integration partial: {e}")
        
        logger.info("✅ Enhanced pipeline initialization complete")
    
    async def analyze_comprehensive(
        self,
        request: MultiModalAnalysisRequest
    ) -> EnhancedAnalysisResult:
        """
        Perform comprehensive analysis using all available capabilities
        
        Args:
            request: Analysis request with multi-modal requirements
            
        Returns:
            Enhanced analysis result with text, visual, and coordinated insights
        """
        
        logger.info(f"🎯 Starting comprehensive analysis: {request.query}")
        
        # Initialize result
        result = EnhancedAnalysisResult(
            query=request.query,
            text_analysis={},
            recommendations=[],
            sources=[]
        )
        
        # 1. Process visual documents if provided
        if request.document_paths and request.include_visual_analysis and self.multimodal_engine:
            result.visual_analysis = await self._process_visual_documents(
                request.document_paths
            )
            self.pipeline_stats["multimodal_analyses"] += 1
        
        # 2. Perform text-based RAG analysis
        result.text_analysis = await self._perform_text_analysis(request.query)
        
        # 3. Coordinate with Rally AI if enabled
        if request.include_agent_coordination and self.rally_orchestrator:
            result.coordinated_insights = await self._perform_coordinated_analysis(
                request
            )
            self.pipeline_stats["coordinated_analyses"] += 1
        
        # 4. Synthesize all insights
        result = await self._synthesize_multimodal_insights(result, request)
        
        # 5. Update pipeline statistics
        await self._update_pipeline_stats(result)
        
        logger.info(f"✅ Comprehensive analysis complete (confidence: {result.confidence_score:.2f})")
        return result
    
    async def _process_visual_documents(
        self,
        document_paths: List[Union[str, Path]]
    ) -> Dict[str, Any]:
        """Process visual documents with ColPali"""
        
        if not self.multimodal_engine:
            return {"status": "disabled", "documents": []}
        
        visual_insights = {
            "processed_documents": [],
            "extracted_insights": [],
            "layout_analysis": [],
            "confidence_scores": []
        }
        
        try:
            for doc_path in document_paths:
                path = Path(doc_path)
                if path.exists():
                    # Process with ColPali
                    documents = await self.multimodal_engine.process_saas_document(
                        path,
                        document_category="market_intelligence"
                    )
                    
                    for doc in documents:
                        visual_insights["processed_documents"].append({
                            "file_name": path.name,
                            "text_content": doc.text[:500] + "..." if len(doc.text) > 500 else doc.text,
                            "metadata": doc.metadata,
                            "confidence": doc.metadata.get("confidence_score", 0.5)
                        })
                        
                        # Extract key insights
                        if "visual_layout" in doc.metadata:
                            visual_insights["layout_analysis"].append({
                                "document": path.name,
                                "layout": doc.metadata["visual_layout"]
                            })
                        
                        visual_insights["confidence_scores"].append(
                            doc.metadata.get("confidence_score", 0.5)
                        )
                
            # Calculate overall visual confidence
            if visual_insights["confidence_scores"]:
                visual_insights["overall_confidence"] = sum(visual_insights["confidence_scores"]) / len(visual_insights["confidence_scores"])
            else:
                visual_insights["overall_confidence"] = 0.0
                
            logger.info(f"✅ Processed {len(visual_insights['processed_documents'])} visual documents")
            
        except Exception as e:
            logger.error(f"❌ Visual processing failed: {e}")
            visual_insights["error"] = str(e)
            visual_insights["overall_confidence"] = 0.0
        
        return visual_insights
    
    async def _perform_text_analysis(self, query: str) -> Dict[str, Any]:
        """Perform text-based analysis with existing RAG"""
        
        try:
            analysis = await self.rag_engine.analyze_market_opportunity(
                query,
                use_agent=True
            )
            
            return {
                "rag_response": analysis["response"],
                "confidence": analysis["confidence_score"],
                "sources": analysis["sources_used"],
                "recommendations": analysis["recommendations"],
                "opportunity_score": analysis["opportunity_score"]
            }
            
        except Exception as e:
            logger.error(f"❌ Text analysis failed: {e}")
            return {
                "error": str(e),
                "confidence": 0.0,
                "sources": [],
                "recommendations": ["Fix RAG engine integration"]
            }
    
    async def _perform_coordinated_analysis(
        self,
        request: MultiModalAnalysisRequest
    ) -> Dict[str, Any]:
        """Perform Rally AI coordinated analysis"""
        
        if not self.rally_orchestrator:
            return {"status": "disabled"}
        
        try:
            coordination_result = await self.rally_orchestrator.coordinate_market_analysis(
                request.query,
                target_revenue_impact=request.target_revenue_impact,
                urgency=request.priority
            )
            
            return {
                "status": "completed",
                "agent_results": coordination_result["agent_results"],
                "unified_recommendations": coordination_result["unified_recommendations"],
                "revenue_impact": coordination_result["revenue_impact_assessment"],
                "next_actions": coordination_result["next_actions"],
                "overall_confidence": coordination_result["overall_confidence"]
            }
            
        except Exception as e:
            logger.error(f"❌ Coordinated analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "overall_confidence": 0.0
            }
    
    async def _synthesize_multimodal_insights(
        self,
        result: EnhancedAnalysisResult,
        request: MultiModalAnalysisRequest
    ) -> EnhancedAnalysisResult:
        """Synthesize insights from all analysis modes"""
        
        # Collect confidence scores
        confidence_scores = []
        
        # Text analysis confidence
        if result.text_analysis.get("confidence"):
            confidence_scores.append(result.text_analysis["confidence"])
        
        # Visual analysis confidence
        if result.visual_analysis and result.visual_analysis.get("overall_confidence"):
            confidence_scores.append(result.visual_analysis["overall_confidence"])
        
        # Coordinated analysis confidence
        if result.coordinated_insights and result.coordinated_insights.get("overall_confidence"):
            confidence_scores.append(result.coordinated_insights["overall_confidence"])
        
        # Calculate weighted confidence
        result.confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Synthesize recommendations
        all_recommendations = []
        
        # From text analysis
        if result.text_analysis.get("recommendations"):
            all_recommendations.extend(result.text_analysis["recommendations"])
        
        # From coordinated analysis
        if result.coordinated_insights and result.coordinated_insights.get("unified_recommendations"):
            all_recommendations.extend(result.coordinated_insights["unified_recommendations"])
        
        # Remove duplicates and prioritize
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        result.recommendations = unique_recommendations[:5]  # Top 5
        
        # Synthesize sources
        all_sources = []
        
        if result.text_analysis.get("sources"):
            all_sources.extend(result.text_analysis["sources"])
        
        if result.visual_analysis and result.visual_analysis.get("processed_documents"):
            visual_sources = [doc["file_name"] for doc in result.visual_analysis["processed_documents"]]
            all_sources.extend(visual_sources)
        
        result.sources = list(set(all_sources))
        
        # Revenue impact synthesis
        if result.coordinated_insights and result.coordinated_insights.get("revenue_impact"):
            result.revenue_impact = result.coordinated_insights["revenue_impact"]
        else:
            # Estimate based on opportunity score
            opportunity_score = result.text_analysis.get("opportunity_score", 5.0)
            result.revenue_impact = {
                "daily_potential": f"${request.target_revenue_impact}",
                "confidence": result.confidence_score,
                "risk_level": "medium" if opportunity_score > 6.0 else "high"
            }
        
        return result
    
    async def _update_pipeline_stats(self, result: EnhancedAnalysisResult) -> None:
        """Update pipeline performance statistics"""
        
        self.pipeline_stats["total_analyses"] += 1
        
        # Update running average confidence
        total = self.pipeline_stats["total_analyses"]
        current_avg = self.pipeline_stats["average_confidence"]
        new_confidence = result.confidence_score
        
        self.pipeline_stats["average_confidence"] = (
            (current_avg * (total - 1) + new_confidence) / total
        )
        
        # Update revenue impact
        if result.revenue_impact and "daily_potential" in result.revenue_impact:
            try:
                daily_amount = float(result.revenue_impact["daily_potential"].replace("$", ""))
                self.pipeline_stats["total_revenue_impact"] += daily_amount
            except (ValueError, AttributeError):
                pass
        
        logger.info(f"📊 Pipeline stats updated: {self.pipeline_stats}")
    
    async def analyze_competitor_documents(
        self,
        competitor_docs: List[Union[str, Path]],
        analysis_focus: str = "pricing and features"
    ) -> EnhancedAnalysisResult:
        """Specialized analysis for competitor documents"""
        
        request = MultiModalAnalysisRequest(
            query=f"Analyze competitor {analysis_focus} for strategic positioning",
            document_paths=competitor_docs,
            analysis_type="competitive",
            priority=TaskPriority.HIGH,
            target_revenue_impact=500.0,  # Competitive intel is high-value
            include_visual_analysis=True,
            include_agent_coordination=True
        )
        
        return await self.analyze_comprehensive(request)
    
    async def analyze_market_reports(
        self,
        report_docs: List[Union[str, Path]],
        market_segment: str = "SaaS automation tools"
    ) -> EnhancedAnalysisResult:
        """Specialized analysis for market research reports"""
        
        request = MultiModalAnalysisRequest(
            query=f"Extract market opportunities in {market_segment} with revenue potential analysis",
            document_paths=report_docs,
            analysis_type="market_research",
            priority=TaskPriority.CRITICAL,
            target_revenue_impact=1000.0,  # Market research drives major decisions
            include_visual_analysis=True,
            include_agent_coordination=True
        )
        
        return await self.analyze_comprehensive(request)
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status"""
        
        status = {
            "pipeline_stats": self.pipeline_stats,
            "component_status": {
                "rag_engine": "operational" if self.rag_engine else "disabled",
                "multimodal_engine": "operational" if self.multimodal_engine else "disabled",
                "rally_orchestrator": "operational" if self.rally_orchestrator else "disabled"
            }
        }
        
        # Get RAG engine status if available
        if self.rag_engine:
            try:
                rag_status = await self.rag_engine.get_system_status()
                status["rag_engine_details"] = rag_status
            except Exception as e:
                status["rag_engine_details"] = {"error": str(e)}
        
        # Get Rally AI status if available
        if self.rally_orchestrator:
            try:
                rally_status = await self.rally_orchestrator.get_orchestration_status()
                status["rally_ai_details"] = rally_status
            except Exception as e:
                status["rally_ai_details"] = {"error": str(e)}
        
        return status


async def main():
    """Test enhanced multi-modal pipeline"""
    
    logger.info("🧪 Testing Enhanced Multi-Modal Pipeline")
    
    # Initialize pipeline
    pipeline = EnhancedMultiModalPipeline(
        enable_colpali=True,
        enable_rally_ai=True
    )
    
    try:
        # Initialize system
        await pipeline.initialize_system()
        
        # Test comprehensive analysis
        request = MultiModalAnalysisRequest(
            query="Find high-revenue SaaS opportunities in Python developer productivity tools",
            analysis_type="comprehensive",
            priority=TaskPriority.HIGH,
            target_revenue_impact=300.0
        )
        
        result = await pipeline.analyze_comprehensive(request)
        
        logger.info("✅ Enhanced pipeline test successful")
        logger.info(f"Confidence: {result.confidence_score:.2f}")
        logger.info(f"Revenue impact: {result.revenue_impact}")
        logger.info(f"Top recommendations: {result.recommendations[:3]}")
        
        # Get status
        status = await pipeline.get_pipeline_status()
        logger.info(f"Pipeline status: {status['component_status']}")
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())