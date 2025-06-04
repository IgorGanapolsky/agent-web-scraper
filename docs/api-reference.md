# 🔌 API Reference Guide

## Overview

The SaaS Market Intelligence Platform provides a comprehensive REST API for accessing agentic RAG capabilities. All endpoints return structured JSON responses with consistent error handling and authentication.

## Authentication

### API Key Authentication

```bash
# Include API key in headers
curl -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     https://api.saasgrowthdispatch.com/v1/analyze
```

### Environment Setup

```bash
export SAAS_INTEL_API_KEY="your_api_key_here"
export SAAS_INTEL_BASE_URL="https://api.saasgrowthdispatch.com/v1"
```

## Core Endpoints

### 1. Market Opportunity Analysis

**Endpoint**: `POST /v1/analyze/market-opportunity`

Analyze market opportunities using agentic RAG across multiple data sources.

#### Request

```json
{
  "query": "Find automation opportunities for Python developers",
  "sources": ["reddit", "github", "market_trends"],
  "use_agent": true,
  "context": {
    "industry": "SaaS",
    "company_stage": "startup",
    "budget_range": "0-50k"
  },
  "options": {
    "max_results": 10,
    "confidence_threshold": 0.7,
    "include_evidence": true
  }
}
```

#### Response

```json
{
  "status": "success",
  "analysis": {
    "opportunity_score": 8.7,
    "confidence_score": 0.92,
    "market_size_estimate": "$2.3M",
    "competition_level": "medium",
    "key_insights": [
      {
        "insight": "Python automation tools show 150% YoY growth in developer searches",
        "evidence_strength": 0.95,
        "source": "market_trends"
      },
      {
        "insight": "45% of SaaS founders report manual workflow pain points",
        "evidence_strength": 0.88,
        "source": "reddit"
      }
    ],
    "recommended_actions": [
      "Focus on SMB workflow automation",
      "Target Python developer communities",
      "Emphasize time-saving benefits"
    ],
    "sources_used": ["reddit", "github", "market_trends"],
    "query_time_ms": 1847
  },
  "metadata": {
    "timestamp": "2025-06-04T12:00:00Z",
    "model_version": "gpt-4-turbo-preview",
    "knowledge_base_version": "2025.06.04"
  }
}
```

### 2. Pain Point Discovery

**Endpoint**: `POST /v1/analyze/pain-points`

Discover and categorize pain points from community discussions.

#### Request

```json
{
  "query": "API integration challenges for SaaS platforms",
  "sources": ["reddit", "historical_reports"],
  "filters": {
    "date_range": "2025-01-01:2025-06-04",
    "subreddits": ["SaaS", "entrepreneur", "startups"],
    "min_engagement": 10
  },
  "categorization": true,
  "sentiment_analysis": true
}
```

#### Response

```json
{
  "status": "success",
  "pain_points": [
    {
      "pain_point": "Complex API authentication flows",
      "category": "integration",
      "severity": "high",
      "frequency": 47,
      "sentiment_score": -0.73,
      "examples": [
        {
          "source": "r/SaaS",
          "text": "OAuth flows are killing our conversion rates...",
          "engagement": 34,
          "date": "2025-05-15"
        }
      ],
      "business_impact": {
        "potential_revenue": "$50K-200K",
        "market_size": "25,000+ affected companies",
        "urgency": "high"
      }
    }
  ],
  "summary": {
    "total_pain_points": 23,
    "categories": {
      "integration": 8,
      "automation": 6,
      "analytics": 5,
      "pricing": 4
    },
    "top_category": "integration",
    "avg_severity": 7.2
  }
}
```

### 3. Competitive Intelligence

**Endpoint**: `POST /v1/analyze/competition`

Analyze competitive landscape and positioning opportunities.

#### Request

```json
{
  "query": "automation tools competitive analysis",
  "focus_areas": ["pricing", "features", "market_position"],
  "competitors": ["zapier", "microsoft_power_automate", "ifttt"],
  "include_gaps": true
}
```

#### Response

