# ⚡ Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will get you up and running with the SaaS Market Intelligence Platform's agentic RAG system in just a few minutes.

## Prerequisites

- **Python 3.10+** (3.12 recommended)
- **8GB+ RAM** (for local vector operations)
- **OpenAI API key** (required for agentic intelligence)
- **50GB+ storage** (for knowledge bases and vector stores)

## Installation

### Option 1: Quick Install (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/IgorGanapolsky/agent-web-scraper.git
cd agent-web-scraper

# 2. Run the automated setup
python setup_dev.py

# 3. Set your OpenAI API key
export OPENAI_API_KEY="sk-your-openai-key-here"

# 4. Test the system
python scripts/test_agentic_rag.py
```

### Option 2: Manual Install

```bash
# 1. Clone repository
git clone https://github.com/IgorGanapolsky/agent-web-scraper.git
cd agent-web-scraper

# 2. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e .

# 4. Set environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize knowledge bases
python -c "
from app.core.rag_engine import SaaSMarketIntelligenceRAG
import asyncio
rag = SaaSMarketIntelligenceRAG()
asyncio.run(rag.initialize_knowledge_base())
"
```

### Option 3: Docker Install

```bash
# 1. Clone repository
git clone https://github.com/IgorGanapolsky/agent-web-scraper.git
cd agent-web-scraper

# 2. Set environment variables
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 3. Start with Docker Compose
docker-compose up -d

# 4. Test the system
docker-compose exec app python scripts/test_agentic_rag.py
```

## First Query

Once installed, try your first agentic intelligence query:

```python
from app.core.rag_engine import SaaSMarketIntelligenceRAG
import asyncio

async def first_query():
    # Initialize the agentic RAG system
    rag = SaaSMarketIntelligenceRAG()

    # Build knowledge base (one-time setup)
    await rag.initialize_knowledge_base()

    # Ask an intelligent question
    result = await rag.analyze_market_opportunity(
        "Find automation opportunities for Python developers in 2025"
    )

    # Display results
    print(f"🎯 Opportunity Score: {result['opportunity_score']}/10")
    print(f"🔍 Confidence: {result['confidence_score']:.0%}")
    print(f"📊 Sources Used: {', '.join(result['sources_used'])}")
    print(f"\n💡 Key Insights:")
    for insight in result['insights'][:3]:
        print(f"   • {insight}")

# Run the query
asyncio.run(first_query())
```

### Expected Output

```
🧠 SaaS Market Intelligence RAG initialized
📚 Building knowledge bases...
✅ Reddit knowledge base: 1,247 documents
✅ Market trends knowledge base: 834 documents
✅ GitHub knowledge base: 567 documents
✅ Historical reports knowledge base: 423 documents

🔍 Analyzing: "Find automation opportunities for Python developers in 2025"

🎯 Opportunity Score: 8.7/10
🔍 Confidence: 92%
📊 Sources Used: reddit, github, market_trends

💡 Key Insights:
   • Python automation tools show 150% YoY growth in developer searches
   • 73% of SaaS founders report manual workflow bottlenecks
   • GitHub shows 2,500+ new automation repositories in 2024
```

## Common Use Cases

### 1. Pain Point Discovery

```python
# Find specific pain points in your market
result = await rag.analyze_market_opportunity(
    "What are the biggest API integration challenges for SaaS platforms?"
)

print("🔥 Top Pain Points:")
for pain_point in result['pain_points']:
    print(f"   • {pain_point['description']}")
    print(f"     Severity: {pain_point['severity']}/10")
    print(f"     Market Size: {pain_point['market_size']}")
```

### 2. Competitive Analysis

```python
# Analyze competitive landscape
result = await rag.analyze_market_opportunity(
    "How does Zapier compare to other automation tools? What gaps exist?"
)

print("🏆 Competitive Intelligence:")
print(f"Market Position: {result['competitive_analysis']['position']}")
print(f"Key Gaps: {result['competitive_analysis']['opportunities']}")
```

### 3. Trend Analysis

```python
# Discover emerging trends
result = await rag.analyze_market_opportunity(
    "What are the emerging trends in SaaS automation for 2025?"
)

print("📈 Emerging Trends:")
for trend in result['trends']:
    print(f"   • {trend['name']}: {trend['growth_rate']}% growth")
```

## Configuration Options

### Environment Variables

Create a `.env` file with your configuration:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional - Model Configuration
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-large

# Optional - Performance Tuning
CHROMA_PERSIST_DIR=data/vector_stores
MAX_CONCURRENT_QUERIES=10
CONTEXT_WINDOW_SIZE=5

# Optional - External APIs
# SERPAPI_KEY removed during legacy cleanup
REDDIT_CLIENT_ID=your-reddit-id
REDDIT_CLIENT_SECRET=your-reddit-secret
```

