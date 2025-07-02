# AI-Powered Newsletter Insights Generator - Project Plan

## Overview
This document summarizes the evaluation and planning discussion for the AI-Powered Newsletter Insights Generator proposed by FissionLabs for MAX Smith KDP LLC.

## Project Summary
- **Product**: Automated weekly newsletter that aggregates Reddit insights using AI
- **Target**: 5,000 free trial users initially
- **Technology**: AWS serverless architecture with Claude AI via Bedrock
- **Timeline**: 125-day implementation (9 milestones)
- **Cost**: $0 development cost (provided free by FissionLabs)

## Key Features
1. **Reddit Data Ingestion**: Scheduled Lambda functions to collect posts from specified subreddits
2. **AI-Powered Insights**: Claude (or other LLMs via FloTorch) generates summaries and insights
3. **Vector Search**: OpenSearch for semantic similarity and RAG capabilities
4. **Email Delivery**: Weekly insights via Amazon SES with unsubscribe handling
5. **Subscription Management**: Stripe integration for 7-day trial to paid conversion

## Technical Architecture

### Core Components
- **Group 1 - Data Ingestion**: EventBridge → Lambda → S3 storage
- **Group 2 - ETL & Semantic**: Data normalization, Titan embeddings, OpenSearch indexing
- **Group 3 - GenAI Engine**: Top-K retrieval, Claude insights generation, DynamoDB storage
- **Group 4 - Subscription**: Landing page, Stripe checkout, webhook integration
- **Group 5 - Email Delivery**: SES delivery with bounce handling and DLQ
- **Group 6 - Monitoring**: CloudWatch, Secrets Manager, comprehensive logging

### Technology Stack
- **AWS Services**: Lambda, S3, EventBridge, Step Functions, Bedrock, OpenSearch, DynamoDB, SES, SNS, SQS, Secrets Manager, CloudWatch
- **Third Party**: Reddit API, Stripe API
- **LLM Gateway**: FloTorch (for experimentation)
- **IaC**: Terraform

## Success Metrics

| Metric | Target | Details |
|--------|--------|---------|
| Processing Latency | 5-7 seconds/post | Batch processing under 10 minutes for 5,000 posts |
| Claude API Success Rate | ≥98% | With retry logic and error handling |
| Weekly Email Volume | Up to 5,000 | Starting with SES sandbox limits |
| End-to-End Automation | Completed weekly flow | Reddit → Claude → SES |
| Email Delivery Rate | 95%+ | Including bounce handling |

## Implementation Timeline

| Milestone | Description | Duration (days) |
|-----------|-------------|-----------------|
| M1 | Reddit Lambda Setup | 5 |
| M2 | ETL Pipeline | 10 |
| M3 | Embedding & Indexing | 8 |
| M3.5 | LLM Experimentation with FloTorch | 8 |
| M4 | Insight Engine | 8 |
| M5 | Weekly Email Delivery | 6 |
| M6 | Stripe Trial & Plan Management | 5 |
| M7 | Landing Page (React) | 3 |
| M8 | Monitoring & Logging | 2 |
| M9 | Infrastructure as Code | 5 |

**Total Timeline**: ~60 working days (125 person-days with parallel work)

## Cost Structure

### Development Cost
- **FissionLabs Quote**: $39,199
- **Actual Cost to Client**: $0 (provided free as consulting showcase)

### Estimated Monthly Operating Costs
- **AWS Lambda**: $50-200
- **AWS Bedrock (Claude)**: $100-500
- **Amazon S3**: $5-10
- **Amazon DynamoDB**: $10-25
- **Amazon SES**: $5-50
- **Amazon OpenSearch**: $100-300
- **Other AWS Services**: $20-50
- **Stripe Fees**: 2.9% + $0.30 per transaction

**Total Monthly Estimate**: $300-1,200 (varies by usage)

### Cost Scaling Examples
- **Starting (100-500 users)**: ~$300-500/month
- **Growth (1,000-2,500 users)**: ~$600-800/month
- **Scale (5,000+ users)**: ~$1,000-1,200/month

### Important Cost Notes
1. **Costs scale with usage** - You only pay more as you get more customers
2. **Already profitable** - Current operation shows $9,000 revenue vs ~$2,770 total costs
3. **69% gross margin** - For every $100 in revenue, you keep $69 after costs
4. **Client only pays monthly operating costs** - Development provided free by FissionLabs

## Client Responsibilities
1. Provide AWS account with required permissions
2. Set up Stripe account and share credentials/webhooks
3. Verify domain and sender email ID in SES
4. Specify maximum five subreddit(s) for Reddit scraping
5. Provide GitHub repository for code maintenance
6. Authorize web domains and SSL certificates

## Risk Mitigation
- Reddit rate limiting included in PoC
- CloudWatch alerts for API quota monitoring
- SES bounce handling with DLQs
- Extensible schema for future data sources
- FloTorch integration for LLM flexibility

## Future Enhancements (Post-PoC)
- Human-in-the-loop review via admin UI
- A/B prompt testing
- User feedback loops
- Content moderation
- Multi-language support
- Personalization features
- Additional data sources beyond Reddit

## Decision Summary
The proposal demonstrates:
- Well-architected serverless foundation
- Clear phased rollout with lean PoC scope
- Strong AWS native service alignment
- Thoughtful error handling and observability
- Exceptional value with free development

**Recommendation**: Proceed with sign-off. The proposal is comprehensive, addresses all technical requirements, and provides clear success metrics with realistic timelines.

## Next Steps
1. Sign proposal and return to FissionLabs
2. Set up required AWS and Stripe accounts
3. Schedule kickoff meeting
4. Begin M1 implementation

---
*Document created: June 26, 2025*
*Based on FissionLabs Proposal Review*