```json
{
  "status": "success",
  "competitive_analysis": {
    "market_overview": {
      "total_market_size": "$12.8B",
      "growth_rate": "23% YoY",
      "key_trends": ["AI integration", "no-code platforms", "enterprise adoption"]
    },
    "competitor_profiles": [
      {
        "name": "Zapier",
        "market_position": "leader",
        "pricing_tier": "premium",
        "strengths": ["integrations", "ease_of_use"],
        "weaknesses": ["pricing", "advanced_features"],
        "market_share": "35%"
      }
    ],
    "opportunity_gaps": [
      {
        "gap": "Developer-focused automation tools",
        "market_size": "$450M",
        "competition_level": "low",
        "difficulty": "medium",
        "time_to_market": "6-12 months"
      }
    ],
    "positioning_recommendations": [
      "Focus on technical users",
      "Emphasize customization capabilities",
      "Competitive pricing for SMBs"
    ]
  }
}
```

### 4. Trend Analysis

**Endpoint**: `POST /v1/analyze/trends`

Analyze market trends and future opportunities.

#### Request

```json
{
  "query": "SaaS automation trends 2025",
  "time_horizon": "12_months",
  "trend_types": ["technology", "market", "customer_behavior"],
  "confidence_level": "high"
}
```

#### Response

```json
{
  "status": "success",
  "trend_analysis": {
    "emerging_trends": [
      {
        "trend": "AI-powered workflow automation",
        "growth_trajectory": "exponential",
        "confidence": 0.94,
        "market_impact": "high",
        "timeline": "6-18 months",
        "key_drivers": ["GPT adoption", "cost reduction", "productivity gains"]
      }
    ],
    "declining_trends": [
      {
        "trend": "Manual data entry solutions",
        "decline_rate": "-15% YoY",
        "replacement_by": "AI automation tools"
      }
    ],
    "market_forecasts": {
      "automation_market_2026": "$18.4B",
      "ai_integration_adoption": "73%",
      "smb_automation_growth": "45% YoY"
    }
  }
}
```

## Knowledge Management Endpoints

### 5. Knowledge Base Status

**Endpoint**: `GET /v1/knowledge/status`

Get current status of all knowledge bases.

#### Response

```json
{
  "status": "operational",
  "knowledge_bases": {
    "reddit": {
      "status": "healthy",
      "document_count": 15647,
      "last_updated": "2025-06-04T06:00:00Z",
      "coverage": "complete"
    },
    "github": {
      "status": "healthy",
      "document_count": 8234,
      "last_updated": "2025-06-04T04:00:00Z",
      "coverage": "complete"
    },
    "market_trends": {
      "status": "updating",
      "document_count": 3421,
      "last_updated": "2025-06-04T08:00:00Z",
      "coverage": "partial"
    }
  },
  "system_metrics": {
    "total_documents": 27302,
    "avg_query_time": "1.8s",
    "uptime": "99.7%",
    "cache_hit_rate": "89%"
  }
}
```

### 6. Custom Knowledge Upload

**Endpoint**: `POST /v1/knowledge/upload`

Upload custom data to enhance knowledge base.

#### Request

```json
{
  "source_name": "custom_research",
  "documents": [
    {
      "text": "Your custom market research content...",
      "metadata": {
        "source": "internal_research",
        "date": "2025-06-04",
        "category": "market_analysis",
        "confidence": 0.9
      }
    }
  ],
  "overwrite": false
}
```

#### Response

```json
{
  "status": "success",
  "upload_summary": {
    "documents_processed": 15,
    "documents_indexed": 15,
    "processing_time_ms": 2341,
    "index_name": "custom_research",
    "available_for_queries": true
  }
}
```

## Utility Endpoints

### 7. Health Check

**Endpoint**: `GET /v1/health`

System health and performance metrics.

#### Response

```json
{
  "status": "healthy",
  "services": {
    "rag_engine": "operational",
    "vector_store": "operational",
    "knowledge_builder": "operational",
    "api_gateway": "operational"
  },
  "performance": {
    "avg_response_time": "1.8s",
    "requests_per_minute": 847,
    "error_rate": "0.2%",
    "uptime": "99.9%"
  },
  "timestamp": "2025-06-04T12:00:00Z"
}
```

### 8. Usage Analytics