### Custom Data Sources

Add your own data to enhance intelligence:

```python
from app.core.knowledge_base import KnowledgeBaseBuilder
from llama_index.core import Document

# Create custom documents
custom_docs = [
    Document(
        text="Your market research content...",
        metadata={
            "source": "internal_research",
            "category": "customer_feedback",
            "date": "2025-06-04"
        }
    )
]

# Add to knowledge base
builder = KnowledgeBaseBuilder()
await builder.add_custom_documents("internal_research", custom_docs)
```

## API Usage

### REST API (Coming Soon)

```bash
# Market opportunity analysis
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "query": "Find automation opportunities for developers",
    "sources": ["reddit", "github"],
    "use_agent": true
  }'
```

### Python SDK (Coming Soon)

```python
import saas_intel

# Initialize client
client = saas_intel.Client(api_key="your-api-key")

# Query the platform
result = await client.analyze_opportunity(
    "Python automation market opportunities"
)
```

## Performance Optimization

### Speed Up Queries

```python
# Use specific sources for faster queries
result = await rag.analyze_market_opportunity(
    "API integration pain points",
    sources=["reddit"],  # Only search Reddit
    use_agent=False      # Skip multi-step reasoning
)

# Cache frequently used queries
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_query(query_text):
    return asyncio.run(rag.analyze_market_opportunity(query_text))
```

### Optimize Memory Usage

```python
# For large datasets, use batch processing
from app.core.vector_store import VectorStoreManager

manager = VectorStoreManager()

# Process documents in batches
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    await manager.add_documents("knowledge_base", batch)
```

## Troubleshooting

### Common Issues

#### 1. Memory Errors

```bash
# Increase system memory or reduce batch size
export PYTHONMAXMEMORY=8G

# Or process smaller batches
python -c "
from app.core.knowledge_base import KnowledgeBaseBuilder
builder = KnowledgeBaseBuilder()
builder.batch_size = 50  # Reduce from default 100
"
```

#### 2. Slow Queries

```bash
# Check vector store performance
python -c "
from app.core.vector_store import VectorStoreManager
import time
manager = VectorStoreManager()
start = time.time()
results = await manager.search_documents('reddit', 'test query', top_k=5)
print(f'Search took {time.time() - start:.2f}s')
"
```

#### 3. API Errors

```bash
# Test OpenAI API connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# Check API key format
echo $OPENAI_API_KEY | grep -E "^sk-[a-zA-Z0-9]{48}$"
```

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
from app.core.rag_engine import SaaSMarketIntelligenceRAG

rag = SaaSMarketIntelligenceRAG(debug=True)
status = await rag.get_system_status()
print(f"System Status: {status}")
```

## Next Steps

### 1. Explore Advanced Features

```python
# Use conversation context
context = {
    "industry": "SaaS",
    "company_size": "startup",
    "budget": "50k"
}

result = await rag.analyze_market_opportunity(
    "Best automation tools for our budget",
    context=context
)
```

### 2. Build Custom Applications

```python
# Create a custom analysis pipeline
class CustomAnalyzer:
    def __init__(self):
        self.rag = SaaSMarketIntelligenceRAG()

    async def analyze_competitor(self, competitor_name):
        # Multi-query analysis
        queries = [
            f"What are {competitor_name}'s strengths and weaknesses?",
            f"What features does {competitor_name} lack?",
            f"How do users feel about {competitor_name}?"
        ]

        results = []
        for query in queries:
            result = await self.rag.analyze_market_opportunity(query)
            results.append(result)

        return self.synthesize_competitor_analysis(results)
```

### 3. Deploy to Production

See our [Deployment Guide](deployment-guide.md) for:
- Docker containerization
- Cloud deployment (AWS, GCP, Azure)
- Scaling and load balancing
- Monitoring and logging

### 4. Integrate with Your Tools

```python
# Slack integration
import slack_sdk

async def send_daily_insights():
    result = await rag.analyze_market_opportunity(
        "What are today's trending SaaS pain points?"
    )

    slack_client.chat_postMessage(
        channel="#market-intelligence",
        text=f"🎯 Daily Market Insights:\n{result['summary']}"
    )

# Schedule daily insights
import schedule
schedule.every().day.at("09:00").do(send_daily_insights)
```

## Support

- **Documentation**: [Full docs](agentic-rag-architecture.md)
- **API Reference**: [API docs](api-reference.md)
- **GitHub Issues**: [Report issues](https://github.com/IgorGanapolsky/agent-web-scraper/issues)
- **Email**: [support@saasgrowthdispatch.com](mailto:support@saasgrowthdispatch.com)

---

**🎉 You're ready to discover market opportunities with AI-powered intelligence!**

Start with the examples above, then explore the full documentation for advanced features and deployment options.