**Endpoint**: `GET /v1/analytics/usage`

Query usage analytics and billing information.

#### Request Parameters

```
?start_date=2025-06-01&end_date=2025-06-04&granularity=daily
```

#### Response

```json
{
  "status": "success",
  "usage_analytics": {
    "period": "2025-06-01 to 2025-06-04",
    "total_queries": 1247,
    "successful_queries": 1221,
    "error_rate": "2.1%",
    "daily_breakdown": [
      {
        "date": "2025-06-01",
        "queries": 312,
        "avg_response_time": "1.9s",
        "top_query_types": ["market_opportunity", "pain_points"]
      }
    ],
    "most_used_sources": ["reddit", "market_trends", "github"],
    "billing": {
      "current_tier": "pro",
      "queries_included": 10000,
      "queries_used": 1247,
      "overage_charges": "$0.00"
    }
  }
}
```

## Error Handling

### Standard Error Response

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_QUERY",
    "message": "Query must be between 10 and 500 characters",
    "details": {
      "query_length": 8,
      "min_length": 10,
      "max_length": 500
    }
  },
  "timestamp": "2025-06-04T12:00:00Z",
  "request_id": "req_12345"
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_API_KEY` | API key missing or invalid | 401 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INVALID_QUERY` | Query format or content invalid | 400 |
| `KNOWLEDGE_BASE_UNAVAILABLE` | Knowledge base temporarily unavailable | 503 |
| `INSUFFICIENT_CONFIDENCE` | Results below confidence threshold | 200 |
| `PROCESSING_TIMEOUT` | Query processing timeout | 504 |

## Rate Limits

### Limits by Plan

| Plan | Queries/Hour | Queries/Day | Burst Limit |
|------|--------------|-------------|-------------|
| **Basic** | 100 | 1,000 | 10/minute |
| **Pro** | 1,000 | 10,000 | 50/minute |
| **Enterprise** | 10,000 | 100,000 | 200/minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1622548800
X-RateLimit-Retry-After: 3600
```

## SDK Examples

### Python SDK

```python
import saas_intel

# Initialize client
client = saas_intel.Client(api_key="your_api_key")

# Market opportunity analysis
result = await client.analyze_market_opportunity(
    query="Python automation opportunities",
    sources=["reddit", "github"],
    use_agent=True
)

print(f"Opportunity Score: {result.opportunity_score}")
print(f"Key Insights: {result.key_insights}")
```

### JavaScript SDK

```javascript
import SaaSIntel from '@saas-intel/sdk';

const client = new SaaSIntel({ apiKey: 'your_api_key' });

// Pain point discovery
const painPoints = await client.analyzePainPoints({
  query: 'API integration challenges',
  sources: ['reddit'],
  categorization: true
});

console.log('Pain Points:', painPoints.pain_points);
```

### cURL Examples

```bash
# Market opportunity analysis
curl -X POST "https://api.saasgrowthdispatch.com/v1/analyze/market-opportunity" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "automation opportunities for developers",
    "sources": ["reddit", "github"],
    "use_agent": true
  }'

# Health check
curl -X GET "https://api.saasgrowthdispatch.com/v1/health" \
  -H "Authorization: Bearer your_api_key"
```

## Webhooks

### Webhook Configuration

```json
{
  "webhook_url": "https://your-app.com/webhooks/market-intel",
  "events": ["analysis_complete", "knowledge_updated"],
  "secret": "your_webhook_secret"
}
```

### Webhook Payload

```json
{
  "event": "analysis_complete",
  "data": {
    "query_id": "q_12345",
    "analysis": { /* full analysis result */ },
    "status": "completed"
  },
  "timestamp": "2025-06-04T12:00:00Z",
  "signature": "sha256=..."
}
```

---

## Support

- **API Status**: [status.saasgrowthdispatch.com](https://status.saasgrowthdispatch.com)
- **Documentation**: [docs.saasgrowthdispatch.com](https://docs.saasgrowthdispatch.com)
- **Support Email**: [api-support@saasgrowthdispatch.com](mailto:api-support@saasgrowthdispatch.com)
- **Developer Discord**: [discord.gg/saas-intel](https://discord.gg/saas-intel)
